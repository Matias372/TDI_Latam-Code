"""
Sistema SyncDesk Manager
"""

import os
import sys
import traceback

def setup_paths():
    """Configurar paths - DEBE SER IDÉNTICA A run.py"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', current_dir)
    else:
        base_dir = os.path.dirname(current_dir)
    
    src_path = os.path.join(base_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    return base_dir, src_path

BASE_DIR, SRC_DIR = setup_paths()

def emergency_log(message):
    """Log de emergencia simple"""
    try:
        log_dir = os.path.join(BASE_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "emergency.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except:
        print(f"EMERGENCY: {message}")

def main():
    print("🚀 Iniciando SyncDesk Manager...")
    emergency_log("Iniciando main()")
    
    try:
        # Intentar importar módulos en orden
        emergency_log("Importando logger...")
        from utils.logger import logger
        
        emergency_log("Logger importado, configurando...")
        logger.log_info("Iniciando aplicación", "🚀 Iniciando SyncDesk Manager...")
        
        # Verificar otros módulos importantes
        emergency_log("Verificando imports críticos...")
        from menus.main_menu import MainMenu
        from config.config_manager import ConfigManager
        
        logger.log_info("Módulos cargados correctamente", "✅ Sistema listo")
        
        # Iniciar aplicación
        emergency_log("Creando menú principal...")
        config_manager = ConfigManager()
        menu = MainMenu()
        
        emergency_log("Mostrando menú...")
        menu.mostrar_menu()
        
        emergency_log("Aplicación finalizada normalmente")
        
    except Exception as e:
        error_msg = f"Error en main: {str(e)}\n{traceback.format_exc()}"
        emergency_log(f"❌ ERROR: {error_msg}")
        
        # Mostrar error al usuario
        print(f"\n💥 ERROR INESPERADO:")
        print(f"📝 {str(e)}")
        print(f"\n🔍 Para más detalles, revisa el archivo logs/emergency.log")
        
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()