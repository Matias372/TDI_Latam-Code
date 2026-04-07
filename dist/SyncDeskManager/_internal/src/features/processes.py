import pandas as pd
from datetime import datetime, timezone
from services.freshdesk_service import FreshdeskService
from utils.file_utils import FileUtils
from utils.validation_utils import ValidationUtils
from utils.api_utils import ApiUtils
from config.state_mapping import MAPEO_ESTADOS_FD_API_A_CLARITY, mapear_estado_desde_api
from utils.display_utils import display
from utils.logging import logger, TransactionLogger

class Processes:
    def __init__(self, freshdesk_service):
        self.service = freshdesk_service

    def enviar_notas_internas(self):
        """Proceso principal para enviar notas internas a tickets inactivos - CON MODO MANUAL Y ACTUALIZACIÓN DE AGENTES"""
        if not self.service.config.validar_configuracion():
            return

        # Seleccionar archivo de tickets
        display.clear_screen()
        display.show_header("ENVÍO DE NOTAS")
        
        display.show_message("Seleccione el archivo de tickets a procesar:", "file")
        ruta_archivo_tickets = FileUtils.seleccionar_archivo("Seleccione el archivo de tickets")
        if not ruta_archivo_tickets:
            display.show_message("No se seleccionó ningún archivo.", "warning")
            display.press_enter_to_continue()
            return

        tickets_df = FileUtils.cargar_excel(ruta_archivo_tickets)
        if tickets_df is None or tickets_df.empty:
            display.show_message("No se pudieron cargar los tickets o el archivo está vacío.", "error")
            display.press_enter_to_continue()
            return

        if 'Ticket ID' not in tickets_df.columns:
            display.show_message("El archivo debe contener la columna 'Ticket ID'", "error")
            display.press_enter_to_continue()
            return

        # Cargar archivo de agentes
        display.show_message("Seleccione el archivo de agentes:", "file")
        ruta_agentes = FileUtils.seleccionar_archivo("Seleccione el archivo de agentes")
        if not ruta_agentes:
            display.show_message("No se seleccionó el archivo de agentes.", "error")
            display.press_enter_to_continue()
            return

        agentes_df = FileUtils.cargar_excel(ruta_agentes)
        if agentes_df is None or agentes_df.empty:
            display.show_message("No se pudo cargar el archivo de agentes o está vacío.", "error")
            display.press_enter_to_continue()
            return

        # Verificar estructura del archivo de agentes
        columnas_requeridas = ['ID', 'Agente', 'MAIL']
        if not all(col in agentes_df.columns for col in columnas_requeridas):
            display.show_message(f"El archivo de agentes debe contener las columnas: {columnas_requeridas}", "error")
            display.press_enter_to_continue()
            return

        agentes_dict = {row['ID']: (row['Agente'], row['MAIL']) for _, row in agentes_df.iterrows()}

        # Seleccionar modo de ejecución
        automatico = ValidationUtils.seleccionar_modo_ejecucion()

        # Contadores
        enviados_ok = 0
        rechazados = 0
        errores = 0
        tickets_error = []
        total_tickets = len(tickets_df)

        display.clear_screen()
        display.show_header("ENVÍO DE NOTAS")
        
        display.show_message(f"Procesando {total_tickets} tickets encontrados...", "info")
        display.show_message("Presione Ctrl+C para cancelar el proceso", "info")
        if not automatico:
            display.show_message("En modo manual, la barra se pausará para confirmaciones", "info")

        try:
            for index, ticket_row in tickets_df.iterrows():
                ticket_id = ticket_row['Ticket ID']
                current = index + 1

                #  ACTUALIZACIÓN EN TIEMPO REAL
                display.show_processing_message(
                    str(ticket_id),
                    current,
                    total_tickets,
                    f":{enviados_ok} ⏭️:{rechazados} ❌:{errores}"
                )

                # Obtener ticket desde Freshdesk
                respuesta = ApiUtils.get_ticket(
                    self.service.config.freshdesk_domain, 
                    self.service.config.api_key, 
                    ticket_id
                )
                
                if respuesta.status_code != 200:
                    errores += 1
                    tickets_error.append(ticket_id)
                    logger.log_error(f"Error al obtener ticket {ticket_id}: {respuesta.status_code}")
                    continue

                ticket = respuesta.json()

                #  CONDICIÓN TEMPORAL - OMITIR TICKETS DE CMPC - ELIMINAR DESPUÉS
                company_id = ticket.get("company_id")
                if company_id == 82001555186:
                    rechazados += 1
                    display.show_message(f"Ticket {ticket_id} omitido - Compañía CMPC", "warning")
                    continue

                group_id = ticket.get("group_id")
                if group_id in [82000658038, 82000461735, 82000662630]: # Grupos a omitir temporalmente 82000658038: BMC Control-M, 82000461735: CA Workload Automation DE, 82000662630: TRIAGE CHILE
                    rechazados += 1
                    display.show_message(
                        f"Ticket {ticket_id} omitido - Grupo excluido ({group_id})",
                        "warning"
                    )
                    continue
                #  FIN CONDICIÓN TEMPORAL
                
                # OMITIR SI COMPANY ES NULL
                group_info = ticket.get("group")
                company_id_es_null = (
                    company_id is None or 
                    str(company_id).lower() == 'null' or 
                    company_id == ''
                )
                
                if company_id_es_null: 
                    rechazados += 1
                    display.show_message(f"Ticket {ticket_id} omitido - Empresa Null", "warning")
                    continue

                # Verificar si es ticket de bitácora
                subject = ticket.get("subject", "")
                if "BITACORA" in subject.upper():
                    rechazados += 1
                    continue
                
                subject = ticket.get("subject", "")
                if "TAREA CMPC" in subject.upper():
                    rechazados += 1
                    continue

                # Verificar contacto específico a omitir: Loki Loki
                requester_id = ticket.get("requester_id")  # Campo que contiene el ID del contacto
                if requester_id == 82068799698:
                    rechazados += 1
                    display.show_message(f"Ticket {ticket_id} omitido - Contacto específico", "warning")
                    continue

                # Verificar contacto específico a omitir: Soporte Automatizacion
                requester_id = ticket.get("requester_id")  # Campo que contiene el ID del contacto
                if requester_id == 82234514937:
                    rechazados += 1
                    display.show_message(f"Ticket {ticket_id} omitido - Contacto específico", "warning")
                    continue

                # Verificar inactividad (más de 10 días)
                updated_at_str = ticket.get("updated_at", "")
                if not updated_at_str:
                    rechazados += 1
                    continue

                try:
                    updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                    ahora = datetime.now(timezone.utc)
                    dias_inactividad = (ahora - updated_at).days
                    
                    if dias_inactividad < 10:
                        rechazados += 1
                        continue
                except ValueError as e:
                    rechazados += 1
                    continue

                # Determinar mensaje según estado del ticket
                mensaje = self._generar_mensaje_segun_estado(ticket)
                if not mensaje:
                    rechazados += 1
                    continue

                # Obtener y procesar agentes
                agentes_result = self._obtener_agentes_ticket(ticket, agentes_dict, agentes_df, ruta_agentes)
                if not agentes_result or not agentes_result[0]:
                    rechazados += 1
                    continue

                (notify_emails, nombres_agentes), nuevos_agentes_df = agentes_result

                # Si se devolvió un DataFrame actualizado, actualizar nuestra referencia
                if nuevos_agentes_df is not None:
                    agentes_df = nuevos_agentes_df

                # Personalizar mensaje con nombre del agente
                if "[NOMBRE_DE_AGENTE]" in mensaje:
                    mensaje = mensaje.replace("[NOMBRE_DE_AGENTE]", nombres_agentes[0])

                #  CONFIRMACIÓN EN MODO MANUAL (CON PAUSA DE BARRA)
                if not automatico:
                    display.clear_line()
                    display.show_header(f"TICKET #{ticket_id} - CONFIRMACIÓN REQUERIDA")
                    display.show_key_value("Agentes", ', '.join(nombres_agentes))
                    display.show_key_value("Emails", ', '.join(notify_emails))
                    display.show_section("MENSAJE")
                    print(mensaje)
                    display.show_divider()
                    
                    confirmado = ValidationUtils.confirmar_accion("¿Desea enviar la nota interna?")
                    
                    if not confirmado:
                        display.show_message(f"Nota NO enviada para el ticket {ticket_id}", "warning")
                        rechazados += 1
                        # Reanudar barra de progreso
                        display.show_processing_message(str(ticket_id), current, total_tickets, f"OK:{enviados_ok} SKIP:{rechazados} ERROR:{errores}")
                        continue
                    
                    # Reanudar barra de progreso después de la confirmación
                    display.show_processing_message(str(ticket_id), current, total_tickets, f"OK:{enviados_ok} SKIP:{rechazados} ERROR:{errores}")

                # Enviar nota interna
                if self._enviar_nota_interna(ticket_id, mensaje, notify_emails):
                    enviados_ok += 1
                else:
                    errores += 1
                    tickets_error.append(ticket_id)

            #  RESULTADO FINAL
            display.clear_line()
            display.show_message("Procesamiento completado!", "success")
            display.show_section("RESULTADOS")
            display.show_key_value("Enviados correctamente", str(enviados_ok))
            display.show_key_value("Omitidos por condición", str(rechazados))
            display.show_key_value("Error en envío", str(errores))

            # Manejo de errores
            if errores > 0:
                if ValidationUtils.confirmar_accion("¿Desea ver los tickets con error?"):
                    display.show_section("TICKETS CON ERRORES")
                    for t_id in tickets_error[:10]:
                        display.show_message(f"Ticket ID: {t_id}", "error")
                    if len(tickets_error) > 10:
                        display.show_message(f"... y {len(tickets_error) - 10} más", "info")

            display.show_message("PROCESO FINALIZADO", "success")

        except KeyboardInterrupt:
            display.clear_line()
            display.show_message("Proceso cancelado por el usuario", "warning")
            display.show_section("PROGRESO HASTA LA CANCELACIÓN")
            display.show_key_value("Enviados", str(enviados_ok))
            display.show_key_value("Omitidos", str(rechazados))
            display.show_key_value("Errores", str(errores))

        display.press_enter_to_continue()

    def _generar_mensaje_segun_estado(self, ticket):
        """Generar mensaje personalizado según el estado del ticket"""
        #  USAR MAPEO UNIFICADO
        status_numerico = ticket.get("status")
        status = mapear_estado_desde_api(status_numerico)
        
        due_by = ticket.get("due_by")

        try:
            due_by_dt = datetime.fromisoformat(due_by.replace("Z", "+00:00")) if due_by else None
            ahora = datetime.now(timezone.utc)
        except:
            due_by_dt = None

        if status == "Derivado al Fabricante":
            return "Hola [NOMBRE_DE_AGENTE], buen día. Vemos que el ticket está derivado al fabricante. ¿Hubo alguna respuesta o actualización por algún otro medio?"
        elif status == "Esperando al Cliente":
            return "Hola [NOMBRE_DE_AGENTE], buen día. Según el ticket se encuentra esperando respuesta del cliente. ¿Has tenido algún contacto a través de otro canal?"
        elif status not in ["Resuelto", "Cerrado"] and due_by_dt and due_by_dt < ahora:
            return "Hola [NOMBRE_DE_AGENTE], buen día. El tiempo de resolución venció. Por favor revisa el ticket para resolverlo y cerrarlo. Saludos."
        else:
            return "Hola [NOMBRE_DE_AGENTE], buen día. Este ticket no ha tenido actividad reciente. ¿Podrías revisarlo? Gracias."

    def _obtener_agentes_ticket(self, ticket, agentes_dict, agentes_df, ruta_agentes):
        """Obtener información de agentes asignados al ticket - VERSIÓN CORREGIDA"""
        notify_emails = []
        nombres_agentes = []
        
        responder_id = ticket.get("responder_id")
        internal_id = ticket.get("internal_agent_id")

        # LÓGICA ESPECIAL: Reemplazar agente específico
        agente_especial_id = 82209238728
        agente_reemplazo_id = 123456789

        if responder_id == agente_especial_id:
            display.show_message(f"Reemplazando agente especial {agente_especial_id} por {agente_reemplazo_id}", "info")
            responder_id = agente_reemplazo_id

        if internal_id == agente_especial_id:
            display.show_message(f"Reemplazando agente especial {agente_especial_id} por {agente_reemplazo_id}", "info")
            internal_id = agente_reemplazo_id

        # Crear conjunto de agentes únicos
        agentes_unicos = set()
        if responder_id is not None:
            agentes_unicos.add(responder_id)
        if internal_id is not None:
            agentes_unicos.add(internal_id)

        if not agentes_unicos:
            return None

        nuevos_agentes = []

        for ag_id in agentes_unicos:
            if ag_id in agentes_dict:
                nombre, mail = agentes_dict[ag_id]
                display.show_message(f"Agente conocido: {nombre} ({mail})", "debug")
            else:
                #  PAUSAR BARRA DE PROGRESO PARA AGREGAR NUEVO AGENTE
                display.clear_line()
                display.show_message(f"NUEVO AGENTE DETECTADO: ID {ag_id}", "warning")
                display.show_message("Por favor, ingrese los datos del nuevo agente:", "info")
                
                nombre = input("    Nombre del agente: ").strip()
                mail = input("    Email del agente: ").strip()
                
                if not nombre or not mail:
                    display.show_message("Nombre y email son obligatorios. Agente omitido.", "error")
                    continue
                    
                # Validar email básico
                if "@" not in mail:
                    display.show_message("Email inválido. Debe contener '@'. Agente omitido.", "error")
                    continue
                    
                # Agregar a lista de nuevos agentes
                nuevos_agentes.append({'ID': ag_id, 'Agente': nombre, 'MAIL': mail})
                # Agregar temporalmente al diccionario para este ticket
                agentes_dict[ag_id] = (nombre, mail)
                
                display.show_message(f"Agente '{nombre}' agregado temporalmente", "success")

            notify_emails.append(mail)
            nombres_agentes.append(nombre)

        #  GUARDADO SIMPLIFICADO Y EFECTIVO
        if nuevos_agentes:
            try:
                display.clear_line()
                display.show_message(f"Guardando {len(nuevos_agentes)} nuevo(s) agente(s)...", "info")
                
                # CARGAR archivo actual COMPLETO (no usar el DataFrame en memoria)
                agentes_existente = pd.read_excel(ruta_agentes)
                
                # CREAR DataFrame con nuevos agentes
                nuevos_agentes_df = pd.DataFrame(nuevos_agentes)
                
                # COMBINAR y GUARDAR
                agentes_completo = pd.concat([agentes_existente, nuevos_agentes_df], ignore_index=True)
                agentes_completo.to_excel(ruta_agentes, index=False)
                
                # ACTUALIZAR las estructuras en memoria
                for agente in nuevos_agentes:
                    ag_id = agente['ID']
                    nombre = agente['Agente']
                    mail = agente['MAIL']
                    agentes_dict[ag_id] = (nombre, mail)
                
                display.show_message(f"{len(nuevos_agentes)} agente(s) guardado(s) correctamente", "success")
                display.show_key_value("Total de agentes en archivo", str(len(agentes_completo)))
                
                # Devolver el DataFrame actualizado
                return (notify_emails, nombres_agentes), agentes_completo
                
            except Exception as e:
                display.show_message(f"Error al guardar agentes: {e}", "error")
                display.show_message("Los agentes nuevos solo están en memoria para esta sesión", "warning")
                # Continuar con los agentes en memoria
                return (notify_emails, nombres_agentes), None

        return (notify_emails, nombres_agentes), None

    def _enviar_nota_interna(self, ticket_id, mensaje, notify_emails):
        """Enviar nota interna al ticket via API Freshdesk"""
        try:
            respuesta = ApiUtils.enviar_nota_interna(
                self.service.config.freshdesk_domain,
                self.service.config.api_key,
                ticket_id,
                mensaje,
                notify_emails
            )
            
            if respuesta.status_code in [200, 201]:
                display.show_message(f"Nota enviada correctamente al ticket {ticket_id}", "success")
                return True
            else:
                display.show_message(f"Error al enviar nota: {respuesta.status_code} - {respuesta.text}", "error")
                return False
                
        except Exception as e:
            display.show_message(f"Error al enviar nota: {e}", "error")
            return False

    def _mostrar_resumen(self, total, enviados, rechazados, errores, tickets_error):
        """Mostrar resumen final del proceso"""
        display.show_header("RESUMEN FINAL")
        display.show_key_value("Total de tickets procesados", str(total))
        display.show_key_value("Notas enviadas correctamente", str(enviados))
        display.show_key_value("Tickets rechazados/saltados", str(rechazados))
        display.show_key_value("Errores en el envío", str(errores))

        if errores > 0:
            if ValidationUtils.confirmar_accion("¿Deseas ver la lista de tickets con error?"):
                display.show_section("TICKETS CON ERROR")
                for t_id in tickets_error:
                    display.show_message(f"Ticket ID: {t_id}", "error")

        display.show_message("PROCESO FINALIZADO", "success")