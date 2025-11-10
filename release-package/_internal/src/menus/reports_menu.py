# src/menus/reports_menu.py
from features.reports import Reports
from utils.display_utils import display

class ReportsMenu:
    def __init__(self, reports):
        self.reports = reports

    def mostrar_menu(self):
        while True:
            display.clear_screen()
            print("\n╔══════════════════════════════════════════════╗")
            print("║                📊 REPORTES                   ║")
            print("╚══════════════════════════════════════════════╝")
            
            print("   🏢 1. Lista de empresas") 
            print("   🔄 2. Productos diferentes (FD vs Clarity)")
            print("   🧠 3. Ir a Sistema de Clasificación")
            print("   ↩️  0. Volver al menú principal")
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.reports.reporte_empresas()
            elif opcion == "2":
                self.reports.reporte_productos_diferentes()
            elif opcion == "3":
                # Redirigir al menú de clasificación
                from menus.classification_menu import ClassificationMenu
                classification_menu = ClassificationMenu()
                classification_menu.mostrar_menu_principal()
            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida. Por favor, intente de nuevo.")
                display.press_enter_to_continue()