from utils.display_utils import display
from .models import TicketDifference

class ClarityIdResolver:
    def __init__(self, clarity_service, logger):
        self.clarity_service = clarity_service
        self.logger = logger
    
    def resolver_ids_clarity(self, diferencias):
        """Obtener IDs de Clarity para las diferencias - CON MEJOR MANEJO DE ERRORES"""
        if not diferencias:
            return []
        
        self.logger.log_info(f"Buscando IDs de Clarity para {len(diferencias)} tickets...")
        
        diferencias_completas = []
        tickets_encontrados = 0
        tickets_no_encontrados = 0
        
        for i, diff in enumerate(diferencias, 1):
            # 🆕 MEJORA: Mostrar progreso cada 5 tickets para mejor rendimiento
            if i % 5 == 0 or i == len(diferencias):
                display.update_progress(
                    current=i,
                    total=len(diferencias),
                    prefix="🔍 Buscando IDs Clarity:",
                    suffix=f"| Encontrados: {tickets_encontrados}, No encontrados: {tickets_no_encontrados}"
                )
            
            diferencia_completa = self._resolver_id_ticket(diff)
            if diferencia_completa:
                diferencias_completas.append(diferencia_completa)
                tickets_encontrados += 1
            else:
                tickets_no_encontrados += 1
                self.logger.log_warning(f"Ticket {diff.ticket_id} no encontrado en Clarity")
        
        # 🆕 LIMPIAR LÍNEA Y MOSTRAR RESUMEN
        display.clear_line()
        
        if tickets_no_encontrados > 0:
            display.show_message(f"Resolución completada: {tickets_encontrados} encontrados, {tickets_no_encontrados} no encontrados", "warning")
        else:
            display.show_message(f"Resolución completada: {tickets_encontrados} encontrados", "success")
        
        self.logger.log_info(f"IDs obtenidos: {tickets_encontrados}/{len(diferencias)} tickets")
        
        # 🆕 SI NO SE ENCONTRÓ NINGÚN TICKET, RETORNAR LISTA VACÍA
        if tickets_encontrados == 0:
            display.show_message("❌ No se pudo encontrar ningún ticket en Clarity", "error")
            return []
        
        return diferencias_completas
    
    def _resolver_id_ticket(self, diferencia):
        """Resolver ID para un ticket individual"""
        ticket_clarity = self.clarity_service.obtener_ticket_por_codigo_directo(diferencia.ticket_id)
        
        if ticket_clarity:
            investment_id = ticket_clarity.get('_parentId')
            internal_id = ticket_clarity.get('_internalId')
            
            if investment_id and internal_id:
                diferencia.investment_id = investment_id
                diferencia.clarity_internal_id = internal_id
                return diferencia
        
        return None