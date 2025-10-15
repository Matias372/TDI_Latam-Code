from features.sync_processes import SyncProcess
from utils.display_utils import display

class ProcessesMenu:
    def __init__(self, processes, config_manager):
        self.processes = processes
        self.config_manager = config_manager

    def mostrar_menu(self):
        while True:
            display.clear_screen()
            print("\n╔══════════════════════════════════════════════╗")
            print("║                ⚙️ PROCESOS                    ║")
            print("╚══════════════════════════════════════════════╝")
            
            print("   📨 1. Revisar tickets sin actividad")
            print("   🔄 2. Sincronizar estados (Freshdesk → Clarity)")
            print("   ↩️  0. Volver al menú principal")
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.processes.enviar_notas_internas()
            elif opcion == "2":
                sync = SyncProcess(self.config_manager)
                sync.sincronizar_estados()
            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida. Por favor, intente de nuevo.")
                display.press_enter_to_continue()