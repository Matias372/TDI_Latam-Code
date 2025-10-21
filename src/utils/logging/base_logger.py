import logging
import sys
import os
from .formatters import LogFormatter

class BaseLogger:
    """Logger base - SOLO para logging técnico, NO para interfaz de usuario"""
    
    def __init__(self):
        self.logger = None
        self.setup_logging()
    
    def setup_logging(self):
        """Configuración core del sistema de logging - SIN salida a consola"""
        self.logger = logging.getLogger('SyncDeskManager')
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar logs duplicados
        self.logger.handlers.clear()
        
        # 🎯 IMPORTANTE: No agregamos handler de consola aquí
        # La consola es solo para la interfaz de usuario via DisplayUtils
    
    def log_info(self, message, user_friendly=None):
        """Log nivel INFO - solo archivo"""
        self.logger.info(message)
        # 🎯 ELIMINADO: No hacer print aquí - usar DisplayUtils en código principal
    
    def log_error(self, message, user_friendly=None, exc_info=True):
        """Log nivel ERROR - solo archivo"""
        self.logger.error(message, exc_info=exc_info)
        # 🎯 ELIMINADO: No hacer print aquí - usar DisplayUtils en código principal
    
    def log_warning(self, message, user_friendly=None):
        """Log nivel WARNING - solo archivo"""
        self.logger.warning(message)
        # 🎯 ELIMINADO: No hacer print aquí - usar DisplayUtils en código principal
    
    def log_debug(self, message, user_friendly=None):
        """Log nivel DEBUG - solo archivo"""
        self.logger.debug(message)
        # 🎯 ELIMINADO: No hacer print aquí - usar DisplayUtils en código principal

class ProjectLogger(BaseLogger):
    """Logger principal - separación clara entre logs técnicos y interfaz de usuario"""
    
    def __init__(self):
        super().__init__()
        from .file_logger import FileLogger
        from .transaction_logger import TransactionLogger
        from .system_logger import SystemLogger
        from .api_logger import ApiLogger
        
        # Inicializar módulos especializados
        self.file_logger = FileLogger(self)
        self.transaction_logger = TransactionLogger(self)
        self.system_logger = SystemLogger(self)
        self.api_logger = ApiLogger(self)
        
        # Configurar handlers de archivo (SOLO archivo, NO consola)
        self.file_logger.setup_file_handlers()
        
        # Configurar logs de sistema (solo archivo)
        self.system_logger.log_system_info()