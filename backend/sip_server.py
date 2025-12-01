import asyncio
import socket
from datetime import datetime
from typing import Optional, Dict
import re
from user_manager import voip_logger

class SIPMessage:
    """Representa un mensaje SIP"""
    def __init__(self, raw_message: str):
        self.raw = raw_message
        self.parse()
    
    def parse(self):
        """Parsea el mensaje SIP"""
        lines = self.raw.split('\r\n')
        self.start_line = lines[0] if lines else ""
        self.headers = {}
        self.body = ""
        
        body_start = False
        for line in lines[1:]:
            if not line.strip():
                body_start = True
                continue
            if body_start:
                self.body += line + '\r\n'
            else:
                if ':' in line:
                    key, value = line.split(':', 1)
                    self.headers[key.strip()] = value.strip()

class SIPServer:
    """Servidor SIP simplificado con logging detallado"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5060):
        self.host = host
        self.port = port
        self.registered_users: Dict[str, dict] = {}
        self.active_calls: Dict[str, dict] = {}
        
    async def start(self):
        """Inicia el servidor SIP"""
        voip_logger.log_step(
            "INICIO DE SERVIDOR SIP",
            {
                'protocolo': 'SIP/2.0 (Session Initiation Protocol)',
                'host': self.host,
                'puerto': self.port,
                'estado': 'INICIANDO',
                'codec_soporte': 'G.711 (PCMU/PCMA), G.729',
                'transporte': 'UDP'
            }
        )
        
        # Crear socket UDP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.setblocking(False)
        
        voip_logger.log_step(
            "SERVIDOR SIP ACTIVO",
            {
                'estado': 'ESCUCHANDO',
                'direccion': f"{self.host}:{self.port}",
                'tipo_socket': 'UDP',
                'buffer_size': '2048 bytes'
            }
        )
        
        # Loop de recepción
        while True:
            try:
                await asyncio.sleep(0.1)
                try:
                    data, addr = self.socket.recvfrom(2048)
                    message = data.decode('utf-8')
                    await self.handle_message(message, addr)
                except BlockingIOError:
                    continue
            except Exception as e:
                voip_logger.log_step(
                    "ERROR EN SERVIDOR SIP",
                    {
                        'error': str(e),
                        'tipo': type(e).__name__
                    }
                )
    
    async def handle_message(self, message: str, addr: tuple):
        """Maneja mensajes SIP entrantes"""
        sip_msg = SIPMessage(message)
        
        voip_logger.log_step(
            "MENSAJE SIP RECIBIDO",
            {
                'desde': f"{addr[0]}:{addr[1]}",
                'tamaño': f"{len(message)} bytes",
                'primera_linea': sip_msg.start_line,
                'metodo': self.get_method(sip_msg.start_line)
            }
        )
        
        # Determinar tipo de mensaje
        if sip_msg.start_line.startswith('REGISTER'):
            await self.handle_register(sip_msg, addr)
        elif sip_msg.start_line.startswith('INVITE'):
            await self.handle_invite(sip_msg, addr)
        elif sip_msg.start_line.startswith('ACK'):
            await self.handle_ack(sip_msg, addr)
        elif sip_msg.start_line.startswith('BYE'):
            await self.handle_bye(sip_msg, addr)
        elif sip_msg.start_line.startswith('OPTIONS'):
            await self.handle_options(sip_msg, addr)
    
    def get_method(self, start_line: str) -> str:
        """Extrae el método del mensaje SIP"""
        parts = start_line.split()
        return parts[0] if parts else "UNKNOWN"
    
    async def handle_register(self, msg: SIPMessage, addr: tuple):
        """Maneja solicitud REGISTER"""
        from_header = msg.headers.get('From', '')
        contact = msg.headers.get('Contact', '')
        call_id = msg.headers.get('Call-ID', 'unknown')
        
        # Extraer username
        username_match = re.search(r'sip:([^@]+)@', from_header)
        username = username_match.group(1) if username_match else 'unknown'
        
        voip_logger.log_step(
            "PASO 1: SOLICITUD DE REGISTRO (REGISTER)",
            {
                'metodo': 'REGISTER',
                'usuario': username,
                'desde_ip': f"{addr[0]}:{addr[1]}",
                'call_id': call_id,
                'contact': contact,
                'estado': 'Procesando registro de usuario en servidor SIP'
            }
        )
        
        # Registrar usuario
        self.registered_users[username] = {
            'addr': addr,
            'contact': contact,
            'registered_at': datetime.now().isoformat()
        }
        
        # Enviar 200 OK
        response = self.create_register_response(msg, username)
        self.socket.sendto(response.encode('utf-8'), addr)
        
        voip_logger.log_step(
            "PASO 2: RESPUESTA DE REGISTRO (200 OK)",
            {
                'codigo': '200 OK',
                'usuario': username,
                'hacia_ip': f"{addr[0]}:{addr[1]}",
                'estado': 'Usuario registrado exitosamente',
                'expiracion': '3600 segundos',
                'usuarios_registrados': len(self.registered_users)
            }
        )
    
    async def handle_invite(self, msg: SIPMessage, addr: tuple):
        """Maneja solicitud INVITE (inicio de llamada)"""
        from_header = msg.headers.get('From', '')
        to_header = msg.headers.get('To', '')
        call_id = msg.headers.get('Call-ID', 'unknown')
        
        caller = self.extract_username(from_header)
        callee = self.extract_username(to_header)
        
        voip_logger.log_step(
            "PASO 3: INICIO DE LLAMADA (INVITE)",
            {
                'metodo': 'INVITE',
                'llamante': caller,
                'llamado': callee,
                'call_id': call_id,
                'desde_ip': f"{addr[0]}:{addr[1]}",
                'sdp': 'Session Description Protocol incluido',
                'codecs_ofrecidos': 'PCMU (G.711 µ-law), PCMA (G.711 A-law)',
                'estado': 'Solicitando establecimiento de sesión'
            }
        )
        
        # Analizar SDP del cuerpo
        if msg.body:
            self.parse_sdp(msg.body, caller)
        
        # Enviar 100 Trying
        trying_response = self.create_trying_response(msg)
        self.socket.sendto(trying_response.encode('utf-8'), addr)
        
        voip_logger.log_step(
            "PASO 4: PROCESANDO LLAMADA (100 TRYING)",
            {
                'codigo': '100 Trying',
                'estado': 'Servidor procesando la solicitud INVITE',
                'accion': 'Buscando al usuario destino'
            }
        )
        
        # Enviar 180 Ringing
        ringing_response = self.create_ringing_response(msg)
        self.socket.sendto(ringing_response.encode('utf-8'), addr)
        
        voip_logger.log_step(
            "PASO 5: ALERTANDO AL DESTINO (180 RINGING)",
            {
                'codigo': '180 Ringing',
                'llamado': callee,
                'estado': 'Teléfono del destino está sonando',
                'accion': 'Esperando respuesta del usuario llamado'
            }
        )
        
        # Simular aceptación después de un delay (en producción, esperaría respuesta real)
        await asyncio.sleep(2)
        
        # Enviar 200 OK
        ok_response = self.create_invite_ok_response(msg)
        self.socket.sendto(ok_response.encode('utf-8'), addr)
        
        # Guardar llamada activa
        self.active_calls[call_id] = {
            'caller': caller,
            'callee': callee,
            'started_at': datetime.now().isoformat()
        }
        
        voip_logger.log_step(
            "PASO 6: LLAMADA ACEPTADA (200 OK)",
            {
                'codigo': '200 OK',
                'estado': 'Llamada aceptada por el destino',
                'llamante': caller,
                'llamado': callee,
                'sdp_respuesta': 'Parámetros de medios negociados',
                'codec_seleccionado': 'PCMU (G.711 µ-law)',
                'puerto_rtp': '8000'
            }
        )
    
    async def handle_ack(self, msg: SIPMessage, addr: tuple):
        """Maneja ACK (confirmación de llamada establecida)"""
        call_id = msg.headers.get('Call-ID', 'unknown')
        
        voip_logger.log_step(
            "PASO 7: CONFIRMACIÓN (ACK)",
            {
                'metodo': 'ACK',
                'call_id': call_id,
                'estado': 'Llamada establecida completamente',
                'accion': 'Inicio de transmisión de audio (RTP)',
                'protocolo_audio': 'RTP (Real-time Transport Protocol)',
                'codec': 'G.711 µ-law',
                'tasa_muestreo': '8000 Hz',
                'bitrate': '64 kbps'
            }
        )
        
        if call_id in self.active_calls:
            call = self.active_calls[call_id]
            voip_logger.log_step(
                "SESIÓN RTP INICIADA",
                {
                    'protocolo': 'RTP sobre UDP',
                    'llamante': call['caller'],
                    'llamado': call['callee'],
                    'estado': 'Conversación en curso',
                    'paquetización': '20ms por paquete',
                    'jitter_buffer': 'Activo para compensar variaciones de red'
                }
            )
    
    async def handle_bye(self, msg: SIPMessage, addr: tuple):
        """Maneja BYE (finalización de llamada)"""
        call_id = msg.headers.get('Call-ID', 'unknown')
        from_header = msg.headers.get('From', '')
        
        caller = self.extract_username(from_header)
        
        voip_logger.log_step(
            "PASO 8: FINALIZACIÓN DE LLAMADA (BYE)",
            {
                'metodo': 'BYE',
                'call_id': call_id,
                'usuario': caller,
                'accion': 'Solicitud de terminación de llamada',
                'estado': 'Cerrando sesión RTP'
            }
        )
        
        # Enviar 200 OK
        bye_response = self.create_bye_response(msg)
        self.socket.sendto(bye_response.encode('utf-8'), addr)
        
        # Eliminar llamada activa
        if call_id in self.active_calls:
            call = self.active_calls.pop(call_id)
            
            voip_logger.log_step(
                "PASO 9: LLAMADA TERMINADA (200 OK)",
                {
                    'codigo': '200 OK',
                    'call_id': call_id,
                    'llamante': call['caller'],
                    'llamado': call['callee'],
                    'inicio': call['started_at'],
                    'fin': datetime.now().isoformat(),
                    'estado': 'Sesión completamente cerrada',
                    'recursos': 'Liberados'
                }
            )
    
    async def handle_options(self, msg: SIPMessage, addr: tuple):
        """Maneja OPTIONS (consulta de capacidades)"""
        voip_logger.log_step(
            "CONSULTA DE CAPACIDADES (OPTIONS)",
            {
                'metodo': 'OPTIONS',
                'desde_ip': f"{addr[0]}:{addr[1]}",
                'estado': 'Cliente consultando capacidades del servidor'
            }
        )
        
        response = self.create_options_response(msg)
        self.socket.sendto(response.encode('utf-8'), addr)
        
        voip_logger.log_step(
            "RESPUESTA DE CAPACIDADES (200 OK)",
            {
                'codigo': '200 OK',
                'metodos_soportados': 'INVITE, ACK, BYE, CANCEL, OPTIONS, REGISTER',
                'codecs': 'PCMU, PCMA, G.729',
                'transporte': 'UDP, TCP'
            }
        )
    
    def parse_sdp(self, sdp_body: str, username: str):
        """Parsea el cuerpo SDP"""
        lines = sdp_body.split('\r\n')
        sdp_info = {}
        
        for line in lines:
            if line.startswith('v='):
                sdp_info['version'] = line[2:]
            elif line.startswith('o='):
                sdp_info['origin'] = line[2:]
            elif line.startswith('c='):
                sdp_info['connection'] = line[2:]
            elif line.startswith('m='):
                sdp_info['media'] = line[2:]
            elif line.startswith('a=rtpmap:'):
                if 'codecs' not in sdp_info:
                    sdp_info['codecs'] = []
                sdp_info['codecs'].append(line[9:])
        
        voip_logger.log_step(
            "ANÁLISIS SDP (Session Description Protocol)",
            {
                'usuario': username,
                'version': sdp_info.get('version', 'N/A'),
                'conexion': sdp_info.get('connection', 'N/A'),
                'media': sdp_info.get('media', 'N/A'),
                'codecs_disponibles': ', '.join(sdp_info.get('codecs', [])) if 'codecs' in sdp_info else 'PCMU, PCMA'
            }
        )
    
    def extract_username(self, header: str) -> str:
        """Extrae el username de un header SIP"""
        match = re.search(r'sip:([^@]+)@', header)
        return match.group(1) if match else 'unknown'
    
    def create_register_response(self, msg: SIPMessage, username: str) -> str:
        """Crea respuesta 200 OK para REGISTER"""
        return f"""SIP/2.0 200 OK
