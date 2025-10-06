import pandas as pd
from typing import List, Dict
from services.freshdesk_service import FreshdeskService
from services.clarity_service import ClarityService
from config.state_mapping import MAPEO_ESTADOS_FD_A_CLARITY

class SyncProcess:
    def __init__(self, config_manager):
        self.config = config_manager
        self.freshdesk_service = FreshdeskService(config_manager)
        self.clarity_service = ClarityService(config_manager)

    def obtener_tickets_freshdesk(self, limite=100) -> List[Dict]:
        """Obtener tickets de Freshdesk con paginación"""
        print("📥 Obteniendo tickets de Freshdesk...")
        todos_tickets = []
        pagina = 1
        
        while len(todos_tickets) < limite:
            tickets = self.freshdesk_service.obtener_tickets_paginados(pagina=pagina)
            if not tickets:
                break
            todos_tickets.extend(tickets)
            pagina += 1
            
            if len(tickets) < 100:  # Última página
                break
        
        print(f"✅ Obtenidos {len(todos_tickets)} tickets de Freshdesk")
        return todos_tickets[:limite]

    def comparar_estados(self, tickets_freshdesk: List[Dict]) -> List[Dict]:
        """Comparar estados entre Freshdesk y Clarity"""
        diferencias = []
        
        for ticket_fd in tickets_freshdesk:
            ticket_id = ticket_fd.get('id')
            estado_fd = ticket_fd.get('status')
            
            # Buscar ticket equivalente en Clarity
            ticket_clarity = self.clarity_service.buscar_ticket_por_codigo(str(ticket_id))
            
            if not ticket_clarity:
                continue  # Ticket no existe en Clarity
                
            # Obtener estado actual en Clarity
            estado_clarity_actual = self._extraer_estado_clarity(ticket_clarity)
            
            # Mapear estado Freshdesk a Clarity
            estado_clarity_propuesto = MAPEO_ESTADOS_FD_A_CLARITY.get(estado_fd)
            
            if not estado_clarity_propuesto:
                continue  # No hay mapeo para este estado
                
            # Comparar estados
            if estado_clarity_actual != estado_clarity_propuesto:
                diferencias.append({
                    'ticket_id': ticket_id,
                    'freshdesk_estado': estado_fd,
                    'clarity_estado_actual': estado_clarity_actual,
                    'clarity_estado_propuesto': estado_clarity_propuesto,
                    'investment_id': ticket_clarity.get('_parentId'),
                    'clarity_internal_id': ticket_clarity.get('_internalId')
                })
        
        return diferencias

    def _extraer_estado_clarity(self, ticket_clarity: Dict) -> str:
        """Extraer el estado de un ticket de Clarity"""
        estado_field = ticket_clarity.get('p_tdi_estado_freshdesk', {})
        if isinstance(estado_field, dict) and 'displayValue' in estado_field:
            return estado_field['displayValue']
        return str(estado_field)

    def mostrar_resumen_cambios(self, diferencias: List[Dict]):
        """Mostrar resumen de cambios propuestos"""
        print("\n" + "="*80)
        print("📊 RESUMEN DE CAMBIOS PROPUESTOS")
        print("="*80)
        
        if not diferencias:
            print("✅ No se encontraron diferencias entre Freshdesk y Clarity")
            return
        
        print(f"🔄 Se encontraron {len(diferencias)} tickets con diferencias:")
        print("-" * 80)
        
        for diff in diferencias:
            print(f"🎫 Ticket {diff['ticket_id']}:")
            print(f"   Freshdesk: {diff['freshdesk_estado']}")
            print(f"   Clarity actual: {diff['clarity_estado_actual']}")
            print(f"   Clarity propuesto: {diff['clarity_estado_propuesto']}")
            print()

    def sincronizar_estados(self):
        """Proceso principal de sincronización"""
        print("🚀 INICIANDO SINCRONIZACIÓN FRESHDESK → CLARITY")
        print("═" * 60)
        
        # Validar configuraciones
        if not self.config.validar_configuracion():
            return
        if not self.config.validar_configuracion_clarity():
            return
        
        # 1. Obtener tickets de Freshdesk
        tickets_fd = self.obtener_tickets_freshdesk(limite=50)  # Límite para prueba
        
        if not tickets_fd:
            print("❌ No se pudieron obtener tickets de Freshdesk")
            return
        
        # 2. Comparar estados
        diferencias = self.comparar_estados(tickets_fd)
        
        # 3. Mostrar resumen
        self.mostrar_resumen_cambios(diferencias)
        
        if not diferencias:
            return
        
        # 4. Confirmación del usuario
        print("\n⚠️  CONFIRMACIÓN REQUERIDA")
        print("-" * 40)
        confirmacion = input("¿Deseas aplicar estos cambios en Clarity? (escribe 'SI' en mayúsculas): ").strip()
        
        if confirmacion != "SI":
            print("🚫 Sincronización cancelada por el usuario")
            return
        
        # 5. Aplicar cambios
        print("\n🔄 Aplicando cambios en Clarity...")
        exitos = 0
        fallos = 0
        
        for diff in diferencias:
            print(f"Actualizando ticket {diff['ticket_id']}...", end=" ")
            
            if self.clarity_service.actualizar_estado_ticket(
                diff['investment_id'], 
                diff['clarity_internal_id'], 
                diff['clarity_estado_propuesto']
            ):
                print("✅")
                exitos += 1
            else:
                print("❌")
                fallos += 1
        
        # 6. Resumen final
        print("\n" + "="*60)
        print("🎉 SINCRONIZACIÓN COMPLETADA")
        print("="*60)
        print(f"✅ Actualizaciones exitosas: {exitos}")
        print(f"❌ Actualizaciones fallidas: {fallos}")
        print("═" * 60)