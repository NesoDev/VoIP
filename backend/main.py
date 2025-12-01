from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import asyncio
import uvicorn
from datetime import datetime

from user_manager import user_manager, voip_logger, User
from sip_server import SIPServer

app = FastAPI(title="VoIP Demo API")

# CORS para permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections para logs en tiempo real
active_websockets: List[WebSocket] = []

class RegisterRequest(BaseModel):
    username: str

class HeartbeatRequest(BaseModel):
    username: str

class CallRequest(BaseModel):
    caller: str
    callee: str

@app.on_event("startup")
async def startup_event():
    """Inicia el servidor SIP al arrancar la API"""
    voip_logger.log_step(
        "INICIALIZACIÓN DEL SISTEMA",
        {
            'componente': 'FastAPI + SIP Server',
            'version': '1.0.0',
            'puerto_api': '8000',
            'puerto_sip': '5060',
            'estado': 'Iniciando servicios'
        }
    )
    
    # Iniciar servidor SIP en background
    sip_server = SIPServer(host='0.0.0.0', port=5060)
    asyncio.create_task(sip_server.start())
    app.state.sip_server = sip_server

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "VoIP Demo Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "register": "/register",
            "heartbeat": "/heartbeat",
            "users": "/users",
            "logs": "/logs",
            "ws_logs": "/ws/logs"
        }
    }

@app.post("/register")
async def register_user(request: RegisterRequest):
    """Registra un nuevo usuario"""
    voip_logger.log_step(
        "SOLICITUD DE REGISTRO DE USUARIO",
        {
            'endpoint': '/register',
            'username': request.username,
            'metodo': 'POST',
            'timestamp': datetime.now().isoformat()
        }
    )
    
    user = user_manager.register_user(request.username)
    
    # Broadcast a WebSockets
    await broadcast_log({
        'type': 'user_registered',
        'user': user.to_dict(),
        'timestamp': datetime.now().isoformat()
    })
    
    return {
        "success": True,
        "user": user.to_dict(),
        "message": f"Usuario {request.username} registrado con IP {user.internal_ip}"
    }

@app.post("/heartbeat")
async def heartbeat(request: HeartbeatRequest):
    """Actualiza el heartbeat de un usuario"""
    success = user_manager.update_heartbeat(request.username)
    
    if not success:
        voip_logger.log_step(
            "ERROR: HEARTBEAT RECHAZADO",
            {
                'username': request.username,
                'razon': 'Usuario no registrado',
                'accion': 'Debe registrarse primero'
            }
        )
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "success": True,
        "message": "Heartbeat actualizado"
    }

@app.get("/users")
async def get_users():
    """Obtiene lista de usuarios activos"""
    active_users = user_manager.get_active_users(timeout=30)
    
    voip_logger.log_step(
        "CONSULTA DE USUARIOS ACTIVOS",
        {
            'endpoint': '/users',
            'total_activos': len(active_users),
            'timestamp': datetime.now().isoformat()
        }
    )
    
    return {
        "success": True,
        "users": [user.to_dict() for user in active_users],
        "total": len(active_users)
    }

@app.get("/users/all")
async def get_all_users():
    """Obtiene todos los usuarios (activos e inactivos)"""
    all_users = user_manager.get_all_users()
    
    return {
        "success": True,
        "users": [user.to_dict() for user in all_users],
        "total": len(all_users)
    }

@app.get("/logs")
async def get_logs():
    """Obtiene todos los logs del sistema"""
    logs = voip_logger.get_logs()
    
    return {
        "success": True,
        "logs": logs,
        "total": len(logs)
    }

@app.delete("/logs")
async def clear_logs():
    """Limpia todos los logs"""
    voip_logger.clear_logs()
    
    return {
        "success": True,
        "message": "Logs limpiados"
    }

@app.post("/call/initiate")
async def initiate_call(request: CallRequest):
    """Inicia una llamada entre dos usuarios"""
    caller = user_manager.get_user(request.caller)
    callee = user_manager.get_user(request.callee)
    
    if not caller:
        raise HTTPException(status_code=404, detail=f"Usuario {request.caller} no encontrado")
    if not callee:
        raise HTTPException(status_code=404, detail=f"Usuario {request.callee} no encontrado")
    
    voip_logger.log_step(
        "INICIANDO PROCESO DE LLAMADA",
        {
            'llamante': request.caller,
            'llamante_ip': caller.internal_ip,
            'llamado': request.callee,
            'llamado_ip': callee.internal_ip,
            'protocolo': 'SIP',
            'estado': 'Preparando INVITE'
        }
    )
    
    await broadcast_log({
        'type': 'call_initiated',
        'caller': caller.to_dict(),
        'callee': callee.to_dict(),
        'timestamp': datetime.now().isoformat()
    })
    
    return {
        "success": True,
        "message": f"Llamada iniciada de {request.caller} a {request.callee}",
        "caller": caller.to_dict(),
        "callee": callee.to_dict()
    }

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket para logs en tiempo real"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    voip_logger.log_step(
        "WEBSOCKET CONECTADO",
        {
            'tipo': 'Logs en tiempo real',
            'total_conexiones': len(active_websockets)
        }
    )
    
    try:
        while True:
            # Mantener conexión viva
            data = await websocket.receive_text()
            
            # Si el cliente envía "get_logs", enviar todos los logs
            if data == "get_logs":
                logs = voip_logger.get_logs()
                await websocket.send_json({
                    'type': 'all_logs',
                    'logs': logs
                })
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        voip_logger.log_step(
            "WEBSOCKET DESCONECTADO",
            {
                'tipo': 'Logs en tiempo real',
                'total_conexiones': len(active_websockets)
            }
        )

async def broadcast_log(log_data: dict):
    """Envía un log a todos los WebSockets conectados"""
    for websocket in active_websockets:
        try:
            await websocket.send_json(log_data)
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
