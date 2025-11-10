from config.config_manager import ConfigManager
from services.freshdesk_service import FreshdeskService
from features.processes import Processes
from features.reports import Reports
from menus.processes_menu import ProcessesMenu
from menus.reports_menu import ReportsMenu
from menus.classification_menu import ClassificationMenu  
from utils.file_utils import FileUtils
from utils.display_utils import display
from menus.guide_menu import GuideMenu

class MainMenu:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.freshdesk_service = FreshdeskService(self.config_manager)
        self.reports = Reports(self.freshdesk_service)
        self.processes = Processes(self.freshdesk_service)
        self.reports_menu = ReportsMenu(self.reports)
        self.processes_menu = ProcessesMenu(self.processes, self.config_manager)  
        self.guide_menu = GuideMenu()
        self.classification_menu = ClassificationMenu(  
            config_manager=self.config_manager, 
            freshdesk_service=self.freshdesk_service
        )

    def mostrar_estado_sistema(self):
        """Mostrar estado actual del sistema"""
        display.clear_screen()
        print("\n╔══════════════════════════════════════════════╗")
        print("║               🔍 ESTADO DEL SISTEMA          ║")
        print("╚══════════════════════════════════════════════╝")
        
        print(f"\n🔐 CONEXIONES:")
        print(f"   🌐 Freshdesk: {'✅ Configurado' if self.config_manager.api_key and self.config_manager.freshdesk_domain else '❌ No configurado'}")
        print(f"   🔐 Clarity: {'✅ Configurado' if self.config_manager.clarity_username and self.config_manager.clarity_domain else '❌ No configurado'}")
        
        # Estado del sistema de clasificación
        library_status = self._verificar_estado_biblioteca()
        print(f"   🧠 Clasificación: {library_status}")
        
        # Verificar archivos disponibles
        archivos = FileUtils.listar_archivos_input()
        print(f"\n📂 ARCHIVOS DISPONIBLES:")
        print(f"   📁 En input: {len(archivos)} archivos")
        if archivos:
            for archivo in archivos[:3]:
                print(f"      • {archivo}")
            if len(archivos) > 3:
                print(f"      ... y {len(archivos) - 3} más")
        
        print("\n──────────────────────────────────────────────────")
        display.press_enter_to_continue()

    def _verificar_estado_biblioteca(self):
        """Verifica el estado de la biblioteca de clasificación"""
        try:
            import os
            import json
            library_path = "data/classification/biblioteca_clasificacion_tickets.json"
            
            if not os.path.exists(library_path):
                return "❌ Sin biblioteca"
            
            with open(library_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_tickets = data.get('metadata', {}).get('total_tickets_analizados', 0)
            total_patrones = data.get('metadata', {}).get('total_patrones_encontrados', 0)
            
            return f"✅ {total_tickets} tickets, {total_patrones} patrones"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def mostrar_guia_usuario(self):
        """Mostrar guía de usuario completa"""
        self.guide_menu.mostrar_menu()

    def mostrar_menu(self):
        while True:
            display.clear_screen()
            print("\n╔══════════════════════════════════════════════╗")
            print("║             🚀 SYNC DESK MANAGER             ║")
            print("╚══════════════════════════════════════════════╝")
            
            print("   🔧 1. Configurar conexión")
            print("   📊 2. Reportes y análisis")
            print("   ⚙️  3. Procesos automáticos")
            print("   🧠 4. Sistema de Clasificación")  
            print("   🔍 5. Estado del sistema")        
            print("   ❓ 6. Guía de usuario")
            print("   ❌ 0. Salir del sistema")
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.config_manager.ingresar_datos()
            elif opcion == "2":
                self.reports_menu.mostrar_menu()
            elif opcion == "3":
                self.processes_menu.mostrar_menu()
            elif opcion == "4":  
                self.classification_menu.mostrar_menu_principal()
            elif opcion == "5":  
                self.mostrar_estado_sistema()
            elif opcion == "6":  
                self.mostrar_guia_usuario()
            elif opcion == "0":
                display.clear_screen()
                print("👋 ¡Hasta luego! Gracias por usar el sistema.")
                break
            else:
                print("❌ Opción inválida. Por favor, intente de nuevo.")
                display.press_enter_to_continue()