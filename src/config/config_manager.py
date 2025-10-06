import json
from getpass import getpass
from .constants import CONFIG_FILE

class ConfigManager:
    def __init__(self):
        self.api_key = None
        self.freshdesk_domain = None
        self.load_config()

    def load_config(self):
        """Cargar configuración desde archivo"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.api_key = config.get('api_key')
                self.freshdesk_domain = config.get('freshdesk_domain')
        except FileNotFoundError:
            self.api_key = None
            self.freshdesk_domain = None

    def save_config(self):
        """Guardar configuración en archivo"""
        config = {
            'api_key': self.api_key,
            'freshdesk_domain': self.freshdesk_domain
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

    def ingresar_datos(self):
        """Interfaz para ingresar datos de conexión"""
        while True:
            print("\n=== CONFIGURACIÓN DE CONEXIÓN ===")
            print("1. Ingresar/Modificar API Key")
            print("2. Ingresar/Modificar Dominio Freshdesk")
            print("3. Ver configuración actual")
            print("0. Volver")
            
            opcion = input("Seleccione una opción: ").strip()

            if opcion == "1":
                self.api_key = input("👉 Ingrese la API Key: ").strip()
                self.save_config()
                print("✅ API Key guardada.\n")

            elif opcion == "2":
                dominio = input("🌐 Ingrese el subdominio de Freshdesk (ej: 'GreenDay'): ").strip()
                if dominio:
                    self.freshdesk_domain = f"https://{dominio}.freshdesk.com"
                    self.save_config()
                    print(f"✅ Dominio configurado: {self.freshdesk_domain}\n")
                else:
                    print("❌ Dominio inválido.\n")

            elif opcion == "3":
                self.mostrar_configuracion()

            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida.\n")

    def mostrar_configuracion(self):
        """Mostrar configuración actual"""
        print("\n--- Configuración actual ---")
        print(f"API Key: {'✅ Cargada' if self.api_key else '❌ No configurada'}")
        print(f"Dominio: {self.freshdesk_domain if self.freshdesk_domain else '❌ No configurado'}")
        print("-----------------------------")

    def validar_configuracion(self):
        """Validar que la configuración esté completa"""
        if not self.api_key or not self.freshdesk_domain:
            print("⚠ Configuración incompleta. Use el menú de configuración primero.")
            return False
        return True