import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
from utils.api_utils import ApiUtils
from datetime import datetime, timedelta
from utils.logging import logger
from utils.display_utils import display
import time

class FreshdeskService:
    def __init__(self, config_manager):
        self.config = config_manager
        logger.log_info("FreshdeskService inicializado")

    def obtener_tickets_paginados(self, pagina=1, por_pagina=100, updated_since=None):
        """Obtener tickets paginados - INTERFAZ LIMPIA"""
        #  VERIFICACIÓN CON DISPLAYUTILS
        if not self.config.validar_configuracion():
            return None

        if not self.config.api_key or not self.config.freshdesk_domain:
            display.show_message("Credenciales de Freshdesk no configuradas en memoria", "error")
            display.show_message("Use 'Configurar conexión' para cargar los datos", "info")
            return None

        url = f"{self.config.freshdesk_domain}/api/v2/tickets"
        auth = HTTPBasicAuth(self.config.api_key, "X")
        params = {
            "page": pagina, 
            "per_page": por_pagina,
            "order_by": "created_at",
            "order_type": "asc"
        }
        
        if updated_since:
            params["updated_since"] = updated_since
        
        max_reintentos = 3
        reintento = 0
        
        while reintento < max_reintentos:
            try:
                logger.log_debug(f"Consultando página {pagina} de Freshdesk...")
                
                response = requests.get(url, auth=auth, params=params, timeout=30)
                
                if response.status_code == 200:
                    tickets = response.json()
                    logger.log_debug(f"Página {pagina}: {len(tickets) if tickets else 0} tickets")
                    return tickets
                    
                elif response.status_code == 429:
                    wait_time = 60
                    display.show_message(f"Rate limit alcanzado. Esperando {wait_time} segundos...", "warning")
                    time.sleep(wait_time)
                    reintento += 1
                    
                elif response.status_code == 404:
                    display.show_message(f"Página {pagina} no encontrada. Posiblemente no hay más tickets", "warning")
                    return []
                    
                else:
                    #  MANEJO DE ERRORES CON DISPLAYUTILS
                    if response.status_code == 401:
                        display.show_message("Error de autenticación en Freshdesk. Verifique la API Key", "error")
                        self.config.clear_sensitive_data()
                    else:
                        display.show_message(f"Error {response.status_code} al obtener página {pagina}", "error")
                        logger.log_error(f"Error detallado: {response.text}")
                    
                    if reintento < max_reintentos - 1:
                        wait_time = 5 * (reintento + 1)
                        display.show_message(f"Reintentando en {wait_time} segundos...", "warning")
                        time.sleep(wait_time)
                        reintento += 1
                    else:
                        return None
                        
            except requests.exceptions.Timeout:
                display.show_message(f"Timeout en página {pagina}. Reintentando...", "warning")
                if reintento < max_reintentos - 1:
                    time.sleep(10)
                    reintento += 1
                else:
                    return None
                    
            except requests.exceptions.RequestException as e:
                display.show_message(f"Error de conexión en página {pagina}: {e}", "error")
                if reintento < max_reintentos - 1:
                    time.sleep(10)
                    reintento += 1
                else:
                    return None
        
        return None

    def obtener_todos_tickets_freshdesk(self, updated_since=None):
        """Obtener todos los tickets de Freshdesk - INTERFAZ LIMPIA"""
        if not self.config.validar_configuracion():
            return []

        display.show_message("Obteniendo tickets de Freshdesk...", "info")
        logger.log_info("Obteniendo tickets de Freshdesk...")
        
        todos_tickets = []
        pagina = 1
        
        while True:
            #  MOSTRAR PROGRESO DE PAGINACIÓN
            if pagina % 10 == 0 or pagina == 1:
                display.show_message(f"Procesando página {pagina}...", "info")
            
            tickets = self.obtener_tickets_paginados(pagina=pagina, por_pagina=100, updated_since=updated_since)
            
            if tickets is None:
                display.show_message("Error crítico al obtener tickets. Deteniendo paginación", "error")
                break
                
            if not tickets:
                display.show_message("No hay más tickets por obtener", "success")
                break
                
            todos_tickets.extend(tickets)
            logger.log_info(f"Página {pagina}: {len(tickets)} tickets obtenidos")
            pagina += 1
            
            # Pausa ocasional para evitar rate limiting
            if pagina % 10 == 0:
                time.sleep(2)
            
            # Límite de seguridad
            if pagina > 1000:
                display.show_message("Límite de seguridad alcanzado (1000 páginas)", "warning")
                break
        
        display.show_message(f"Obtenidos {len(todos_tickets)} tickets de Freshdesk", "success")
        logger.log_info(f"Obtenidos {len(todos_tickets)} tickets de Freshdesk")
        return todos_tickets

    def obtener_empresas(self):
        """Obtener lista de empresas - INTERFAZ LIMPIA"""
        if not self.config.validar_configuracion():
            return None

        if not self.config.api_key:
            display.show_message("API Key no configurada en memoria", "error")
            return None

        display.show_message("Obteniendo lista de empresas...", "info")
        empresas = []
        pagina = 1

        while True:
            url = f"{self.config.freshdesk_domain}/api/v2/companies"
            auth = HTTPBasicAuth(self.config.api_key, "X")
            params = {"page": pagina}

            try:
                response = requests.get(url, auth=auth, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        break
                    empresas.extend(data)
                    pagina += 1
                    
                    #  MOSTRAR PROGRESO
                    if len(empresas) % 50 == 0:
                        display.show_message(f"Obtenidas {len(empresas)} empresas...", "info")
                        
                elif response.status_code == 403:
                    display.show_message("No tiene permisos para ver empresas", "error")
                    break
                elif response.status_code == 401:
                    display.show_message("Error de autenticación. Verifique la API Key", "error")
                    self.config.clear_sensitive_data()
                    break
                else:
                    display.show_message(f"Error {response.status_code} al obtener empresas", "error")
                    logger.log_error(f"Error detallado: {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                display.show_message("Timeout al obtener empresas", "error")
                break
            except requests.exceptions.RequestException as e:
                display.show_message(f"Error de conexión: {e}", "error")
                break

        display.show_message(f"Obtenidas {len(empresas)} empresas", "success")
        return empresas