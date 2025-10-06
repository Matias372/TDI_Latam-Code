import pandas as pd
import os
from tkinter import messagebox
from .file_utils import FileUtils
from ..config.constants import TEMPLATES_DIR, AGENTES_TEMPLATE

class TemplateManager:
    @staticmethod
    def inicializar_template_agentes():
        """Inicializar template de agentes si no existe"""
        if not os.path.exists(AGENTES_TEMPLATE):
            # Crear template básico
            template_data = {
                'ID': [],
                'Agente': [],
                'MAIL': []
            }
            df = pd.DataFrame(template_data)
            df.to_excel(AGENTES_TEMPLATE, index=False)
            print("✅ Template de agentes creado en:", AGENTES_TEMPLATE)
    
    @staticmethod
    def cargar_o_seleccionar_agentes():
        """Cargar template de agentes o permitir seleccionar uno nuevo"""
        TemplateManager.inicializar_template_agentes()
        
        print("\n👥 OPCIONES DE ARCHIVO DE AGENTES:")
        print("1. Usar template guardado")
        print("2. Seleccionar archivo diferente")
        
        opcion = input("Seleccione opción (1/2): ").strip()
        
        if opcion == "1":
            return AGENTES_TEMPLATE
        elif opcion == "2":
            archivo = FileUtils.seleccionar_archivo("Seleccione archivo de agentes")
            if archivo:
                # Opcional: actualizar el template con el nuevo archivo
                if messagebox.askyesno("Actualizar Template", "¿Desea actualizar el template con este archivo?"):
                    TemplateManager.actualizar_template_agentes(archivo)
            return archivo
        else:
            print("❌ Opción inválida, usando template por defecto")
            return AGENTES_TEMPLATE
    
    @staticmethod
    def actualizar_template_agentes(nuevo_archivo):
        """Actualizar el template con un nuevo archivo de agentes"""
        try:
            df_nuevo = pd.read_excel(nuevo_archivo)
            df_nuevo.to_excel(AGENTES_TEMPLATE, index=False)
            print("✅ Template de agentes actualizado")
        except Exception as e:
            print(f"❌ Error al actualizar template: {e}")