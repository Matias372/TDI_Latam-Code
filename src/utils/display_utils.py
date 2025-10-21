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
            print("\n" * 100)
    
    @staticmethod
    def clear_line():
        """Limpia la línea actual en la terminal"""
        print("\r" + " " * 100, end="", flush=True)
    
    @staticmethod
    def update_progress(current: int, total: int, prefix: str = "", suffix: str = ""):
        """Actualizar barra de progreso en la misma línea"""
        bar_length = 30
        progress = current / total if total > 0 else 0
        filled_length = int(bar_length * progress)
        
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        percentage = f"{progress * 100:.1f}%"
        
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
    
    @staticmethod
    def show_message(message: str, message_type: str = "info"):
        """🎯 MOSTRAR MENSAJES FORMATEADOS AL USUARIO"""
        icons = {
            "info": "ℹ️",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌",
            "debug": "🔍",
            "header": "🚀",
            "file": "📁",
            "search": "🔍",
            "sync": "🔄",
            "config": "🔧",
            "user": "👤",
            "key": "🔑",
            "domain": "🌐"
        }
        
        icon = icons.get(message_type, "•")
        print(f"{icon}  {message}")
    
    @staticmethod
    def show_header(title: str):
        """🎯 MOSTRAR CABECERAS FORMATEADAS"""
        width = len(title) + 4  # +4 por los espacios y emojis
        print(f"\n╔{'═' * width}╗")
        print(f"║  {title}  ║")
        print(f"╚{'═' * width}╝")
    
    @staticmethod
    def show_section(title: str):
        """🎯 MOSTRAR SECCIONES"""
        print(f"\n📋 {title}")
        print("─" * (len(title) + 2))
    
    @staticmethod
    def show_subsection(title: str):
        """🎯 MOSTRAR SUBSECCIONES"""
        print(f"\n   📌 {title}")
        print("   " + "─" * (len(title) + 2))
    
    @staticmethod
    def show_divider(length: int = 50):
        """🎯 MOSTRAR DIVISOR"""
        print("─" * length)
    
    @staticmethod
    def show_bullet_list(items: list, bullet: str = "•"):
        """🎯 MOSTRAR LISTA CON VIÑETAS"""
        for item in items:
            print(f"   {bullet} {item}")
    
    @staticmethod
    def show_key_value(key: str, value: str, indent: int = 0):
        """🎯 MOSTRAR PAR CLAVE-VALOR"""
        indent_str = " " * indent
        print(f"{indent_str}{key}: {value}")
    
    @staticmethod
    def show_table(headers: list, rows: list, column_widths: list = None):
        """🎯 MOSTRAR TABLA FORMATEADA"""
        if not rows:
            return
            
        # Calcular anchos de columna si no se proporcionan
        if not column_widths:
            column_widths = [len(str(header)) for header in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    column_widths[i] = max(column_widths[i], len(str(cell)))
        
        # Crear formato de fila
        row_format = " | ".join([f"{{:<{width}}}" for width in column_widths])
        
        # Mostrar cabecera
        header_row = row_format.format(*headers)
        separator = "─" * len(header_row)
        
        print(f"\n{header_row}")
        print(separator)
        
        # Mostrar filas
        for row in rows:
            print(row_format.format(*[str(cell) for cell in row]))
        
        print(separator)

# Instancia global
display = DisplayUtils()