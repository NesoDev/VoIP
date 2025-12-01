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
        self.ip_counter = 1
        self.logger = VoIPLogger()
        
    def generate_internal_ip(self) -> str:
        """Genera una IP interna única para el usuario"""
        ip = f"192.168.100.{self.ip_counter}"
        self.ip_counter += 1
        if self.ip_counter > 254:
            self.ip_counter = 1
        return ip
    
    def register_user(self, username: str) -> User:
        """Registra un nuevo usuario"""
        if username in self.users:
            # Actualizar heartbeat si ya existe
            self.users[username].last_heartbeat = time.time()
            self.logger.log_step(
                "USUARIO YA REGISTRADO - ACTUALIZACIÓN",
                {
                    'username': username,
                    'ip_interna': self.users[username].internal_ip,
                    'estado': self.users[username].status
                }
            )
            return self.users[username]
        
        internal_ip = self.generate_internal_ip()
        sip_port = 5060 + len(self.users)
        
        user = User(
            username=username,
            internal_ip=internal_ip,
            sip_port=sip_port,
            registered_at=time.time(),
            last_heartbeat=time.time(),
            status="online"
        )
        
        self.users[username] = user
        
        self.logger.log_step(
            "REGISTRO DE USUARIO",
            {
                'username': username,
                'ip_interna': internal_ip,
                'puerto_sip': sip_port,
                'timestamp': datetime.now().isoformat(),
                'total_usuarios': len(self.users)
            }
        )
        
        return user
    
    def update_heartbeat(self, username: str) -> bool:
        """Actualiza el heartbeat de un usuario"""
        if username in self.users:
            old_time = self.users[username].last_heartbeat
            self.users[username].last_heartbeat = time.time()
            
            self.logger.log_step(
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
