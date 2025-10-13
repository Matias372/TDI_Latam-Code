import requests
from requests.auth import HTTPBasicAuth
import urllib3
import time
from typing import Dict, Optional, List

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ClarityService:
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def _get_auth(self):
        """Obtener autenticación Basic Auth"""
        return HTTPBasicAuth(self.config.clarity_username, self.config.clarity_password)

    def obtener_ticket_por_codigo_directo(self, codigo_ticket: str) -> Optional[Dict]:
        """Buscar ticket específico por código usando filtro directo (MÁS EFICIENTE)"""
        print(f"   🔍 Buscando ticket {codigo_ticket} directamente en Clarity...")
        
        if not self.config.validar_configuracion_clarity():
            return None

        endpoint = "/tasks"
        url = self.config.clarity_domain + endpoint
        
        # Usar filtro directo para buscar por código - ¡MUCHO MÁS EFICIENTE!
        params = {
            "filter": f"(code = '{codigo_ticket}')",
            "limit": 1,
            "fields": "code,p_tdi_estado_freshdesk,_internalId,_parentId,name,status"
        }

        try:
            response = self.session.get(url, params=params, auth=self._get_auth())
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('_results', [])
                
                if tasks:
                    ticket = tasks[0]
                    print(f"   ✅ Ticket {codigo_ticket} encontrado directamente")
                    return ticket
                else:
                    print(f"   ❌ Ticket {codigo_ticket} no encontrado en Clarity")
                    return None
            else:
                print(f"   ❌ Error HTTP {response.status_code} buscando ticket: {response.text}")
                return None

        except Exception as e:
            print(f"   ❌ Error buscando ticket {codigo_ticket}: {str(e)}")
            return None

    # Mantener método existente para compatibilidad
    def buscar_ticket_por_codigo(self, codigo_ticket: str) -> Optional[Dict]:
        """Método legacy - usar obtener_ticket_por_codigo_directo en su lugar"""
        return self.obtener_ticket_por_codigo_directo(codigo_ticket)

    def obtener_todos_tickets_clarity(self) -> Dict[str, Dict]:
        """Obtener todos los tickets de Clarity (solo para casos necesarios)"""
        print("📥 Obteniendo todos los tickets de Clarity...")
        
        if not self.config.validar_configuracion_clarity():
            return {}

        todos_tickets = {}
        offset = 0
        limit = 100
        total_tickets = 0
        MAX_TICKETS = 5000  # Límite máximo por seguridad
        
        while True:
            endpoint = "/tasks"
            url = self.config.clarity_domain + endpoint
            
            params = {
                "limit": limit,
                "offset": offset,
                "fields": "code,p_tdi_estado_freshdesk,_internalId,_parentId,name,status"
            }

            try:
                response = self.session.get(url, params=params, auth=self._get_auth())
                
                if response.status_code == 200:
                    data = response.json()
                    tasks = data.get('_results', [])
                    
                    if not tasks:
                        break  # No hay más tickets
                    
                    # Contar tickets con código válido
                    tickets_con_codigo = 0
                    for ticket in tasks:
                        codigo = ticket.get('code')
                        if codigo:
                            todos_tickets[str(codigo)] = ticket
                            tickets_con_codigo += 1
                    
                    total_tickets += len(tasks)
                    print(f"📋 Offset {offset}: {len(tasks)} tickets recibidos, {tickets_con_codigo} con código")
                    
                    # Incrementar offset para la siguiente página
                    offset += len(tasks)
                    
                    # Verificar límites
                    if len(tasks) < limit:
                        break  # Última página
                    
                    if total_tickets >= MAX_TICKETS:
                        print(f"⚠️  Se alcanzó el límite máximo de {MAX_TICKETS} tickets")
                        break
                    
                    # Pequeña pausa para no saturar la API
                    time.sleep(0.1)
                    
                else:
                    print(f"❌ Error HTTP {response.status_code} obteniendo tickets Clarity: {response.text}")
                    break

            except Exception as e:
                print(f"❌ Error obteniendo tickets Clarity: {str(e)}")
                break

        print(f"✅ Obtenidos {total_tickets} tickets de Clarity en total")
        print(f"✅ {len(todos_tickets)} tickets con código válido para sincronización")
        return todos_tickets

    def actualizar_estado_ticket(self, investment_id: str, ticket_id: str, nuevo_estado: str) -> bool:
        """Actualizar estado de ticket en Clarity"""
        endpoint = f"/custTdiInvBacklogs/{investment_id}/tasks/{ticket_id}"
        url = self.config.clarity_domain + endpoint

        datos_actualizacion = {
            "p_tdi_estado_freshdesk": {
                "id": nuevo_estado,
                "displayValue": nuevo_estado
            }
        }

        try:
            # Intentar PATCH primero
            response = self.session.patch(url, json=datos_actualizacion, auth=self._get_auth())
            
            if response.status_code == 200:
                return True
            else:
                # Fallback a PUT
                response = self.session.put(url, json=datos_actualizacion, auth=self._get_auth())
                return response.status_code == 200
                
        except Exception as e:
            print(f"❌ Error actualizando ticket: {str(e)}")
            return False

    def verificar_estado_actual(self, codigo_ticket: str) -> Optional[str]:
        """Verificar el estado actual de un ticket en Clarity"""
        ticket = self.obtener_ticket_por_codigo_directo(codigo_ticket)
        if ticket:
            estado_field = ticket.get('p_tdi_estado_freshdesk', {})
            if isinstance(estado_field, dict) and 'displayValue' in estado_field:
                return estado_field['displayValue']
            return estado_field
        return None