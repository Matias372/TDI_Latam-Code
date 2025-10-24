"""
Sistema de Logging Modular para SyncDesk Manager
"""
from .base_logger import ProjectLogger
from .transaction_logger import TransactionLogger
from .file_logger import FileLogger
from .system_logger import SystemLogger
from .api_logger import ApiLogger

# Instancia global para compatibilidad
logger = ProjectLogger()

__all__ = [
    'logger', 
    'ProjectLogger', 
    'TransactionLogger',
    'FileLogger', 
    'SystemLogger', 
    'ApiLogger'
]