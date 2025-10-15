import logging
import os
from datetime import datetime, timedelta
import sys
import glob

class ProjectLogger:
    def __init__(self):
        self.logs_dir = self._get_logs_directory()
        self.setup_logging()
        self._clean_old_logs()  # 🆕 Limpiar logs antiguos al iniciar
    
    def _get_logs_directory(self):
        """Obtener directorio de logs, compatible con PyInstaller"""
        if getattr(sys, 'frozen', False):
            # Si estamos en un ejecutable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Si estamos en desarrollo
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        logs_dir = os.path.join(base_dir, "logs")
        return logs_dir
    
    def setup_logging(self):
        """Configurar el sistema de logging"""
        try:
            # Crear directorio de logs si no existe
            os.makedirs(self.logs_dir, exist_ok=True)
            
            # Configurar logging
            log_file = self._get_log_file_path()
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger('SyncDeskManager')
            self.log_info("Sistema de logging inicializado", "✅ Sistema de registro activado")
            
        except Exception as e:
            print(f"❌ Error crítico al configurar logging: {e}")
    
    def _get_log_file_path(self):
        """Obtener ruta del archivo de log diario"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.logs_dir, f"freshdesk_{timestamp}.log")
    
    def _clean_old_logs(self, days_to_keep=30):
        """🆕 Eliminar archivos de log más antiguos que `days_to_keep` días"""
        try:
            current_time = datetime.now()
            log_pattern = os.path.join(self.logs_dir, "freshdesk_*.log")
            
            log_files = glob.glob(log_pattern)
            deleted_count = 0
            
            for log_file in log_files:
                try:
                    # Obtener fecha del archivo desde su nombre (más confiable)
                    file_name = os.path.basename(log_file)
                    # Extraer fecha del formato: freshdesk_YYYY-MM-DD.log
                    date_str = file_name.replace('freshdesk_', '').replace('.log', '')
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Calcular antigüedad
                    file_age = current_time - file_date
                    
                    # Si el archivo es más viejo que days_to_keep, eliminarlo
                    if file_age > timedelta(days=days_to_keep):
                        os.remove(log_file)
                        deleted_count += 1
                        self.log_debug(f"Log antiguo eliminado: {file_name}")
                        
                except (ValueError, Exception) as e:
                    # Si falla el parsing por nombre, usar fecha de modificación
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                        file_age = current_time - file_mtime
                        
                        if file_age > timedelta(days=days_to_keep):
                            os.remove(log_file)
                            deleted_count += 1
                            self.log_debug(f"Log antiguo eliminado (por fecha mod): {os.path.basename(log_file)}")
                    except Exception:
                        # Si no se puede eliminar, continuar
                        continue
            
            if deleted_count > 0:
                self.log_info(f"Limpieza de logs completada: {deleted_count} archivos antiguos eliminados")
            else:
                self.log_debug("No se encontraron logs antiguos para eliminar")
                
        except Exception as e:
            # Usar print porque el logger podría no estar listo
            print(f"⚠️  Error al limpiar logs antiguos: {e}")
    
    def log_info(self, message, user_friendly=None):
        """Log nivel INFO"""
        self.logger.info(message)
        if user_friendly:
            print(f"ℹ️  {user_friendly}")
    
    def log_error(self, message, user_friendly=None, exc_info=True):
        """Log nivel ERROR con detalles completos"""
        self.logger.error(message, exc_info=exc_info)
        if user_friendly:
            print(f"❌ {user_friendly}")
    
    def log_warning(self, message, user_friendly=None):
        """Log nivel WARNING"""
        self.logger.warning(message)
        if user_friendly:
            print(f"⚠️  {user_friendly}")
    
    def log_debug(self, message, user_friendly=None):
        """Log nivel DEBUG"""
        self.logger.debug(message)
        if user_friendly:
            print(f"🔍 {user_friendly}")
    
    def log_api_call(self, endpoint, method, status_code=None):
        """Log específico para llamadas API"""
        message = f"API {method} {endpoint}"
        if status_code:
            message += f" - Status: {status_code}"
        self.log_info(message)

# Instancia global para usar en todo el proyecto
logger = ProjectLogger()