import pandas as pd
from datetime import datetime
from services.freshdesk_service import FreshdeskService
from utils.file_utils import FileUtils

class Reports:
    def __init__(self, freshdesk_service):
        self.service = freshdesk_service

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

        # Crear DataFrame y guardar
        df = pd.DataFrame(tickets_sin_etiquetas)
        ruta_archivo = FileUtils.guardar_excel(df, "Reporte_Tickets_Sin_Etiquetas.xlsx")
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
        ruta_archivo = FileUtils.guardar_excel(df, "Reporte_Empresas.xlsx")
        print(f"✅ Reporte generado con {len(datos_empresas)} empresas.")