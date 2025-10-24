from utils.display_utils import display
from .models import TicketDifference

class ClarityIdResolver:
    def __init__(self, clarity_service, logger):
        self.clarity_service = clarity_service
        self.logger = logger
    
    def resolver_ids_clarity(self, diferencias):
        """Obtener IDs de Clarity para las diferencias"""
        if not diferencias:
            return []
        
        self.logger.log_info(f"Buscando IDs de Clarity para {len(diferencias)} tickets...")
        
        diferencias_completas = []
        tickets_encontrados = 0
        
        for i, diff in enumerate(diferencias, 1):
            if i % 10 == 0 or i == len(diferencias):
                display.update_progress(
                    current=i,
                    total=len(diferencias),
                    prefix="🔍 Buscando IDs Clarity:",
                    suffix=f"| Encontrados: {tickets_encontrados}"
                )
            
            diferencia_completa = self._resolver_id_ticket(diff)
            if diferencia_completa:
                diferencias_completas.append(diferencia_completa)
                tickets_encontrados += 1
        
        display.clear_line()
        self.logger.log_info(f"IDs obtenidos: {tickets_encontrados}/{len(diferencias)} tickets")
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