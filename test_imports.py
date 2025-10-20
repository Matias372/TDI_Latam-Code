#!/usr/bin/env python3
"""
Script para testear imports antes del build
"""

import os
import sys
import traceback

def setup_environment():
    """Configurar el entorno antes de los tests"""
    print("🔧 Configurando entorno...")
    
    # Configurar path igual que en main.py
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_path)
    print(f"📁 Path configurado: {src_path}")
    
    # Configurar logging básico para evitar errores
    import logging
    logging.basicConfig(level=logging.ERROR, format='%(message)s')

def test_basic_imports():
    """Testear imports básicos sin pandas primero"""
    print("🧪 TESTEANDO IMPORTS BÁSICOS...")
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"🐍 Python path: {sys.executable}")
    
    basic_modules = [
        "utils.logger",
        "utils.file_utils", 
        "utils.display_utils",
        "config.config_manager"
    ]
    
    all_ok = True
    
    for module in basic_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            all_ok = False
    
    return all_ok

def test_pandas_imports():
    """Testear imports que requieren pandas"""
    print("\n🧪 TESTEANDO IMPORTS CON PANDAS...")
    
    # Primero testear pandas solo
    try:
        import pandas as pd
        print(f"✅ pandas {pd.__version__}")
    except Exception as e:
        print(f"❌ pandas: {e}")
        return False
    
    # Luego testear módulos que usan pandas
    pandas_modules = [
        "utils.template_manager",
        "services.freshdesk_service",
        "features.processes", 
        "features.reports"
    ]
    
    all_ok = True
    
    for module in pandas_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            all_ok = False
    
    return all_ok

def main():
    setup_environment()
    
    # Testear imports básicos primero
    basic_ok = test_basic_imports()
    
    # Testear imports con pandas
    pandas_ok = test_pandas_imports()
    
    if basic_ok and pandas_ok:
        print("\n🎉 TODOS LOS IMPORTS FUNCIONAN CORRECTAMENTE")
        return 0
    else:
        print("\n💥 ALGUNOS IMPORTS FALLARON")
        if not pandas_ok:
            print("\n💡 SUGERENCIA: Ejecuta 'pip install numpy==1.24.3 pandas==1.5.3'")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPresiona Enter para salir...")
    sys.exit(exit_code)