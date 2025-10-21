from utils.display_utils import display
from .models import SyncResult, TicketDifference

class ChangeApplier:
    def __init__(self, clarity_service, logger):
        self.clarity_service = clarity_service
        self.logger = logger
    
    def aplicar_cambios_clarity(self, diferencias, transaction_id):
        """Aplicar cambios en Clarity CON LOGGING TRANSACCIONAL"""
        self.logger.log_info(f"Aplicando {len(diferencias)} cambios en Clarity...")
        
        resultado = SyncResult(exitos=0, fallos=0, detalles=[], total_cambios=len(diferencias))
        
        for i, diff in enumerate(diferencias, 1):
            display.show_processing_message(
                ticket_id=diff.ticket_id,
                current=i,
                total=len(diferencias),
                status=f"Aplicando cambios..."
            )
            
            # 🆕 REGISTRAR CAMBIO ANTES DE APLICAR
            self._registrar_cambio_transaccional(transaction_id, diff, 'PENDING')
            
            detalle = self._aplicar_cambio_individual(diff, i, len(diferencias), transaction_id)
            resultado.detalles.append(detalle)
            
            if detalle['resultado'] == 'Éxito':
                resultado.exitos += 1
                # 🆕 ACTUALIZAR ESTADO DEL CAMBIO A EXITOSO
                self._actualizar_estado_cambio(transaction_id, diff.ticket_id, 'SUCCESS')
            else:
                resultado.fallos += 1
                # 🆕 ACTUALIZAR ESTADO DEL CAMBIO A FALLIDO
                self._actualizar_estado_cambio(transaction_id, diff.ticket_id, 'FAILED', detalle['error'])
        
        return resultado
    
    def _registrar_cambio_transaccional(self, transaction_id, diferencia, estado):
        """Registrar cambio individual en la transacción"""
        change_data = {
            'ticket_id': diferencia.ticket_id,
            'system': 'CLARITY',
            'field': 'p_tdi_estado_freshdesk',
            'old_value': diferencia.clarity_estado_actual,
            'new_value': diferencia.clarity_estado_propuesto,
            'freshdesk_estado_original': diferencia.freshdesk_estado,
            'estado': estado,
            'rollback_data': {
                'investment_id': diferencia.investment_id,
                'internal_id': diferencia.clarity_internal_id
            },
            'timestamp': self.logger._get_current_timestamp()
        }
        
        self.logger.log_transaction_change(transaction_id, change_data)
    
    def _actualizar_estado_cambio(self, transaction_id, ticket_id, estado, error=None):
        """Actualizar estado de un cambio específico"""
        update_data = {
            'ticket_id': ticket_id,
            'estado': estado,
            'timestamp_actualizacion': self.logger._get_current_timestamp()
        }
        
        if error:
            update_data['error'] = error
        
        # Buscar y actualizar el cambio específico en la transacción
        self.logger._update_specific_change(transaction_id, ticket_id, update_data)
    
    def _aplicar_cambio_individual(self, diferencia, current, total, transaction_id):
        """Aplicar cambio individual"""
        try:
            exito = self.clarity_service.actualizar_estado_ticket(
                diferencia.investment_id, 
                diferencia.clarity_internal_id, 
                diferencia.clarity_estado_propuesto
            )
            
            if exito:
                self.logger.log_info(f"✅ Ticket {diferencia.ticket_id} actualizado exitosamente")
                return {
                    'ticket_id': diferencia.ticket_id,
                    'estado_actual': diferencia.clarity_estado_actual,
                    'estado_propuesto': diferencia.clarity_estado_propuesto,
                    'estado_freshdesk_original': diferencia.freshdesk_estado,
                    'resultado': 'Éxito',
                    'error': None,
                    'investment_id': diferencia.investment_id,
                    'internal_id': diferencia.clarity_internal_id,
                    'timestamp': self.logger._get_current_timestamp()
                }
            else:
                self.logger.log_error(f"❌ Error actualizando ticket {diferencia.ticket_id}")
                return {
                    'ticket_id': diferencia.ticket_id,
                    'estado_actual': diferencia.clarity_estado_actual,
                    'estado_propuesto': diferencia.clarity_estado_propuesto,
                    'estado_freshdesk_original': diferencia.freshdesk_estado,
                    'resultado': 'Error',
                    'error': 'Error general en la actualización - API retornó False',
                    'investment_id': diferencia.investment_id,
                    'internal_id': diferencia.clarity_internal_id,
                    'timestamp': self.logger._get_current_timestamp()
                }
                
        except Exception as e:
            self.logger.log_error(f"❌ Excepción actualizando ticket {diferencia.ticket_id}: {str(e)}")
            return {
                'ticket_id': diferencia.ticket_id,
                'estado_actual': diferencia.clarity_estado_actual,
                'estado_propuesto': diferencia.clarity_estado_propuesto,
                'estado_freshdesk_original': diferencia.freshdesk_estado,
                'resultado': 'Error',
                'error': f"Excepción: {str(e)}",
                'investment_id': diferencia.investment_id,
                'internal_id': diferencia.clarity_internal_id,
                'timestamp': self.logger._get_current_timestamp()
            }