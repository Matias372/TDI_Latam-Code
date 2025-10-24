# src/features/freshdesk_updater.py
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import time
from typing import Dict, List, Optional, Tuple
import json
from utils.file_utils import FileUtils
from utils.display_utils import display
from utils.logging import logger
# O para funcionalidades específicas:
from utils.logging import logger, TransactionLogger

class FreshdeskDirectUpdater:
    def __init__(self, freshdesk_domain: str, api_key: str):
        if not freshdesk_domain.startswith(('http://', 'https://')):
            self.freshdesk_domain = f"https://{freshdesk_domain}.freshdesk.com"
        else:
            self.freshdesk_domain = freshdesk_domain.rstrip('/')
        
        self.api_key = api_key
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(api_key, 'X')
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        self.custom_fields_mapping = {
            'Segmento': 'cf_bmc',
            'Fabricante': 'cf_itsm', 
            'Producto': 'cf_remedy'
        }
        
        self.grupos_excluidos = ['TRIAGE CHILE', 'SOPORTE N0']
        self.ticket_cache = {}
        self.grupo_cache = {}
        
    def safe_request(self, method: str, url: str, **kwargs) -> Tuple[requests.Response, str]:
        """Realizar petición con reintentos - solo log interno"""
        max_retries = 3
        wait_seconds = 2
        
        for attempt in range(max_retries):
            try:
                # Solo log interno - no mostrar en consola
                logger.logger.debug(f"Request {method} a {url}")
                
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 429:
                    logger.logger.warning(f"Rate limit. Reintento {attempt + 1}/{max_retries}")
                    time.sleep(wait_seconds)
                    wait_seconds *= 2
                else:
                    return response, "OK"
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Error de conexión (intento {attempt + 1}): {e}"
                logger.logger.error(error_msg)
                if attempt == max_retries - 1:
                    return None, error_msg
                time.sleep(wait_seconds)
        
        return response, "Max retries reached"

    def obtener_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Obtener ticket de Freshdesk - solo log interno"""
        if ticket_id in self.ticket_cache:
            return self.ticket_cache[ticket_id]
            
        url = f"{self.freshdesk_domain}/api/v2/tickets/{ticket_id}"
        
        try:
            response, msg = self.safe_request('GET', url)
            
            if response and response.status_code == 200:
                ticket_data = response.json()
                self.ticket_cache[ticket_id] = ticket_data
                logger.logger.debug(f"Ticket {ticket_id} obtenido exitosamente")
                return ticket_data
            elif response and response.status_code == 404:
                logger.logger.debug(f"Ticket {ticket_id} no encontrado")
                return None
            else:
                error_msg = f"Error HTTP {response.status_code if response else 'N/A'}: {msg}"
                logger.logger.error(f"Error al obtener ticket {ticket_id}: {error_msg}")
                return None
                
        except Exception as e:
            logger.logger.error(f"Excepción al obtener ticket {ticket_id}: {str(e)}")
            return None

    def obtener_nombre_grupo(self, group_id: int) -> str:
        """Obtener nombre del grupo - solo log interno"""
        if not group_id:
            return "Sin grupo"
        
        if group_id in self.grupo_cache:
            return self.grupo_cache[group_id]
            
        url = f"{self.freshdesk_domain}/api/v2/groups/{group_id}"
        
        try:
            response, msg = self.safe_request('GET', url)
            if response and response.status_code == 200:
                grupo_data = response.json()
                nombre_grupo = grupo_data.get('name', f'Grupo ID: {group_id}')
                self.grupo_cache[group_id] = nombre_grupo
                return nombre_grupo
            else:
                return f"Grupo ID: {group_id}"
        except Exception as e:
            logger.logger.error(f"Error al obtener grupo {group_id}: {e}")
            return f"Grupo ID: {group_id}"

    def tiene_etiquetas_clarity(self, ticket_data: Dict) -> bool:
        """Verificar si el ticket ya tiene etiquetas CREATE/UPDATE CLARITY"""
        tags = ticket_data.get('tags', [])
        if not tags:
            return False
            
        clarity_tags = {'CREATE CLARITY', 'UPDATE CLARITY'}
        ticket_tags = {tag.upper() for tag in tags if tag}
        
        return bool(clarity_tags.intersection(ticket_tags))

    def verificar_condiciones_ticket(self, ticket_data: Dict) -> Tuple[bool, str, Dict]:
        """Verificar condiciones en Freshdesk - solo log interno"""
        datos_ticket = {
            'group_id': ticket_data.get('group_id'),
            'responder_id': ticket_data.get('responder_id'),
            'custom_fields': ticket_data.get('custom_fields', {})
        }
        
        # 1. Verificar si ya tiene etiquetas CLARITY
        if self.tiene_etiquetas_clarity(ticket_data):
            return False, "ya tiene etiquetas CLARITY", datos_ticket
        
        # 2. Verificar si tiene grupo
        if not datos_ticket['group_id']:
            return False, "sin grupo", datos_ticket
        
        # 3. Verificar si tiene agente
        if not datos_ticket['responder_id']:
            return False, "sin agente", datos_ticket
        
        # 4. Obtener nombre del grupo y verificar si está excluido
        nombre_grupo = self.obtener_nombre_grupo(datos_ticket['group_id'])
        datos_ticket['nombre_grupo'] = nombre_grupo
        
        if nombre_grupo in self.grupos_excluidos:
            return False, f"grupo excluido: {nombre_grupo}", datos_ticket
        
        return True, "ok", datos_ticket

    def establecer_campos_null(self, ticket_id: str) -> Tuple[bool, str]:
        """Establecer campos a NULL - solo log interno"""
        payload = {
            'custom_fields': {
                'cf_bmc': None,
                'cf_itsm': None,
                'cf_remedy': None
            }
        }
        
        url = f"{self.freshdesk_domain}/api/v2/tickets/{ticket_id}"
        
        try:
            response, msg = self.safe_request('PUT', url, json=payload)
            
            if response is None:
                return False, f"No hubo respuesta del servidor: {msg}"
            
            if response.status_code == 200:
                if ticket_id in self.ticket_cache:
                    del self.ticket_cache[ticket_id]
                logger.logger.debug(f"Campos establecidos a NULL para ticket {ticket_id}")
                return True, "Campos establecidos a NULL"
            else:
                error_msg = f"Error HTTP {response.status_code}: {response.text}"
                logger.logger.error(f"Error al establecer NULL para ticket {ticket_id}: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Excepción durante establecimiento a NULL: {str(e)}"
            logger.logger.error(f"Error en ticket {ticket_id}: {error_msg}")
            return False, error_msg

    def restaurar_campos_originales(self, ticket_id: str, valores_excel: Dict) -> Tuple[bool, str]:
        """Restaurar campos desde Excel - solo log interno"""
        payload = {
            'custom_fields': {
                'cf_bmc': valores_excel['Segmento'],
                'cf_itsm': valores_excel['Fabricante'],
                'cf_remedy': valores_excel['Producto']
            }
        }
        
        url = f"{self.freshdesk_domain}/api/v2/tickets/{ticket_id}"
        
        try:
            response, msg = self.safe_request('PUT', url, json=payload)
            
            if response is None:
                return False, f"No hubo respuesta del servidor: {msg}"
            
            if response.status_code == 200:
                if ticket_id in self.ticket_cache:
                    del self.ticket_cache[ticket_id]
                logger.logger.debug(f"Campos restaurados para ticket {ticket_id}")
                return True, "Campos restaurados correctamente"
            else:
                error_msg = f"Error HTTP {response.status_code}: {response.text}"
                logger.logger.error(f"Error al restaurar campos para ticket {ticket_id}: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Excepción durante restauración: {str(e)}"
            logger.logger.error(f"Error en ticket {ticket_id}: {error_msg}")
            return False, error_msg

    def actualizar_campos_con_estrategia_null(self, ticket_id: str, valores_excel: Dict) -> Tuple[bool, str]:
        """Estrategia comprobada: NULL -> Restauración - solo log interno"""
        logger.logger.info(f"Iniciando actualización en 2 pasos para ticket {ticket_id}")
        
        # PASO 1: Establecer campos a NULL
        exito_null, mensaje_null = self.establecer_campos_null(ticket_id)
        if not exito_null:
            return False, f"Error en paso 1 (NULL): {mensaje_null}"
        
        # Pausa entre operaciones
        time.sleep(2)
        
        # PASO 2: Restaurar valores desde Excel
        exito_restore, mensaje_restore = self.restaurar_campos_originales(ticket_id, valores_excel)
        if not exito_restore:
            return False, f"Error en paso 2 (Restauración): {mensaje_restore}"
        
        logger.logger.info(f"Actualización completa exitosa para ticket {ticket_id}")
        return True, "Actualización completa exitosa"

    def procesar_actualizacion_etiquetas(self):
        """Proceso automático para forzar regeneración de etiquetas CREATE CLARITY"""
        display.clear_screen()
        print("\n╔══════════════════════════════════════════════╗")
        print("║           🏷️ REGENERAR ETIQUETAS             ║")
        print("╚══════════════════════════════════════════════╝")
        
        print("🚀 INICIANDO PROCESO AUTOMÁTICO")
        print("=" * 50)
        print("📋 Buscando tickets sin etiquetas CLARITY...")
        print("=" * 50)
        
        # Seleccionar archivo Excel
        ruta_archivo = FileUtils.seleccionar_archivo(
            "Seleccione archivo Excel", 
            [("Excel files", "*.xlsx *.xls")]
        )
        
        if not ruta_archivo:
            print("❌ No se seleccionó ningún archivo.")
            display.press_enter_to_continue()
            return
        
        try:
            df = pd.read_excel(ruta_archivo)
            print(f"📊 Archivo cargado: {len(df)} tickets")
        except Exception as e:
            print(f"❌ Error al cargar archivo: {e}")
            display.press_enter_to_continue()
            return
        
        # Verificar columnas requeridas
        columnas_requeridas = ['Ticket ID', 'Segmento', 'Fabricante', 'Producto']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            print(f"❌ Columnas faltantes: {columnas_faltantes}")
            display.press_enter_to_continue()
            return
        
        # Contadores y listas para detalle
        tickets_actualizados = 0
        tickets_salteados = 0
        tickets_error = 0
        total_tickets = len(df)
        
        # Listas para almacenar detalles
        tickets_con_error = []  # Lista de diccionarios con ticket_id y error
        tickets_salteados_detalle = []  # Lista de diccionarios con ticket_id y motivo
        
        print(f"\n🔄 Procesando {total_tickets} tickets...")
        print("💡 Modo automático - todos los tickets válidos se actualizarán\n")
        
        try:
            for index, fila in df.iterrows():
                ticket_id = str(fila['Ticket ID'])
                current = index + 1
                
                # Estado actual para mostrar
                estado = f"✅:{tickets_actualizados} ⏭️:{tickets_salteados} ❌:{tickets_error}"
                
                # Mostrar cabecera del ticket actual
                display.clear_line()
                print(f"\r🔄 Procesando: Ticket #{ticket_id} [{current}/{total_tickets}] {estado}")
                
                # 1. Verificar campos en Excel
                valores_excel = {
                    'Segmento': fila['Segmento'],
                    'Fabricante': fila['Fabricante'],
                    'Producto': fila['Producto']
                }
                
                # Verificar campos vacíos
                campos_vacios = [campo for campo, valor in valores_excel.items() 
                            if pd.isna(valor) or str(valor).strip() == '']
                if campos_vacios:
                    motivo = f"campos vacíos en Excel: {', '.join(campos_vacios)}"
                    # Solo log interno
                    logger.logger.debug(f"Ticket {ticket_id} excluido: {motivo}")
                    tickets_salteados += 1
                    tickets_salteados_detalle.append({'ticket_id': ticket_id, 'motivo': motivo})
                    continue
                
                # 2. Obtener ticket desde Freshdesk
                ticket_data = self.obtener_ticket(ticket_id)
                if not ticket_data:
                    motivo = "no encontrado en Freshdesk"
                    # Solo log interno
                    logger.logger.debug(f"Ticket {ticket_id} excluido: {motivo}")
                    tickets_salteados += 1
                    tickets_salteados_detalle.append({'ticket_id': ticket_id, 'motivo': motivo})
                    continue
                
                # 3. Verificar condiciones en Freshdesk
                cumple_condiciones, motivo, _ = self.verificar_condiciones_ticket(ticket_data)
                if not cumple_condiciones:
                    # Solo log interno
                    logger.logger.debug(f"Ticket {ticket_id} excluido: {motivo}")
                    tickets_salteados += 1
                    tickets_salteados_detalle.append({'ticket_id': ticket_id, 'motivo': motivo})
                    continue
                
                # 4. Realizar actualización automática - MOSTRAR PROGRESO EN CONSOLA
                print(f"   - Actualizando automáticamente ticket {ticket_id}")
                # Log interno
                logger.logger.info(f"Actualizando automáticamente ticket {ticket_id}")
                
                print(f"   - Iniciando actualización en 2 pasos para ticket {ticket_id}")
                # Log interno
                logger.logger.info(f"Iniciando actualización en 2 pasos para ticket {ticket_id}")
                
                exito, mensaje = self.actualizar_campos_con_estrategia_null(ticket_id, valores_excel)
                
                if exito:
                    tickets_actualizados += 1
                    print(f"   - Actualización completa exitosa para ticket {ticket_id}")
                    print(f"   - ✅ Ticket {ticket_id} actualizado exitosamente")
                    # Log interno
                    logger.logger.info(f"Ticket {ticket_id} actualizado exitosamente")
                else:
                    tickets_error += 1
                    print(f"   - ❌ Error en ticket {ticket_id}: {mensaje}")
                    # Guardar ticket con error para reporte final
                    tickets_con_error.append({'ticket_id': ticket_id, 'error': mensaje})
                    # Log interno con detalles
                    logger.logger.error(f"Error en ticket {ticket_id}: {mensaje}")
                
                # Pausa entre tickets
                time.sleep(3)
                
        except KeyboardInterrupt:
            display.clear_line()
            print(f"\r⏹️  Proceso cancelado por el usuario")
            print(f"📊 Progreso hasta la cancelación:")
            print(f"   ✅ Actualizados: {tickets_actualizados}")
            print(f"   ⏭️  Salteados: {tickets_salteados}")
            print(f"   ❌ Errores: {tickets_error}")
        
        # Mostrar resumen final
        display.clear_line()
        self.mostrar_resumen_final(total_tickets, tickets_actualizados, tickets_salteados, tickets_error)
        
        # Mostrar detalles de errores si los hay
        if tickets_con_error:
            self.mostrar_detalle_errores(tickets_con_error)
        
        display.press_enter_to_continue()

    def mostrar_detalle_errores(self, tickets_con_error):
        """Mostrar detalle de tickets con errores"""
        print("\n" + "=" * 80)
        print("❌ DETALLE DE TICKETS CON ERRORES - REVISIÓN MANUAL REQUERIDA")
        print("=" * 80)
        
        for i, ticket_error in enumerate(tickets_con_error, 1):
            print(f"{i:2d}. 🎫 Ticket #{ticket_error['ticket_id']}")
            print(f"      📋 Error: {ticket_error['error']}")
            print(f"      🔧 Acción: Revisar manualmente en Freshdesk")
            print()
        
        print("💡 RECOMENDACIONES:")
        print("   • Verificar que el ticket exista en Freshdesk")
        print("   • Revisar permisos de la API Key")
        print("   • Verificar conexión a internet")
        print("   • Intentar actualización manual del ticket")
        print("=" * 80)

    def mostrar_resumen_final(self, total, actualizados, salteados, errores):
        """Mostrar resumen compacto del proceso"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN FINAL - REGENERACIÓN DE ETIQUETAS")
        print("=" * 60)
        
        print(f"📋 Total tickets procesados: {total}")
        print(f"✅ Tickets actualizados exitosamente: {actualizados}")
        print(f"⏭️ Tickets salteados: {salteados}")
        print(f"❌ Errores en actualización: {errores}")
        print("=" * 60)
        
        if actualizados > 0:
            print("🎯 Las etiquetas CREATE CLARITY deberían generarse automáticamente")
        
        if errores > 0:
            print("⚠️  Se encontraron errores - revisar detalle arriba")
        
        # Log detallado
        logger.logger.info(f"Resumen proceso regeneración etiquetas: "
                    f"Total={total}, Actualizados={actualizados}, "
                    f"Salteados={salteados}, Errores={errores}")