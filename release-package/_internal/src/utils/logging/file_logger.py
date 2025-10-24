import logging
import os
import sys
import glob
from datetime import datetime, timedelta

class FileLogger:
    """Manejo de archivos de log, rotación y limpieza"""
    
    def __init__(self, base_logger):
        self.base_logger = base_logger
        self.logs_dir = self._get_logs_directory()
    
    def _get_logs_directory(self):
        """Obtener directorio de logs, compatible con PyInstaller"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir
    
    def setup_file_handlers(self):
        """Configurar handlers de archivo para logging detallado"""
        try:
            log_file = self._get_log_file_path()
            
            # Handler para archivo (DEBUG - captura todo)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            from .formatters import LogFormatter
            formatter = LogFormatter()
            file_handler.setFormatter(formatter)
            
            self.base_logger.logger.addHandler(file_handler)
            
            # Configurar loggers de terceros para archivo solo
            self._setup_third_party_loggers(file_handler)
            
            # Limpiar logs antiguos
            self._clean_old_logs()
            
        except Exception as e:
            self.base_logger.log_error(f"Error configurando file handlers: {e}")
    
    def _get_log_file_path(self):
        """Obtener ruta del archivo de log diario"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.logs_dir, f"freshdesk_{timestamp}.log")
    
    def _setup_third_party_loggers(self, file_handler):
        """Configurar loggers de bibliotecas externas"""
        # urllib3 - solo a archivo, no a consola
        urllib3_logger = logging.getLogger("urllib3")
        urllib3_logger.setLevel(logging.DEBUG)
        urllib3_logger.addHandler(file_handler)
        urllib3_logger.propagate = False
        
        urllib3_connection_logger = logging.getLogger("urllib3.connectionpool")
        urllib3_connection_logger.setLevel(logging.DEBUG)
        urllib3_connection_logger.addHandler(file_handler)
        urllib3_connection_logger.propagate = False
    
    def _clean_old_logs(self, days_to_keep=30):
        """Eliminar archivos de log más antiguos que `days_to_keep` días"""
        try:
            current_time = datetime.now()
            log_pattern = os.path.join(self.logs_dir, "freshdesk_*.log")
            
            log_files = glob.glob(log_pattern)
            deleted_count = 0
            
            for log_file in log_files:
                try:
                    # Obtener fecha del archivo desde su nombre
                    file_name = os.path.basename(log_file)
                    date_str = file_name.replace('freshdesk_', '').replace('.log', '')
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Calcular antigüedad
                    file_age = current_time - file_date
                    
                    if file_age > timedelta(days=days_to_keep):
                        os.remove(log_file)
                        deleted_count += 1
                        self.base_logger.log_debug(f"Log antiguo eliminado: {file_name}")
                        
                except (ValueError, Exception):
                    # Si falla el parsing por nombre, usar fecha de modificación
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                        file_age = current_time - file_mtime
                        
                        if file_age > timedelta(days=days_to_keep):
                            os.remove(log_file)
                            deleted_count += 1
                            self.base_logger.log_debug(f"Log antiguo eliminado (por fecha mod): {os.path.basename(log_file)}")
                    except Exception:
                        continue
            
            if deleted_count > 0:
                self.base_logger.log_info(f"Limpieza de logs completada: {deleted_count} archivos antiguos eliminados")
                
        except Exception as e:
            self.base_logger.log_error(f"Error al limpiar logs antiguos: {e}")