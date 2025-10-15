import os
import sys
import platform

class DisplayUtils:
    @staticmethod
    def clear_screen():
        """Limpia la pantalla de manera cross-platform"""
        try:
            if platform.system() == "Windows":
                os.system('cls')
            else:
                os.system('clear')
        except:
            # Fallback: imprimir múltiples líneas nuevas
            print("\n" * 100)
    
    @staticmethod
    def clear_line():
        """Limpia la línea actual en la terminal"""
        print("\r" + " " * 100, end="", flush=True)
    
    @staticmethod
    def update_progress(current: int, total: int, prefix: str = "", suffix: str = ""):
        """Actualizar barra de progreso en la misma línea - MEJORADO"""
        bar_length = 30
        progress = current / total if total > 0 else 0
        filled_length = int(bar_length * progress)
        
        # Crear barra visual más atractiva
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        percentage = f"{progress * 100:.1f}%"
        
        # Mensaje completo con emojis
        message = f"\r{prefix} [{bar}] {percentage} ({current}/{total}) {suffix}"
        print(message, end="", flush=True)
    
    @staticmethod
    def show_processing_message(ticket_id: str, current: int, total: int, status: str = ""):
        """Mostrar mensaje de procesamiento actualizado en línea"""
        message = f"\r🔄 Procesando: Ticket #{ticket_id} [{current}/{total}] {status}"
        print(message, end="", flush=True)
    
    @staticmethod
    def press_enter_to_continue():
        """Esperar que el usuario presione Enter"""
        input("\n↩️  Presione Enter para continuar...")

# Instancia global
display = DisplayUtils()