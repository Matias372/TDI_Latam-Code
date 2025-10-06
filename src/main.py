#!/usr/bin/env python3
"""
Sistema de Gestión Freshdesk
"""

import os
import sys

def main():
    print("🚀 Iniciando Sistema de Gestión Freshdesk...")
    print("📍 Versión Local")
    
    try:
        # Importar después de configurar el path
        from menus.main_menu import MainMenu
        
        print("✅ Módulos importados correctamente")
        
        # Iniciar menú principal
        menu = MainMenu()
        menu.mostrar_menu()
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()