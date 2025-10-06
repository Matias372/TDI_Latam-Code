#!/usr/bin/env python3
"""
Diagnóstico de imports
"""

import os
import sys

print("🔍 DIAGNÓSTICO DE IMPORTS")
print("=" * 50)

# Configurar path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

print(f"📁 Directorio src: {src_dir}")
print(f"🐍 Path de Python: {sys.path}")

# Probar imports uno por uno
modules_to_test = [
    'main',
    'menus.main_menu',
    'config.config_manager',
    'utils.file_utils',
    'services.freshdesk_service',
    'features.reports',
    'features.processes'
]

print("\n🧪 Probando imports...")
for module in modules_to_test:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module}: {e}")

print("\n🎯 Para ejecutar el sistema: python run.py")
input("Presiona Enter para salir...")