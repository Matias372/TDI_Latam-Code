import requests
from requests.auth import HTTPBasicAuth
import urllib3
import time
from typing import Dict, Optional, List
from utils.logging import logger
from utils.display_utils import display

#  COMENTADO POR SEGURIDAD
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ClarityService:
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = requests.Session()
        self.session.verify = True  #  SEGURIDAD HABILITADA
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def _get_auth(self):
        """Obtener autenticación Basic Auth"""
        if not self.config.clarity_username or not self.config.clarity_password:
            logger.log_error("Credenciales de Clarity no disponibles en memoria")
            return None
        return HTTPBasicAuth(self.config.clarity_username, self.config.clarity_password)

    def obtener_ticket_por_codigo_directo(self, codigo_ticket: str) -> Optional[Dict]:
        """Buscar ticket específico - INTERFAZ LIMPIA"""
        logger.log_debug(f"Buscando ticket {codigo_ticket} directamente en Clarity...")
        
        #  VERIFICACIÓN MEJORADA DE CONFIGURACIÓN
        if not self.config.validar_configuracion_clarity():
            return None

        if not self.config.clarity_username or not self.config.clarity_password:
            display.show_message("Credenciales de Clarity no configuradas en memoria", "error")
            return None

        endpoint = "/tasks"
        url = self.config.clarity_domain + endpoint
        
        params = {
            "filter": f"(code = '{codigo_ticket}')",
            "limit": 1,
            "fields": "code,p_tdi_estado_freshdesk,_internalId,_parentId,name,status"
        }

        try:
            auth = self._get_auth()
            if auth is None:
                return None
                
            response = self.session.get(url, params=params, auth=auth, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('_results', [])
                
                if tasks:
                    ticket = tasks[0]
                    logger.log_info(f"Ticket {codigo_ticket} encontrado directamente")
                    display.show_message(f"Ticket {codigo_ticket} encontrado", "success")
                    return ticket
                else:
                    logger.log_warning(f"Ticket {codigo_ticket} no encontrado en Clarity")
                    display.show_message(f"Ticket {codigo_ticket} no encontrado en Clarity", "warning")
                    return None
            else:
                #  MANEJO MEJORADO DE ERRORES
                if response.status_code == 401:
                    display.show_message("Error de autenticación en Clarity. Verifique usuario y contraseña", "error")
                    self.config.clear_sensitive_data()
                else:
                    display.show_message(f"Error HTTP {response.status_code} buscando ticket", "error")
                    logger.log_error(f"Error detallado: {response.text}")
                return None

        except requests.exceptions.Timeout:
            display.show_message(f"Timeout al buscar ticket {codigo_ticket} en Clarity", "error")
            return None
        except Exception as e:
            logger.log_error(f"Error buscando ticket {codigo_ticket}: {str(e)}")
            display.show_message(f"Error buscando ticket: {str(e)}", "error")
            return None

    def obtener_todos_tickets_clarity(self) -> Dict[str, Dict]:
        """Obtener todos los tickets de Clarity - INTERFAZ LIMPIA"""
        display.show_message("Obteniendo todos los tickets de Clarity...", "info")
        
        #  VERIFICACIÓN MEJORADA
        if not self.config.validar_configuracion_clarity():
            return {}

        if not self.config.clarity_username or not self.config.clarity_password:
            display.show_message("Credenciales de Clarity no configuradas en memoria", "error")
            return {}

        todos_tickets = {}
        offset = 0
        limit = 100
        total_tickets = 0
        MAX_TICKETS = 5000
        
        #  BARRA DE PROGRESO PARA OPERACIÓN LARGA
        display.show_message("Esta operación puede tomar varios minutos...", "warning")
        
        while True:
            endpoint = "/tasks"
            url = self.config.clarity_domain + endpoint
            
            params = {
                "limit": limit,
                "offset": offset,
                "fields": "code,p_tdi_estado_freshdesk,_internalId,_parentId,name,status"
            }

            try:
                auth = self._get_auth()
                if auth is None:
                    break

                response = self.session.get(url, params=params, auth=auth, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    tasks = data.get('_results', [])
                    
                    if not tasks:
                        break
                    
                    tickets_con_codigo = 0
                    for ticket in tasks:
                        codigo = ticket.get('code')
                        if codigo:
                            todos_tickets[str(codigo)] = ticket
                            tickets_con_codigo += 1
                    
                    total_tickets += len(tasks)
                    
                    #  ACTUALIZAR PROGRESO
                    if offset % 500 == 0:  # Mostrar cada 500 tickets
                        display.show_message(f"Procesados {total_tickets} tickets...", "info")
                    
                    offset += len(tasks)
                    
                    if len(tasks) < limit:
                        break
                    
                    if total_tickets >= MAX_TICKETS:
                        display.show_message(f"Límite máximo de {MAX_TICKETS} tickets alcanzado", "warning")
                        break
                    
                    time.sleep(0.1)
                    
                else:
                    if response.status_code == 401:
                        display.show_message("Error de autenticación en Clarity. Verifique usuario y contraseña", "error")
                        self.config.clear_sensitive_data()
                        break
                    else:
                        display.show_message(f"Error HTTP {response.status_code} obteniendo tickets Clarity", "error")
                        logger.log_error(f"Error detallado: {response.text}")
                        break

            except requests.exceptions.Timeout:
                display.show_message("Timeout al obtener tickets de Clarity", "error")
                break
            except Exception as e:
                display.show_message(f"Error obteniendo tickets Clarity: {str(e)}", "error")
                break

        display.show_message(f"Obtenidos {total_tickets} tickets de Clarity en total", "success")
        display.show_message(f"{len(todos_tickets)} tickets con código válido para sincronización", "success")
        return todos_tickets

    def actualizar_estado_ticket(self, investment_id: str, ticket_id: str, nuevo_estado: str) -> bool:
        """Actualizar estado de ticket en Clarity - INTERFAZ LIMPIA"""
        if not self.config.validar_configuracion_clarity():
            return False

        if not self.config.clarity_username or not self.config.clarity_password:
            display.show_message("Credenciales de Clarity no configuradas en memoria", "error")
            return False

        endpoint = f"/custTdiInvBacklogs/{investment_id}/tasks/{ticket_id}"
        url = self.config.clarity_domain + endpoint

        datos_actualizacion = {
            "p_tdi_estado_freshdesk": {
                "id": nuevo_estado,
                "displayValue": nuevo_estado
            }
        }

        try:
            auth = self._get_auth()
            if auth is None:
                return False

            # Intentar PATCH primero
            response = self.session.patch(url, json=datos_actualizacion, auth=auth, timeout=30)
            
            if response.status_code == 200:
                display.show_message(f"Ticket {ticket_id} actualizado exitosamente", "success")
                return True
            else:
                # Fallback a PUT
                response = self.session.put(url, json=datos_actualizacion, auth=auth, timeout=30)
                if response.status_code == 200:
                    display.show_message(f"Ticket {ticket_id} actualizado exitosamente (vía PUT)", "success")
                    return True
                else:
                    display.show_message(f"Error actualizando ticket {ticket_id}: HTTP {response.status_code}", "error")
                    return False
                
        except requests.exceptions.Timeout:
            display.show_message(f"Timeout al actualizar ticket {ticket_id} en Clarity", "error")
            return False
        except Exception as e:
            display.show_message(f"Error actualizando ticket {ticket_id}: {str(e)}", "error")
            return False

    def verificar_estado_actual(self, codigo_ticket: str) -> Optional[str]:
        """Verificar el estado actual de un ticket en Clarity"""
        display.show_message(f"Verificando estado actual del ticket {codigo_ticket}...", "info")
        ticket = self.obtener_ticket_por_codigo_directo(codigo_ticket)
        if ticket:
            estado_field = ticket.get('p_tdi_estado_freshdesk', {})
            if isinstance(estado_field, dict) and 'displayValue' in estado_field:
                display.show_message(f"Estado actual: {estado_field['displayValue']}", "success")
                return estado_field['displayValue']
            display.show_message("Estado actual: No disponible", "warning")
            return estado_field
        return None

    def verificar_conexion(self):
        """Verificar conexión a Clarity - INTERFAZ LIMPIA"""
        display.show_message("Verificando conexión a Clarity...", "info")
        
        if not self.config.validar_configuracion_clarity():
            return False, "Configuración incompleta en memoria"

        try:
            url = self.config.clarity_domain + "/tasks"
            auth = self._get_auth()
            if auth is None:
                return False, "Credenciales no configuradas"

            params = {
                "limit": 1,
                "fields": "code"
            }

            response = self.session.get(url, params=params, auth=auth, timeout=10)
            
            if response.status_code == 200:
                return True, " Conexión exitosa a Clarity"
            elif response.status_code == 401:
                return False, " Error de autenticación - Usuario o contraseña inválidos"
            elif response.status_code == 403:
                return False, " Acceso denegado - verifique permisos"
            else:
                return False, f" Error {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return False, " Timeout - verifique la conexión a internet y el dominio de Clarity"
        except requests.exceptions.ConnectionError:
            return False, " Error de conexión - verifique el dominio de Clarity"
        except Exception as e:
            return False, f" Error inesperado: {str(e)}"