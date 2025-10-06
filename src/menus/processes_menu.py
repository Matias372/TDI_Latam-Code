from features.processes import Processes

class ProcessesMenu:
    def __init__(self, processes):
        self.processes = processes

    def mostrar_menu(self):
        while True:
            print("\n" + "="*30)
            print("   ⚙️ MENÚ DE PROCESOS")
            print("="*30)
            print("1. 📨 Revisar tickets sin actividad")
            print("0. ↩️ Volver al menú principal")
            
            opcion = input("\nSeleccione una opción: ").strip()

            if opcion == "1":
                self.processes.enviar_notas_internas()
            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida. Por favor, intente de nuevo.")