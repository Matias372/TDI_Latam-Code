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

    def buscar_ticket_por_codigo(self, codigo_ticket: str) -> Optional[Dict]:
        """Buscar ticket en Clarity por código (ID de Freshdesk)"""
        if not self.config.validar_configuracion_clarity():
            return None

        endpoint = "/tasks"
        url = self.config.clarity_domain + endpoint
        
        params = {
            "filter": f"(code = '{codigo_ticket}')",
            "limit": 1,
            "fields": "_internalId,_parentId,code,name,p_tdi_estado_freshdesk,status"
        }

        try:
            response = self.session.get(url, params=params, auth=self._get_auth())
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('_results', [])
                return tasks[0] if tasks else None
            else:
                print(f"❌ Error HTTP {response.status_code} buscando ticket {codigo_ticket}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error buscando ticket {codigo_ticket}: {str(e)}")
            return None

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
        ticket = self.buscar_ticket_por_codigo(codigo_ticket)
        if ticket:
            estado_field = ticket.get('p_tdi_estado_freshdesk', {})
            if isinstance(estado_field, dict) and 'displayValue' in estado_field:
                return estado_field['displayValue']
            return estado_field
        return None