import pandas as pd
import os
from datetime import datetime
from services.freshdesk_service import FreshdeskService
from utils.file_utils import FileUtils

class Reports:
    def __init__(self, freshdesk_service):
        self.service = freshdesk_service

    def _obtener_ruta_descargas(self):
        """Obtiene la ruta de la carpeta de Descargas del usuario actual"""
        # Para Windows
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes, windll
            
            # Usar SHGetFolderPath para obtener la carpeta Downloads
            CSIDL_PERSONAL = 5  # My Documents
            SHGFP_TYPE_CURRENT = 0
            
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
            
            # En Windows, Downloads está dentro de Documents
            downloads_path = os.path.join(buf.value, "Downloads")
        else:
            # Para Linux/Mac
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Crear la carpeta si no existe
        os.makedirs(downloads_path, exist_ok=True)
        return downloads_path

    def _guardar_en_descargas(self, df, nombre_archivo):
        """Guarda un DataFrame en la carpeta de Descargas"""
        ruta_descargas = self._obtener_ruta_descargas()
        ruta_completa = os.path.join(ruta_descargas, nombre_archivo)
        
        try:
            df.to_excel(ruta_completa, index=False)
            print(f"📁 Archivo guardado en: {ruta_completa}")
            return ruta_completa
        except Exception as e:
            print(f"❌ Error al guardar el archivo: {str(e)}")
            # Fallback: guardar en la carpeta output original
            return FileUtils.guardar_excel(df, nombre_archivo)

    def reporte_tickets_sin_etiquetas(self):
        """Generar reporte de tickets sin etiquetas"""
        print("\n=== Generando reporte de tickets sin etiquetas ===")

        tickets_sin_etiquetas = []
        pagina = 1

        while True:
            tickets = self.service.obtener_tickets_paginados(pagina)
            if not tickets:
                break

            for ticket in tickets:
                etiquetas = ticket.get("tags")
                if not etiquetas:  # None o lista vacía
                    tickets_sin_etiquetas.append({
                        "ID": ticket.get("id"),
                        "Asunto": ticket.get("subject"),
                        "Estado": ticket.get("status"),
                        "Prioridad": ticket.get("priority"),
                        "URL": f"{self.service.config.freshdesk_domain}/a/tickets/{ticket.get('id')}"
                    })

            pagina += 1
            if len(tickets) < 100:  # Última página
                break

        if not tickets_sin_etiquetas:
            print("✅ Todos los tickets tienen al menos una etiqueta.")
            return

        # Crear DataFrame y guardar en Descargas
        df = pd.DataFrame(tickets_sin_etiquetas)
        nombre_archivo = f"Reporte_Tickets_Sin_Etiquetas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self._guardar_en_descargas(df, nombre_archivo)
        print(f"✅ Reporte generado con {len(tickets_sin_etiquetas)} tickets sin etiquetas.")

    def reporte_empresas(self):
        """Generar reporte de empresas"""
        print("\n=== Generando reporte de empresas ===")
        
        empresas = self.service.obtener_empresas()
        if not empresas:
            print("❌ No se pudieron obtener las empresas.")
            return

        datos_empresas = []
        for empresa in empresas:
            datos_empresas.append({
                "ID": empresa.get("id"),
                "Nombre": empresa.get("name"),
                "Dominio": empresa.get("domains", [""])[0] if empresa.get("domains") else "",
                "Creado": empresa.get("created_at")
            })

        df = pd.DataFrame(datos_empresas)
        nombre_archivo = f"Reporte_Empresas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self._guardar_en_descargas(df, nombre_archivo)
        print(f"✅ Reporte generado con {len(datos_empresas)} empresas.")