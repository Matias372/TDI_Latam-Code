import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
from utils.api_utils import ApiUtils
from datetime import datetime, timedelta
from utils.logger import logger
import time

class FreshdeskService:
    def __init__(self, config_manager):
        self.config = config_manager
        logger.log_info("FreshdeskService inicializado")

    def obtener_tickets_paginados(self, pagina=1, por_pagina=100, updated_since=None):
        """Obtener tickets paginados con filtro opcional por fecha y manejo de errores"""
        # 🆕 MEJOR VALIDACIÓN - verificar que los datos existen en memoria
        if not self.config.validar_configuracion():
            return None

        # 🆕 VERIFICACIÓN EXPLÍCITA DE CREDENCIALES EN MEMORIA
        if not self.config.api_key or not self.config.freshdesk_domain:
            print("❌ Credenciales de Freshdesk no configuradas en memoria.")
            print("💡 Use 'Configurar conexión' para cargar los datos")
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
                # 🆕 LOG MÁS INFORMATIVO (sin mostrar credenciales)
                logger.log_debug(f"Consultando página {pagina} de Freshdesk...")
                
                response = requests.get(url, auth=auth, params=params, timeout=30)
                
                if response.status_code == 200:
                    tickets = response.json()
                    logger.log_debug(f"Página {pagina}: {len(tickets) if tickets else 0} tickets")
                    return tickets
                    
                elif response.status_code == 429:
                    wait_time = 60
                    print(f"⏳ Rate limit alcanzado. Esperando {wait_time} segundos...")
                    time.sleep(wait_time)
                    reintento += 1
                    
                elif response.status_code == 404:
                    print(f"❌ Página {pagina} no encontrada. Posiblemente no hay más tickets.")
                    return []
                    
                else:
                    # 🆕 MEJOR MANEJO DE ERRORES DE AUTENTICACIÓN
                    if response.status_code == 401:
                        print("❌ Error de autenticación en Freshdesk. Verifique la API Key.")
                        # 🆕 LIMPIAR CREDENCIALES INVÁLIDAS
                        self.config.clear_sensitive_data()
                    else:
                        print(f"❌ Error {response.status_code} al obtener página {pagina}: {response.text}")
                    
                    if reintento < max_reintentos - 1:
                        wait_time = 5 * (reintento + 1)
                        print(f"⏳ Reintentando en {wait_time} segundos...")
                        time.sleep(wait_time)
                        reintento += 1
                    else:
                        return None
                        
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout en página {pagina}. Reintentando...")
                if reintento < max_reintentos - 1:
                    time.sleep(10)
                    reintento += 1
                else:
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"🔌 Error de conexión en página {pagina}: {e}")
                if reintento < max_reintentos - 1:
                    time.sleep(10)
                    reintento += 1
                else:
                    return None
        
        return None

    def obtener_todos_tickets_freshdesk(self, updated_since=None):
        """Obtener todos los tickets de Freshdesk (con paginación)"""
        # 🆕 VERIFICACIÓN INICIAL EXPLÍCITA
        if not self.config.validar_configuracion():
            return []

        logger.log_info("Obteniendo tickets de Freshdesk...", "📥 Obteniendo tickets de Freshdesk...")
        todos_tickets = []
        pagina = 1
        
        while True:
            tickets = self.obtener_tickets_paginados(pagina=pagina, por_pagina=100, updated_since=updated_since)
            
            if tickets is None:  # Error grave
                print("❌ Error crítico al obtener tickets. Deteniendo paginación.")
                break
                
            if not tickets:  # Lista vacía - fin de paginación
                break
                
            todos_tickets.extend(tickets)
            logger.log_info(f"Página {pagina}: {len(tickets)} tickets obtenidos")
            pagina += 1
            
            # Pausa ocasional para evitar rate limiting
            if pagina % 10 == 0:
                time.sleep(2)
            
            # Límite de seguridad
            if pagina > 1000:
                print("⚠️  Límite de seguridad alcanzado (1000 páginas)")
                break
        
        logger.log_info(f"Obtenidos {len(todos_tickets)} tickets de Freshdesk", f"✅ Obtenidos {len(todos_tickets)} tickets de Freshdesk")
        return todos_tickets

    def obtener_empresas(self):
        """Obtener lista de empresas"""
        # 🆕 VERIFICACIÓN MEJORADA
        if not self.config.validar_configuracion():
            return None

        # 🆕 VERIFICACIÓN EXPLÍCITA ADICIONAL
        if not self.config.api_key:
            print("❌ API Key no configurada en memoria.")
            return None

        empresas = []
        pagina = 1

        while True:
            url = f"{self.config.freshdesk_domain}/api/v2/companies"
            auth = HTTPBasicAuth(self.config.api_key, "X")
            params = {"page": pagina}

            try:
                # 🆕 AGREGAR TIMEOUT Y MEJOR MANEJO DE ERRORES
                response = requests.get(url, auth=auth, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if not data:
                        break
                    empresas.extend(data)
                    pagina += 1
                elif response.status_code == 403:
                    print("⛔ No tienes permisos para ver empresas.")
                    break
                elif response.status_code == 401:
                    print("❌ Error de autenticación. Verifique la API Key.")
                    # 🆕 LIMPIAR CREDENCIALES INVÁLIDAS
                    self.config.clear_sensitive_data()
                    break
                else:
                    print(f"❌ Error {response.status_code}: {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                print("⏰ Timeout al obtener empresas.")
                break
            except requests.exceptions.RequestException as e:
                print(f"🔌 Error de conexión: {e}")
                break

        return empresas