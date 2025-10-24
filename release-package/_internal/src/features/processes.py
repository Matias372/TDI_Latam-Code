import pandas as pd
from datetime import datetime, timezone
from services.freshdesk_service import FreshdeskService
from utils.file_utils import FileUtils
from utils.validation_utils import ValidationUtils
from utils.api_utils import ApiUtils
from config.state_mapping import MAPEO_ESTADOS_FD_API_A_CLARITY, mapear_estado_desde_api
from utils.display_utils import display
from utils.logging import logger
# O para funcionalidades específicas:
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
        print("\n╔══════════════════════════════════════════════╗")
        print("║              📨 ENVÍO DE NOTAS               ║")
        print("╚══════════════════════════════════════════════╝")
        
        print("\n📋 Seleccione el archivo de tickets a procesar:")
        ruta_archivo_tickets = FileUtils.seleccionar_archivo("Seleccione el archivo de tickets")
        if not ruta_archivo_tickets:
            print("❌ No se seleccionó ningún archivo.")
            display.press_enter_to_continue()
            return

        tickets_df = FileUtils.cargar_excel(ruta_archivo_tickets)
        if tickets_df is None or tickets_df.empty:
            print("❌ No se pudieron cargar los tickets o el archivo está vacío.")
            display.press_enter_to_continue()
            return

        if 'Ticket ID' not in tickets_df.columns:
            print("❌ El archivo debe contener la columna 'Ticket ID'")
            display.press_enter_to_continue()
            return

        # Cargar archivo de agentes
        print("\n👥 Seleccione el archivo de agentes:")
        ruta_agentes = FileUtils.seleccionar_archivo("Seleccione el archivo de agentes")
        if not ruta_agentes:
            print("❌ No se seleccionó el archivo de agentes.")
            display.press_enter_to_continue()
            return

        agentes_df = FileUtils.cargar_excel(ruta_agentes)
        if agentes_df is None or agentes_df.empty:
            display.press_enter_to_continue()
            return

        # Verificar estructura del archivo de agentes
        columnas_requeridas = ['ID', 'Agente', 'MAIL']
        if not all(col in agentes_df.columns for col in columnas_requeridas):
            print(f"❌ El archivo de agentes debe contener las columnas: {columnas_requeridas}")
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
        print("\n╔══════════════════════════════════════════════╗")
        print("║              📨 ENVÍO DE NOTAS               ║")
        print("╚══════════════════════════════════════════════╝")
        
        print(f"\n📊 Procesando {total_tickets} tickets encontrados...")
        print("💡 Presione Ctrl+C para cancelar el proceso")
        print("🔍 En modo manual, la barra se pausará para confirmaciones\n")

        try:
            for index, ticket_row in tickets_df.iterrows():
                ticket_id = ticket_row['Ticket ID']
                current = index + 1

                # 🎯 ACTUALIZACIÓN EN TIEMPO REAL
                display.show_processing_message(
                    ticket_id=ticket_id,
                    current=current,
                    total=total_tickets,
                    status=f"✅:{enviados_ok} ⏭️:{rechazados} ❌:{errores}"
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
                
                # Verificar si es ticket de bitácora
                subject = ticket.get("subject", "")
                if "BITACORA" in subject.upper():
                    rechazados += 1
                    continue

                # Verificar inactividad (más de 10 días)
                updated_at_str = ticket.get("updated_at", "")
                if not updated_at_str:
                    rechazados += 1
                    continue

                try:
                    from datetime import datetime, timezone
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

                # 🎯 CONFIRMACIÓN EN MODO MANUAL (CON PAUSA DE BARRA)
                if not automatico:
                    display.clear_line()
                    print(f"\n📋 TICKET #{ticket_id} - CONFIRMACIÓN REQUERIDA")
                    print("─" * 50)
                    print(f"👤 Agentes: {', '.join(nombres_agentes)}")
                    print(f"📧 Emails: {', '.join(notify_emails)}")
                    print(f"💬 Mensaje:\n{mensaje}")
                    print("─" * 50)
                    
                    confirmado = ValidationUtils.confirmar_accion("¿Desea enviar la nota interna?")
                    
                    if not confirmado:
                        print(f"❌ Nota NO enviada para el ticket {ticket_id}")
                        rechazados += 1
                        # Reanudar barra de progreso
                        display.show_processing_message(ticket_id, current, total_tickets, f"✅:{enviados_ok} ⏭️:{rechazados} ❌:{errores}")
                        continue
                    
                    # Reanudar barra de progreso después de la confirmación
                    display.show_processing_message(ticket_id, current, total_tickets, f"✅:{enviados_ok} ⏭️:{rechazados} ❌:{errores}")

                # Enviar nota interna
                if self._enviar_nota_interna(ticket_id, mensaje, notify_emails):
                    enviados_ok += 1
                else:
                    errores += 1
                    tickets_error.append(ticket_id)

            # 🎯 RESULTADO FINAL
            display.clear_line()
            print(f"\r🎉 Procesamiento completado!")
            print("\n---------------------------------------")
            print("📊 Resultados: ")
            print(f"✅ Enviados correctamente: {enviados_ok}")  
            print(f"⏭️ Omitidos por condición: {rechazados}")
            print(f"❌ Error en envío: {errores}")
            print("---------------------------------------")

            # Manejo de errores
            if errores > 0:
                print(f"\n¿Desea ver los tickets con error? (S/N): ", end="")
                if input().strip().upper() == 'S':
                    print("\n📋 Tickets con errores:")
                    for t_id in tickets_error[:10]:
                        print(f"   • Ticket ID: {t_id}")
                    if len(tickets_error) > 10:
                        print(f"   ... y {len(tickets_error) - 10} más")

            print("\n🎯 PROCESO FINALIZADO")

        except KeyboardInterrupt:
            display.clear_line()
            print(f"\r⏹️  Proceso cancelado por el usuario")
            print(f"📊 Progreso hasta la cancelación:")
            print(f"   ✅ Enviados: {enviados_ok}")
            print(f"   ⏭️  Omitidos: {rechazados}")
            print(f"   ❌ Errores: {errores}")

        display.press_enter_to_continue()

    def _generar_mensaje_segun_estado(self, ticket):
        """Generar mensaje personalizado según el estado del ticket"""
        # 🎯 USAR MAPEO UNIFICADO
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
            print(f"   ⚡ Reemplazando agente especial {agente_especial_id} por {agente_reemplazo_id}")
            responder_id = agente_reemplazo_id

        if internal_id == agente_especial_id:
            print(f"   ⚡ Reemplazando agente especial {agente_especial_id} por {agente_reemplazo_id}")
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
                print(f"   👤 Agente conocido: {nombre} ({mail})")
            else:
                # 🎯 PAUSAR BARRA DE PROGRESO PARA AGREGAR NUEVO AGENTE
                display.clear_line()
                print(f"\r⚠️  NUEVO AGENTE DETECTADO: ID {ag_id}")
                print("📝 Por favor, ingrese los datos del nuevo agente:")
                
                nombre = input("   👉 Nombre del agente: ").strip()
                mail = input("   📧 Email del agente: ").strip()
                
                if not nombre or not mail:
                    print("   ❌ Nombre y email son obligatorios. Agente omitido.")
                    continue
                    
                # Validar email básico
                if "@" not in mail:
                    print("   ❌ Email inválido. Debe contener '@'. Agente omitido.")
                    continue
                    
                # Agregar a lista de nuevos agentes
                nuevos_agentes.append({'ID': ag_id, 'Agente': nombre, 'MAIL': mail})
                # Agregar temporalmente al diccionario para este ticket
                agentes_dict[ag_id] = (nombre, mail)
                
                print(f"   ✅ Agente '{nombre}' agregado temporalmente")

            notify_emails.append(mail)
            nombres_agentes.append(nombre)

        # 🎯 GUARDADO SIMPLIFICADO Y EFECTIVO
        if nuevos_agentes:
            try:
                display.clear_line()
                print(f"\r💾 Guardando {len(nuevos_agentes)} nuevo(s) agente(s)...")
                
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
                
                print(f"   ✅ {len(nuevos_agentes)} agente(s) guardado(s) correctamente")
                print(f"   📊 Total de agentes en archivo: {len(agentes_completo)}")
                
                # Devolver el DataFrame actualizado
                return (notify_emails, nombres_agentes), agentes_completo
                
            except Exception as e:
                print(f"   ❌ Error al guardar agentes: {e}")
                print("   ⚠️  Los agentes nuevos solo están en memoria para esta sesión")
                # Continuar con los agentes en memoria
                return (notify_emails, nombres_agentes), None

        return (notify_emails, nombres_agentes), None


    def _confirmar_envio(self, ticket_id, agentes, mensaje, emails):
        """Confirmar envío de nota interna"""
        print("\n" + "="*50)
        print(f"Ticket ID: {ticket_id}")
        print(f"Agentes: {', '.join(agentes)}")
        print(f"Emails: {', '.join(emails)}")
        print(f"Mensaje:\n{mensaje}")
        print("="*50)
        return ValidationUtils.confirmar_accion("¿Desea enviar la nota interna?")

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
                print(f"✅ Nota enviada correctamente al ticket {ticket_id}")
                return True
            else:
                print(f"❌ Error al enviar nota: {respuesta.status_code} - {respuesta.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error al enviar nota: {e}")
            return False

    def _mostrar_resumen(self, total, enviados, rechazados, errores, tickets_error):
        """Mostrar resumen final del proceso"""
        print("\n" + "="*60)
        print("📊 RESUMEN FINAL")
        print("="*60)
        print(f"📌 Total de tickets procesados: {total}")
        print(f"✅ Notas enviadas correctamente: {enviados}")
        print(f"⏭ Tickets rechazados/saltados: {rechazados}")
        print(f"❌ Errores en el envío: {errores}")
        print("="*60)

        if errores > 0:
            if ValidationUtils.confirmar_accion("¿Deseas ver la lista de tickets con error?"):
                print("\n=== TICKETS CON ERROR ===")
                for t_id in tickets_error:
                    print(f" - Ticket ID: {t_id}")

        print("\n🎯 PROCESO FINALIZADO")