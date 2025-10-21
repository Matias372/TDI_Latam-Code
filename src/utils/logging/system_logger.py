import platform
import os
import sys
import getpass
from datetime import datetime

class SystemLogger:
    """Logs del sistema, diagnósticos y información del entorno"""
    
    def __init__(self, base_logger):
        self.base_logger = base_logger
    
    def log_system_info(self):
        """Log información crítica del sistema"""
        try:
            self.base_logger.log_info("=" * 50)
            self.base_logger.log_info("🚀 INICIANDO SYNC DESK MANAGER")
            self.base_logger.log_info("=" * 50)
            self.base_logger.log_info(f"Sistema operativo: {platform.system()} {platform.release()}")
            self.base_logger.log_info(f"Python: {platform.python_version()}")
            self.base_logger.log_info(f"Usuario: {getpass.getuser()}")
            self.base_logger.log_info(f"Directorio de trabajo: {os.getcwd()}")
            self.base_logger.log_info(f"Directorio de logs: {self.base_logger.file_logger.logs_dir}")
            self.base_logger.log_info("=" * 50)
            
        except Exception as e:
            self.base_logger.log_error(f"Error al loguear información del sistema: {e}")
    
    def log_system_diagnostics(self):
        """Log diagnóstico completo del sistema"""
        try:
            self.base_logger.log_info("=" * 60)
            self.base_logger.log_info("🔍 DIAGNÓSTICO DEL SISTEMA")
            self.base_logger.log_info("=" * 60)
            
            # Información básica del sistema
            self.base_logger.log_info(f"Sistema: {platform.system()} {platform.release()}")
            self.base_logger.log_info(f"Python: {platform.python_version()}")
            self.base_logger.log_info(f"Directorio: {os.getcwd()}")
            self.base_logger.log_info(f"Ejecutable: {sys.executable}")
            self.base_logger.log_info(f"Args: {sys.argv}")
            self.base_logger.log_info(f"Plataforma: {sys.platform}")
                    
            self.base_logger.log_info("=" * 60)
            
        except Exception as e:
            self.base_logger.log_warning(f"Error en diagnóstico del sistema: {e}")
    
    def log_import_attempt(self, module_name: str, success: bool, error_msg: str = None):
        """Log intentos de importación de módulos"""
        status = "✅" if success else "❌"
        message = f"Import {module_name}: {status}"
        if not success and error_msg:
            message += f" - Error: {error_msg}"
        self.base_logger.log_info(message)