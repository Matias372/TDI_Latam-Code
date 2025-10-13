from features.sync_processes import SyncProcess

class ProcessesMenu:
    def __init__(self, processes, config_manager):
        self.processes = processes
        self.config_manager = config_manager

    def mostrar_menu(self):
        while True:
            print("\n" + "="*30)
            print("   ⚙️ MENÚ DE PROCESOS")
            print("="*30)
            print("1. 📨 Revisar tickets sin actividad")
            print("2. 📁 Sincronizar estados desde archivos (Excel/CSV)")
            print("0. ↩️ Volver al menú principal")

            opcion = input("\nSeleccione una opción: ").strip()

            if opcion == "1":
                self.processes.enviar_notas_internas()
            elif opcion == "2":
                sync = SyncProcess(self.config_manager)
                sync.sincronizar_estados()  # Ahora usa archivos Excel/CSV
            elif opcion == "0":
                break
            else:
                print("✗ Opción inválida. Por favor, intente de nuevo.")