Via: {msg.headers.get('Via', 'SIP/2.0/UDP')}
From: {msg.headers.get('From', '')}
To: {msg.headers.get('To', '')}
Call-ID: {msg.headers.get('Call-ID', '')}
CSeq: {msg.headers.get('CSeq', '')}
Contact: {msg.headers.get('Contact', '')}
Expires: 3600
Content-Length: 0

"""
    
    def create_trying_response(self, msg: SIPMessage) -> str:
        """Crea respuesta 100 Trying"""
        return f"""SIP/2.0 100 Trying
Via: {msg.headers.get('Via', 'SIP/2.0/UDP')}
From: {msg.headers.get('From', '')}
To: {msg.headers.get('To', '')}
Call-ID: {msg.headers.get('Call-ID', '')}
CSeq: {msg.headers.get('CSeq', '')}
Content-Length: 0

"""
    
    def create_ringing_response(self, msg: SIPMessage) -> str:
        """Crea respuesta 180 Ringing"""
        return f"""SIP/2.0 180 Ringing
Via: {msg.headers.get('Via', 'SIP/2.0/UDP')}
From: {msg.headers.get('From', '')}
To: {msg.headers.get('To', '')}
Call-ID: {msg.headers.get('Call-ID', '')}
CSeq: {msg.headers.get('CSeq', '')}
Content-Length: 0

