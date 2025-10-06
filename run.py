#!/usr/bin/env python3
"""
Ejecutar con: python run.py
"""

import os
import sys

# Agregar el directorio src al path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

print(f"🔍 Path configurado: {src_path}")

try:
    # Importar desde main sin prefijo src
    from src.main import main
    print("✅ Importación exitosa")
    main()
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    
    import traceback
    traceback.print_exc()
    input("Presiona Enter para salir...")