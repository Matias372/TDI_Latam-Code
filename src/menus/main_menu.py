# CORRECTO ✅
from config.config_manager import ConfigManager
from services.freshdesk_service import FreshdeskService
from features.processes import Processes
from features.reports import Reports
from menus.processes_menu import ProcessesMenu
from menus.reports_menu import ReportsMenu
from utils.file_utils import FileUtils

class MainMenu:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.freshdesk_service = FreshdeskService(self.config_manager)
        self.reports = Reports(self.freshdesk_service)
        self.processes = Processes(self.freshdesk_service)
        self.reports_menu = ReportsMenu(self.reports)
        # Pasar tanto processes como config_manager a ProcessesMenu
        self.processes_menu = ProcessesMenu(self.processes, self.config_manager)

    def mostrar_estado_sistema(self):
        """Mostrar estado actual del sistema"""
        print("\n" + "="*40)
        print("   🔍 ESTADO DEL SISTEMA")
        print("="*40)
        print(f"🔑 API Key: {'✅ Cargada' if self.config_manager.api_key else '❌ No configurada'}")
        print(f"🌐 Dominio: {'✅ ' + self.config_manager.freshdesk_domain if self.config_manager.freshdesk_domain else '❌ No configurado'}")
        
        # Verificar archivos disponibles
        archivos = FileUtils.listar_archivos_input()
        print(f"📂 Archivos en input: {len(archivos)} disponibles")
        
        if archivos:
            print("   - " + "\n   - ".join(archivos))
        print("="*40)

    def mostrar_menu(self):
        while True:
            print("\n" + "="*40)
            print("   🚀 SISTEMA DE GESTIÓN FRESHDESK")
            print("="*40)
            print("1. 🔑 Configurar conexión")
            print("2. 🔍 Estado del sistema")
            print("3. 📊 Reportes")
            print("4. ⚙️ Procesos")
            print("0. ❌ Salir")
            
            opcion = input("\nSeleccione una opción: ").strip()

            if opcion == "1":
                self.config_manager.ingresar_datos()
            elif opcion == "2":
                self.mostrar_estado_sistema()
            elif opcion == "3":
                self.reports_menu.mostrar_menu()
            elif opcion == "4":
                self.processes_menu.mostrar_menu()
            elif opcion == "0":
                print("👋 ¡Hasta luego! Gracias por usar el sistema.")
                break
            else:
                print("❌ Opción inválida. Por favor, intente de nuevo.")