import logging
import sys
import os
from .formatters import LogFormatter
import datetime
import json
import traceback

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
    
    # ========== MÉTODOS ESTÁNDAR DE LOGGING ==========
    def info(self, message, *args, **kwargs):
        """Método estándar info"""
        self.logger.info(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """Método estándar error"""
        # Manejar exc_info de manera compatible
        if 'exc_info' in kwargs:
            exc_info = kwargs.pop('exc_info')
            if exc_info:
                # Si exc_info es True, capturar la traza actual
                kwargs['exc_info'] = sys.exc_info()
        self.logger.error(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """Método estándar warning"""
        self.logger.warning(message, *args, **kwargs)
    
    def debug(self, message, *args, **kwargs):
        """Método estándar debug"""
        self.logger.debug(message, *args, **kwargs)
    
    # ========== MÉTODOS PERSONALIZADOS ==========
    def log_info(self, message, user_friendly=None):
        """Log nivel INFO - solo archivo"""
        self.info(message)
    
    def log_error(self, message, user_friendly=None, exc_info=True):
        """Log nivel ERROR - solo archivo"""
        if exc_info:
            self.error(message, exc_info=True)
        else:
            self.error(message)
    
    def log_warning(self, message, user_friendly=None):
        """Log nivel WARNING - solo archivo"""
        self.warning(message)
    
    def log_debug(self, message, user_friendly=None):
        """Log nivel DEBUG - solo archivo"""
        self.debug(message)

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

    def _get_current_timestamp(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def log_transaction_change(self, transaction_id, change_data):
        """Registra cambios transaccionales"""
        try:
            log_message = f"TRANSACTION_CHANGE - {transaction_id}: {json.dumps(change_data, default=str)}"
            self.log_info(log_message)
        except Exception as e:
            self.log_error(f"Error en log_transaction_change: {e}")
    
    def _update_specific_change(self, transaction_id, ticket_id, update_data):
        """Actualiza un cambio específico en la transacción"""
        try:
            log_message = f"TRANSACTION_UPDATE - {transaction_id} - Ticket {ticket_id}: {json.dumps(update_data, default=str)}"
            self.log_info(log_message)
        except Exception as e:
            self.log_error(f"Error en _update_specific_change: {e}")