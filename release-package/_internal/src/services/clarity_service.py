import requests
from requests.auth import HTTPBasicAuth
import urllib3
import time
from typing import Dict, Optional, List
from utils.logger import logger

# 🚨 ELIMINAR O COMENTAR ESTA LÍNEA - ES UN RIESGO DE SEGURIDAD
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ClarityService:
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = requests.Session()
        # 🆕 HABILITAR SSL VERIFICATION - CRÍTICO PARA SEGURIDAD
        self.session.verify = True  # Cambiar de False a True
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def _get_auth(self):
        """Obtener autenticación Basic Auth"""
        # 🆕 VERIFICAR QUE LAS CREDENCIALES ESTÁN EN MEMORIA
        if not self.config.clarity_username or not self.config.clarity_password:
            logger.log_error("Credenciales de Clarity no disponibles en memoria")
            return None
        return HTTPBasicAuth(self.config.clarity_username, self.config.clarity_password)

    def obtener_ticket_por_codigo_directo(self, codigo_ticket: str) -> Optional[Dict]:
        """Buscar ticket específico por código usando filtro directo"""
        logger.log_debug(f"Buscando ticket {codigo_ticket} directamente en Clarity...")
        
        # 🆕 VERIFICACIÓN MEJORADA DE CONFIGURACIÓN
        if not self.config.validar_configuracion_clarity():
            return None

        # 🆕 VERIFICACIÓN EXPLÍCITA DE CREDENCIALES EN MEMORIA
        if not self.config.clarity_username or not self.config.clarity_password:
            print("❌ Credenciales de Clarity no configuradas en memoria.")
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
                
            # 🆕 AGREGAR TIMEOUT
            response = self.session.get(url, params=params, auth=auth, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('_results', [])
                
                if tasks:
                    ticket = tasks[0]
                    logger.log_info(f"Ticket {codigo_ticket} encontrado directamente", f"✅ Ticket {codigo_ticket} encontrado")
                    return ticket
                else:
                    logger.log_warning(f"Ticket {codigo_ticket} no encontrado en Clarity")
                    return None
            else:
                # 🆕 MEJOR MANEJO DE ERRORES DE AUTENTICACIÓN
                if response.status_code == 401:
                    print("❌ Error de autenticación en Clarity. Verifique usuario y contraseña.")
                    # 🆕 LIMPIAR CREDENCIALES INVÁLIDAS
                    self.config.clear_sensitive_data()
                else:
                    logger.log_error(f"Error HTTP {response.status_code} buscando ticket: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print(f"⏰ Timeout al buscar ticket {codigo_ticket} en Clarity.")
            return None
        except Exception as e:
            logger.log_error(f"Error buscando ticket {codigo_ticket}: {str(e)}")
            return None

    def obtener_todos_tickets_clarity(self) -> Dict[str, Dict]:
        """Obtener todos los tickets de Clarity (solo para casos necesarios)"""
        print("📥 Obteniendo todos los tickets de Clarity...")
        
        # 🆕 VERIFICACIÓN MEJORADA
        if not self.config.validar_configuracion_clarity():
            return {}

        # 🆕 VERIFICACIÓN EXPLÍCITA ADICIONAL
        if not self.config.clarity_username or not self.config.clarity_password:
            print("❌ Credenciales de Clarity no configuradas en memoria.")
            return {}

        todos_tickets = {}
        offset = 0
        limit = 100
        total_tickets = 0
        MAX_TICKETS = 5000
        
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

                # 🆕 AGREGAR TIMEOUT
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
                    print(f"📋 Offset {offset}: {len(tasks)} tickets recibidos, {tickets_con_codigo} con código")
                    
                    offset += len(tasks)
                    
                    if len(tasks) < limit:
                        break
                    
                    if total_tickets >= MAX_TICKETS:
                        print(f"⚠️  Se alcanzó el límite máximo de {MAX_TICKETS} tickets")
                        break
                    
                    time.sleep(0.1)
                    
                else:
                    # 🆕 MEJOR MANEJO DE ERRORES
                    if response.status_code == 401:
                        print("❌ Error de autenticación en Clarity. Verifique usuario y contraseña.")
                        self.config.clear_sensitive_data()
                        break
                    else:
                        print(f"❌ Error HTTP {response.status_code} obteniendo tickets Clarity: {response.text}")
                        break

            except requests.exceptions.Timeout:
                print("⏰ Timeout al obtener tickets de Clarity.")
                break
            except Exception as e:
                print(f"❌ Error obteniendo tickets Clarity: {str(e)}")
                break

        print(f"✅ Obtenidos {total_tickets} tickets de Clarity en total")
        print(f"✅ {len(todos_tickets)} tickets con código válido para sincronización")
        return todos_tickets

    def actualizar_estado_ticket(self, investment_id: str, ticket_id: str, nuevo_estado: str) -> bool:
        """Actualizar estado de ticket en Clarity"""
        # 🆕 VERIFICACIÓN MEJORADA
        if not self.config.validar_configuracion_clarity():
            return False

        # 🆕 VERIFICACIÓN EXPLÍCITA
        if not self.config.clarity_username or not self.config.clarity_password:
            print("❌ Credenciales de Clarity no configuradas en memoria.")
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

            # 🆕 AGREGAR TIMEOUTS
            # Intentar PATCH primero
            response = self.session.patch(url, json=datos_actualizacion, auth=auth, timeout=30)
            
            if response.status_code == 200:
                return True
            else:
                # Fallback a PUT
                response = self.session.put(url, json=datos_actualizacion, auth=auth, timeout=30)
                return response.status_code == 200
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout al actualizar ticket {ticket_id} en Clarity.")
            return False
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

    # 🆕 AGREGAR MÉTODO DE VERIFICACIÓN DE CONEXIÓN
    def verificar_conexion(self):
        """Verificar que la conexión a Clarity funciona con las credenciales actuales"""
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
                return True, "✅ Conexión exitosa a Clarity"
            elif response.status_code == 401:
                return False, "❌ Error de autenticación - Usuario o contraseña inválidos"
            elif response.status_code == 403:
                return False, "❌ Acceso denegado - verifique permisos"
            else:
                return False, f"❌ Error {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "⏰ Timeout - verifique la conexión a internet y el dominio de Clarity"
        except requests.exceptions.ConnectionError:
            return False, "🔌 Error de conexión - verifique el dominio de Clarity"
        except Exception as e:
            return False, f"❌ Error inesperado: {str(e)}"