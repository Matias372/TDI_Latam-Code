import os
import pandas as pd
from tkinter import filedialog, Tk
from config.constants import DATA_DIR, OUTPUT_DIR, TEMPLATES_DIR, CONFIG_FILE, AGENTES_TEMPLATE

class FileUtils:
    @staticmethod
    def seleccionar_archivo(titulo="Seleccionar archivo", tipos_archivo=[("Excel files", "*.xlsx *.xls")]):
        """Seleccionar archivo mediante diálogo"""
        root = Tk()
        root.withdraw()  # Ocultar ventana principal
        root.attributes('-topmost', True)  # Traer al frente
        
        archivo = filedialog.askopenfilename(
            title=titulo,
            filetypes=tipos_archivo,
            initialdir=DATA_DIR  # Cambiado de INPUT_DIR a DATA_DIR
        )
        root.destroy()
        return archivo

    @staticmethod
    def listar_archivos_input():
        """Listar archivos en la carpeta de input"""
        return [f for f in os.listdir(DATA_DIR) if f.endswith(('.xlsx', '.xls'))]  # Cambiado de INPUT_DIR a DATA_DIR

    @staticmethod
    def cargar_excel(ruta_archivo):
        """Cargar archivo Excel"""
        try:
            return pd.read_excel(ruta_archivo)
        except Exception as e:
            print(f"❌ Error al cargar archivo: {e}")
            return None

    @staticmethod
    def guardar_excel(dataframe, nombre_archivo):
        """Guardar DataFrame como Excel en output"""
        ruta_completa = os.path.join(OUTPUT_DIR, nombre_archivo)
        dataframe.to_excel(ruta_completa, index=False)
        print(f"✅ Archivo guardado: {ruta_completa}")
        return ruta_completa