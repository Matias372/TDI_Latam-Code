"""
Sistema SyncDesk Manager
"""

import os
import sys

# Agregar el directorio src al path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Importar el logger
from utils.logger import logger

def main():
    logger.log_info("🚀 Iniciando SyncDesk Manager...", "🚀 Iniciando SyncDesk Manager...")
    logger.log_info("📍 Versión Local", "📍 Versión Local")
    
    try:
        # Importar después de configurar el path
        from menus.main_menu import MainMenu
        
        logger.log_info("Módulos importados correctamente", "✅ Módulos importados correctamente")
        
        # Iniciar menú principal
        menu = MainMenu()
        menu.mostrar_menu()
        
    except ImportError as e:
        error_msg = f"Error de importación: {e}"
        logger.log_error(error_msg, "❌ Error al importar módulos. Revise la instalación.")
        input("Presiona Enter para salir...")
        
    except Exception as e:
        error_msg = f"Error inesperado en main: {e}"
        logger.log_error(error_msg, "❌ Error inesperado. Consulte el log para más detalles.")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()