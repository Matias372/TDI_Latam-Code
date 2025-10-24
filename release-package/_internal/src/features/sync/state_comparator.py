import pandas as pd
from config.state_mapping import MAPEO_ESTADOS_FD_TEXTO_A_CLARITY
from utils.display_utils import display
from .models import TicketDifference
import unicodedata

class StateComparator:
    def __init__(self, logger):
        self.logger = logger
        self.mapeo_estados = MAPEO_ESTADOS_FD_TEXTO_A_CLARITY
    
    def comparar_estados(self, df_freshdesk, df_clarity):
        """Comparar estados entre Freshdesk y Clarity - INTERFAZ LIMPIA"""
        self.logger.log_info("Iniciando comparación de estados...")
        display.show_message("Iniciando comparación de estados...", "sync")
        
        diferencias = []
        total_tickets = len(df_freshdesk)
        
        for index, ticket_fd in df_freshdesk.iterrows():
            current = index + 1
            
            # Mostrar progreso cada 50 tickets
            if current % 50 == 0 or current == total_tickets:
                display.update_progress(
                    current=current,
                    total=total_tickets,
                    prefix="🔍 Comparando estados",
                    suffix=f"| Diferencias: {len(diferencias)}"
                )
            
            diferencia = self._comparar_ticket_individual(ticket_fd, df_clarity)
            if diferencia:
                diferencias.append(diferencia)
        
        display.clear_line()
        self.logger.log_info(f"Comparación completada: {len(diferencias)} diferencias encontradas")
        
        if diferencias:
            display.show_message(f"Comparación completada: {len(diferencias)} diferencias encontradas", "success")
        else:
            display.show_message("Comparación completada: No se encontraron diferencias", "success")
            
        return diferencias
    
    def _comparar_ticket_individual(self, ticket_fd, df_clarity):
        """Comparar un ticket individual"""
        ticket_id = str(ticket_fd['Ticket ID'])
        estado_fd_original = ticket_fd['Estado']
        
        # Obtener estado mapeado
        estado_clarity_propuesto = self.mapeo_estados.get(estado_fd_original)
        if not estado_clarity_propuesto:
            self.logger.log_debug(f"Ticket {ticket_id}: Estado '{estado_fd_original}' no mapeado")
            return None
        
        # Buscar en Clarity
        ticket_clarity = df_clarity[df_clarity['ID'].astype(str) == ticket_id]
        if ticket_clarity.empty:
            self.logger.log_debug(f"Ticket {ticket_id}: No encontrado en Clarity")
            return None
        
        ticket_clarity = ticket_clarity.iloc[0]
        estado_clarity_actual = ticket_clarity['Estado_Freshdesk_Clarity']
        
        if estado_clarity_actual != estado_clarity_propuesto:
            self.logger.log_debug(f"Ticket {ticket_id}: Diferencia encontrada {estado_clarity_actual} -> {estado_clarity_propuesto}")
            return TicketDifference(
                ticket_id=ticket_id,
                freshdesk_estado=estado_fd_original,
                clarity_estado_actual=estado_clarity_actual,
                clarity_estado_propuesto=estado_clarity_propuesto
            )
        
        return None

    def analizar_estados_archivos(self, df_freshdesk, df_clarity):
        """🎯 ANÁLISIS COMPLETO: Distribución de estados antes de sincronizar"""
        display.show_message("Analizando distribución de estados...", "search")
        
        analisis = {
            'freshdesk': {
                'total_tickets': len(df_freshdesk),
                'estados': df_freshdesk['Estado'].value_counts().to_dict(),
                'estados_no_mapeados': []
            },
            'clarity': {
                'total_tickets': len(df_clarity),
                'estados': df_clarity['Estado_Freshdesk_Clarity'].value_counts().to_dict()
            },
            'coincidencias': 0,
            'tickets_sin_coincidencia': 0
        }
        
        # 🎯 IDENTIFICAR ESTADOS NO MAPEADOS
        estados_freshdesk = df_freshdesk['Estado'].unique()
        for estado in estados_freshdesk:
            estado_mapeado = self.mapeo_estados.get(estado)
            if not estado_mapeado:
                analisis['freshdesk']['estados_no_mapeados'].append(estado)
        
        # Contar coincidencias
        tickets_freshdesk = set(df_freshdesk['Ticket ID'].astype(str))
        tickets_clarity = set(df_clarity['ID'].astype(str))
        analisis['coincidencias'] = len(tickets_freshdesk.intersection(tickets_clarity))
        analisis['tickets_sin_coincidencia'] = len(tickets_freshdesk - tickets_clarity)
        
        self.logger.log_info(f"Análisis completado: {analisis['coincidencias']} coincidencias, {analisis['tickets_sin_coincidencia']} sin coincidencia")
        return analisis

    def mostrar_analisis_estados(self, analisis):
        """🎯 MUESTRA COMPLETA: Análisis de distribución de estados con DisplayUtils"""
        display.show_section("ANÁLISIS DE DISTRIBUCIÓN DE ESTADOS")
        
        # Resumen ejecutivo
        display.show_message("📊 RESUMEN EJECUTIVO", "header")
        display.show_key_value("Total tickets Freshdesk", str(analisis['freshdesk']['total_tickets']), 3)
        display.show_key_value("Total tickets Clarity", str(analisis['clarity']['total_tickets']), 3)
        display.show_key_value("Coincidencias de IDs", str(analisis['coincidencias']), 3)
        display.show_key_value("Tickets sin coincidencia", str(analisis['tickets_sin_coincidencia']), 3)
        
        # Distribución de estados Freshdesk
        display.show_message("", "info")  # Línea en blanco
        display.show_message("📊 DISTRIBUCIÓN DE ESTADOS FRESHDESK", "header")
        for estado, cantidad in analisis['freshdesk']['estados'].items():
            estado_mapeado = self.mapeo_estados.get(estado) or "❌ NO MAPEADO"
            display.show_key_value(f"{estado} ({cantidad})", estado_mapeado, 3)
        
        # Distribución de estados Clarity
        display.show_message("", "info")  # Línea en blanco
        display.show_message("📊 DISTRIBUCIÓN DE 'ESTADO FRESHDESK' EN CLARITY", "header")
        for estado, cantidad in analisis['clarity']['estados'].items():
            display.show_key_value(f"{estado}", f"{cantidad} tickets", 3)
        
        # Estados no mapeados
        if analisis['freshdesk']['estados_no_mapeados']:
            display.show_message("", "info")  # Línea en blanco
            display.show_message("⚠️  ESTADOS NO MAPEADOS EN FRESHDESK", "warning")
            for estado in analisis['freshdesk']['estados_no_mapeados']:
                display.show_message(f"   ❌ {estado}", "error")
        
        display.show_divider(60)

    def _normalizar_texto(self, texto):
        """🚀 NORMALIZACIÓN CONSISTENTE: maneja acentos, mayúsculas y espacios"""
        if pd.isna(texto):
            return ""
        
        # Convertir a string y limpiar
        texto_str = str(texto).strip().lower()
        
        # Eliminar acentos y caracteres especiales
        texto_str = unicodedata.normalize('NFKD', texto_str)
        texto_str = ''.join([c for c in texto_str if not unicodedata.combining(c)])
        
        # Eliminar espacios múltiples y caracteres especiales
        texto_str = ' '.join(texto_str.split())
        texto_str = texto_str.replace('-', ' ').replace('_', ' ')
        
        return texto_str