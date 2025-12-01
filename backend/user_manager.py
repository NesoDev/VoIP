import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json

# Configuración de logs detallados
class VoIPLogger:
    def __init__(self):
        self.setup_logger()
        self.call_logs = []
        
    def setup_logger(self):
        """Configura el sistema de logging detallado"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
        self.logger = logging.getLogger('VoIP')
        
    def log_step(self, step: str, details: dict):
        """Registra un paso detallado del proceso VoIP"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_entry = {
            'timestamp': timestamp,
            'step': step,
            'details': details
        }
        self.call_logs.append(log_entry)
        
        print("\n" + "="*80)
        print(f"TIMESTAMP: {timestamp}")
        print(f"STEP: {step}")
        print("DETAILS:")
        for key, value in details.items():
            print(f"   - {key}: {value}")
        print("="*80 + "\n")
        
    def get_logs(self) -> List[dict]:
        """Obtiene todos los logs registrados"""
        return self.call_logs
    
    def clear_logs(self):
        """Limpia los logs"""
        self.call_logs = []

@dataclass
class User:
    """Representa un usuario conectado"""
    username: str
    internal_ip: str
    sip_port: int
    registered_at: float
    last_heartbeat: float
    status: str = "online"  # online, busy, offline
    
    def to_dict(self):
        return asdict(self)

class UserManager:
    """Gestiona los usuarios conectados y sus IPs internas"""
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.call_manager = CallManager()
        # IP pool management
        self.ip_base = "192.168.100."
        self.next_ip = 10
        
    def generate_internal_ip(self) -> str:
        """Genera una IP interna única para el usuario"""
        # This method is no longer used as IP generation is inline in register_user
        # Keeping it for now to avoid breaking other parts if they still call it.
        # However, the new register_user logic implies it's not needed.
        ip = f"{self.ip_base}{self.next_ip}"
        self.next_ip += 1
        return ip
    
    def register_user(self, username: str) -> User:
        """Registra un nuevo usuario"""
        if username in self.users:
            user = self.users[username]
            user.last_heartbeat = time.time() # Assuming last_heartbeat is still the field
            user.status = "online"
            voip_logger.log_step(
                "REGISTRO DE USUARIO (EXISTENTE)",
                {
                    'usuario': username,
                    'ip_interna': user.internal_ip,
                    'estado': 'Reconexión exitosa'
                }
            )
            return user
            
        # Asignar nueva IP
        internal_ip = f"{self.ip_base}{self.next_ip}"
        self.next_ip += 1
        sip_port = 5060 + len(self.users) # Keep original SIP port logic
        
        user = User(
            username=username,
            internal_ip=internal_ip,
            sip_port=sip_port,
            registered_at=time.time(),
            last_heartbeat=time.time(),
            status="online"
        )
        self.users[username] = user
        
        voip_logger.log_step(
            "NUEVO REGISTRO DE USUARIO",
            {
                'usuario': username,
                'ip_asignada': internal_ip,
                'puertos': 'SIP:5060, RTP:10000+',
                'estado': 'Usuario creado y activo'
            }
        )
        return user
    
    def update_heartbeat(self, username: str) -> bool:
        """Actualiza el heartbeat de un usuario"""
        if username in self.users:
            old_time = self.users[username].last_heartbeat
            self.users[username].last_heartbeat = time.time()
            self.users[username].status = "online" # Ensure status is online on heartbeat
            
            voip_logger.log_step( # Changed to voip_logger as per new code
                "HEARTBEAT RECIBIDO",
                {
                    'username': username,
                    'ip_interna': self.users[username].internal_ip,
                    'ultimo_heartbeat': datetime.fromtimestamp(old_time).isoformat(),
                    'nuevo_heartbeat': datetime.now().isoformat(),
                    'diferencia_segundos': f"{time.time() - old_time:.2f}"
                }
            )
            return True
        return False
    
    def get_active_users(self, timeout: int = 30) -> List[User]:
        """Obtiene lista de usuarios activos (con heartbeat reciente)"""
        current_time = time.time()
        active_users = []
        
        for username, user in list(self.users.items()):
            if current_time - user.last_heartbeat > timeout:
                # Usuario inactivo
                self.logger.log_step(
                    "USUARIO DESCONECTADO POR TIMEOUT",
                    {
                        'username': username,
                        'ip_interna': user.internal_ip,
                        'ultimo_heartbeat': datetime.fromtimestamp(user.last_heartbeat).isoformat(),
                        'timeout_segundos': timeout,
                        'tiempo_inactivo': f"{current_time - user.last_heartbeat:.2f}"
                    }
                )
                user.status = "offline"
                # No lo eliminamos, solo marcamos como offline
            else:
                user.status = "online"
                active_users.append(user)
        
        return active_users
    
    def get_user(self, username: str) -> Optional[User]:
        """Obtiene información de un usuario específico"""
        return self.users.get(username)
    
    def get_all_users(self) -> List[User]:
        """Obtiene todos los usuarios (activos e inactivos)"""
        return list(self.users.values())

# Instancia global
user_manager = UserManager()
voip_logger = VoIPLogger()
