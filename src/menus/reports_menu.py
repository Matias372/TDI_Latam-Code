from features.reports import Reports

class ReportsMenu:
    def __init__(self, reports):
        self.reports = reports

    def mostrar_menu(self):
        while True:
            print("\n" + "="*30)
            print("   📊 MENÚ DE REPORTES")
            print("="*30)
            print("1. 📋 Tickets sin etiquetas")
            print("2. 🏢 Lista de Empresas")
            print("0. ↩️ Volver al menú principal")
            
            opcion = input("\nSeleccione una opción: ").strip()

            if opcion == "1":
                self.reports.reporte_tickets_sin_etiquetas()
            elif opcion == "2":
                self.reports.reporte_empresas()
            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida. Por favor, intente de nuevo.")