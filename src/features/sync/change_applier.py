from utils.display_utils import display
from .models import SyncResult, TicketDifference
from datetime import datetime
import json

class ChangeApplier:
    def __init__(self, clarity_service, logger):
        self.clarity_service = clarity_service
        self.logger = logger
        self.tickets_fallidos = []  # 🆕 Lista para tickets con errores
    
    def aplicar_cambios_clarity(self, diferencias, transaction_id):
        """Aplicar cambios en Clarity - CONTINÚA CON ERRORES"""
        self.logger.log_info(f"Aplicando {len(diferencias)} cambios en Clarity...")
        self.tickets_fallidos = []  # 🆕 Reiniciar lista
        
        resultado = SyncResult(exitos=0, fallos=0, detalles=[], total_cambios=len(diferencias))
        
        for i, diff in enumerate(diferencias, 1):
            display.show_processing_message(
                ticket_id=diff.ticket_id,
                current=i,
                total=len(diferencias),
                status=f"Aplicando cambios..."
            )
            
            # 🆕 REGISTRAR CAMBIO CON MANEJO DE ERRORES
            try:
                self._registrar_cambio_transaccional(transaction_id, diff, 'PENDING')
            except Exception as e:
                self.logger.log_warning(f"Error registrando cambio para ticket {diff.ticket_id}: {e}")
            
            try:
                detalle = self._aplicar_cambio_individual(diff, i, len(diferencias), transaction_id)
                resultado.detalles.append(detalle)
                
                if detalle['resultado'] == 'Éxito':
                    resultado.exitos += 1
                    # 🆕 ACTUALIZAR CON MANEJO DE ERRORES
                    try:
                        self._actualizar_estado_cambio(transaction_id, diff.ticket_id, 'SUCCESS')
                    except Exception as e:
                        self.logger.log_warning(f"Error actualizando estado de éxito para {diff.ticket_id}: {e}")
                else:
                    resultado.fallos += 1
                    # 🆕 AGREGAR A LISTA DE FALLIDOS
                    self.tickets_fallidos.append({
                        'ticket_id': diff.ticket_id,
                        'error': detalle['error'],
                        'estado_actual': diff.clarity_estado_actual,
                        'estado_propuesto': diff.clarity_estado_propuesto
                    })
                    # 🆕 ACTUALIZAR CON MANEJO DE ERRORES
                    try:
                        self._actualizar_estado_cambio(transaction_id, diff.ticket_id, 'FAILED', detalle['error'])
                    except Exception as e:
                        self.logger.log_warning(f"Error actualizando estado de fallo para {diff.ticket_id}: {e}")
                        
            except Exception as e:
                # 🆕 CAPTURA DE ERRORES CRÍTICOS - CONTINÚA IGUAL
                resultado.fallos += 1
                error_msg = f"Error crítico procesando ticket {diff.ticket_id}: {str(e)}"
                self.logger.log_error(error_msg)
                
                # 🆕 AGREGAR A LISTA DE FALLIDOS
                self.tickets_fallidos.append({
                    'ticket_id': diff.ticket_id,
                    'error': error_msg,
                    'estado_actual': diff.clarity_estado_actual,
                    'estado_propuesto': diff.clarity_estado_propuesto
                })
        
        # 🆕 MOSTRAR RESUMEN AL FINAL
        self._mostrar_resumen_fallos(resultado)
        
        return resultado
    
    def _mostrar_resumen_fallos(self, resultado):
        """🎯 MOSTRAR RESUMEN DE TICKETS FALLIDOS"""
        if self.tickets_fallidos:
            display.show_message("\n" + "="*60, "warning")
            display.show_message("📋 RESUMEN DE TICKETS CON ERRORES", "warning")
            display.show_message("="*60, "warning")
            
            for i, fallo in enumerate(self.tickets_fallidos, 1):
                display.show_message(f"{i}. Ticket #{fallo['ticket_id']}", "error")
                display.show_message(f"   Estado actual: {fallo['estado_actual']}", "info")
                display.show_message(f"   Estado propuesto: {fallo['estado_propuesto']}", "info")
                display.show_message(f"   Error: {fallo['error']}", "error")
                display.show_message("   " + "-"*50, "debug")
            
            display.show_message(f"\n📊 Total: {len(self.tickets_fallidos)} tickets con errores", "error")
            display.show_message(f"✅ {resultado.exitos} tickets actualizados exitosamente", "success")
        else:
            display.show_message(f"🎉 ¡Todos los {resultado.exitos} tickets se actualizaron exitosamente!", "success")
    
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
        
        self.logger._update_specific_change(transaction_id, ticket_id, update_data)
    
    def _aplicar_cambio_individual(self, diferencia, current, total, transaction_id):
        """Aplicar cambio individual con manejo robusto de errores"""
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
                # 🆕 ERROR ESPECÍFICO DE LA API
                error_msg = "Error en la API - HTTP 400 (posiblemente datos inválidos)"
                self.logger.log_warning(f"❌ Error actualizando ticket {diferencia.ticket_id}: {error_msg}")
                return {
                    'ticket_id': diferencia.ticket_id,
                    'estado_actual': diferencia.clarity_estado_actual,
                    'estado_propuesto': diferencia.clarity_estado_propuesto,
                    'estado_freshdesk_original': diferencia.freshdesk_estado,
                    'resultado': 'Error',
                    'error': error_msg,
                    'investment_id': diferencia.investment_id,
                    'internal_id': diferencia.clarity_internal_id,
                    'timestamp': self.logger._get_current_timestamp()
                }
                
        except Exception as e:
            # 🆕 CAPTURA DE ERRORES DURANTE LA ACTUALIZACIÓN
            error_msg = f"Excepción durante actualización: {str(e)}"
            self.logger.log_error(f"❌ Excepción actualizando ticket {diferencia.ticket_id}: {error_msg}")
            return {
                'ticket_id': diferencia.ticket_id,
                'estado_actual': diferencia.clarity_estado_actual,
                'estado_propuesto': diferencia.clarity_estado_propuesto,
                'estado_freshdesk_original': diferencia.freshdesk_estado,
                'resultado': 'Error',
                'error': error_msg,
                'investment_id': diferencia.investment_id,
                'internal_id': diferencia.clarity_internal_id,
                'timestamp': self.logger._get_current_timestamp()
            }