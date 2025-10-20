#!/usr/bin/env python3
"""
Ejecutar con: python run.py
"""

import os
import sys
import traceback

def setup_environment():
    """Configura el entorno para desarrollo y para ejecutable"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Si estamos en un ejecutable de PyInstaller
    if getattr(sys, 'frozen', False):
        # En el ejecutable, los archivos están en sys._MEIPASS
        base_dir = getattr(sys, '_MEIPASS', current_dir)
        print(f"🔍 Modo Ejecutable - Base dir: {base_dir}")
    else:
        # En desarrollo
        base_dir = current_dir
        print(f"🔍 Modo Desarrollo - Base dir: {base_dir}")
    
    # Agregar src al path
    src_path = os.path.join(base_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    print(f"📁 Path configurado: {src_path}")
    print(f"📁 Sys.path: {sys.path}")
    
    return base_dir, src_path

# Configurar environment inmediatamente
BASE_DIR, SRC_DIR = setup_environment()

def emergency_startup_log(message):
    """Log de emergencia para el inicio"""
    try:
        log_dir = os.path.join(BASE_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "startup_emergency.log")
        
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except:
        print(f"EMERGENCY: {message}")

try:
    emergency_startup_log("Iniciando run.py")
    emergency_startup_log(f"BASE_DIR: {BASE_DIR}")
    emergency_startup_log(f"SRC_DIR: {SRC_DIR}")
    
    # Verificar que src existe
    if os.path.exists(SRC_DIR):
        emergency_startup_log(f"✅ SRC_DIR existe: {os.listdir(SRC_DIR)}")
    else:
        emergency_startup_log(f"❌ SRC_DIR no existe: {SRC_DIR}")
        print(f"❌ ERROR: No se encuentra la carpeta src en: {SRC_DIR}")
        print("📁 Directorio actual:", os.getcwd())
        print("📁 Contenido del directorio actual:", os.listdir('.'))
        input("Presiona Enter para salir...")
        sys.exit(1)
    
    # Importar desde main - usar importación absoluta
    from src.main import main
    print("✅ Importación exitosa")
    main()
    
except ImportError as e:
    error_msg = f"❌ Error de importación en run.py: {e}"
    print(error_msg)
    emergency_startup_log(error_msg)
    emergency_startup_log(f"Traceback: {traceback.format_exc()}")
    
    # Diagnóstico detallado
    print(f"\n🔍 DIAGNÓSTICO:")
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"📁 BASE_DIR: {BASE_DIR}")
    print(f"📁 SRC_DIR: {SRC_DIR}")
    print(f"📁 Existe SRC_DIR: {os.path.exists(SRC_DIR)}")
    
    if os.path.exists(SRC_DIR):
        print(f"📁 Contenido de SRC_DIR: {os.listdir(SRC_DIR)}")
        if os.path.exists(os.path.join(SRC_DIR, 'utils')):
            print(f"📁 Contenido de src/utils: {os.listdir(os.path.join(SRC_DIR, 'utils'))}")
    
    print(f"🐍 Python path: {sys.path}")
    
    input("\nPresiona Enter para salir...")
    
except Exception as e:
    error_msg = f"❌ Error inesperado en run.py: {e}"
    print(error_msg)
    emergency_startup_log(error_msg)
    emergency_startup_log(f"Traceback: {traceback.format_exc()}")
    input("Presiona Enter para salir...")