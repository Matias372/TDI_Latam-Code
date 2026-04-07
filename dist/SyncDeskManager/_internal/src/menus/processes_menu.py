# src/menus/processes_menu.py
from features.sync import SyncOrchestrator as SyncProcess
from features.freshdesk_updater import FreshdeskDirectUpdater
from utils.display_utils import display

class ProcessesMenu:
    def __init__(self, processes, config_manager):
        self.processes = processes
        self.config_manager = config_manager

    def mostrar_menu(self):
        while True:
            display.clear_screen()
            print("\n╔══════════════════════════════════════════════╗")
            print("║                  PROCESOS                    ║")
            print("╚══════════════════════════════════════════════╝")
            
            print("    1. Revisar tickets sin actividad")
            print("    2. Sincronizar estados (Freshdesk → Clarity)")
            print("     3. Forzar regeneración de etiquetas CREATE CLARITY")
            print("   ↩  0. Volver al menú principal")
            
            opcion = input("\n Seleccione una opción: ").strip()

            if opcion == "1":
                self.processes.enviar_notas_internas()
            elif opcion == "2":
                sync = SyncProcess(self.config_manager)
                sync.sincronizar_estados()
            elif opcion == "3":
                self.regenerar_etiquetas_create_clarity()
            elif opcion == "0":
                break
            else:
                print(" Opción inválida. Por favor, intente de nuevo.")
                display.press_enter_to_continue()

    def regenerar_etiquetas_create_clarity(self):
        """Forzar regeneración de etiquetas CREATE CLARITY"""
        if not self.config_manager.validar_configuracion():
            print(" Configuración de Freshdesk no válida.")
            display.press_enter_to_continue()
            return

        # Crear instancia del actualizador
        updater = FreshdeskDirectUpdater(
            self.config_manager.freshdesk_domain,
            self.config_manager.api_key
        )

        # Ejecutar el proceso
        updater.procesar_actualizacion_etiquetas()