"""
    
    def create_invite_ok_response(self, msg: SIPMessage) -> str:
        """Crea respuesta 200 OK para INVITE"""
        sdp = """v=0
o=VoIPDemo 123456 654321 IN IP4 192.168.100.1
s=VoIP Call
c=IN IP4 192.168.100.1
t=0 0
m=audio 8000 RTP/AVP 0
a=rtpmap:0 PCMU/8000
"""
        return f"""SIP/2.0 200 OK
Via: {msg.headers.get('Via', 'SIP/2.0/UDP')}
From: {msg.headers.get('From', '')}
To: {msg.headers.get('To', '')}
Call-ID: {msg.headers.get('Call-ID', '')}
CSeq: {msg.headers.get('CSeq', '')}
Contact: <sip:server@192.168.100.1:5060>
Content-Type: application/sdp
Content-Length: {len(sdp)}

{sdp}"""
    
    def create_bye_response(self, msg: SIPMessage) -> str:
        """Crea respuesta 200 OK para BYE"""
        return f"""SIP/2.0 200 OK
Via: {msg.headers.get('Via', 'SIP/2.0/UDP')}
From: {msg.headers.get('From', '')}
To: {msg.headers.get('To', '')}
Call-ID: {msg.headers.get('Call-ID', '')}
CSeq: {msg.headers.get('CSeq', '')}
Content-Length: 0

"""
    
    def create_options_response(self, msg: SIPMessage) -> str:
        """Crea respuesta 200 OK para OPTIONS"""
        return f"""SIP/2.0 200 OK
Via: {msg.headers.get('Via', 'SIP/2.0/UDP')}
From: {msg.headers.get('From', '')}
To: {msg.headers.get('To', '')}
Call-ID: {msg.headers.get('Call-ID', '')}
CSeq: {msg.headers.get('CSeq', '')}
Allow: INVITE, ACK, BYE, CANCEL, OPTIONS, REGISTER
Accept: application/sdp
Content-Length: 0

"""
