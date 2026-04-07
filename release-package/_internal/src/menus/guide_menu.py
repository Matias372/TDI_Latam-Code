from features.guide import UserGuide
from utils.display_utils import display

class GuideMenu:
    def __init__(self):
        self.guide = UserGuide()

    def mostrar_menu(self):
        while True:
            display.clear_screen()
            print("\n╔══════════════════════════════════════════════╗")
            print("║                GUÍA DE USUARIO              ║")
            print("╚══════════════════════════════════════════════╝")
            
            # Listar secciones disponibles
            sections = self.guide.list_sections()
            for i, (key, title) in enumerate(sections, 1):
                print(f"   {i}. {title}")
            
            print("   ↩  0. Volver al menú principal")
            
            opcion = input("\n Seleccione una sección: ").strip()

            if opcion == "0":
                break
            
            # Convertir opción numérica a clave de sección
            try:
                opcion_num = int(opcion)
                if 1 <= opcion_num <= len(sections):
                    section_key = sections[opcion_num - 1][0]
                    # Aquí está el cambio: capturar el retorno de mostrar_seccion
                    salir_al_menu_principal = self.mostrar_seccion(section_key)
                    if salir_al_menu_principal:
                        break  # Salir completamente y volver al menú principal
                else:
                    print(" Opción inválida.")
                    display.press_enter_to_continue()
            except ValueError:
                print(" Por favor ingrese un número válido.")
                display.press_enter_to_continue()

    def mostrar_seccion(self, section_key):
        """Mostrar una sección específica de la guía"""
        while True:
            display.clear_screen()
            
            # Obtener contenido de la sección
            contenido = self.guide.get_section(section_key)
            print(contenido)
            
            print("\n──────────────────────────────────────────────────")
            print("1. ↩  Volver al índice de la guía")
            print("2.  Volver al menú principal")
            
            opcion = input("\n Seleccione una opción: ").strip()

            if opcion == "1":
                break
            elif opcion == "2":
                return True  # Indicar salida completa
            else:
                print(" Opción inválida.")
                display.press_enter_to_continue()
        
        return False