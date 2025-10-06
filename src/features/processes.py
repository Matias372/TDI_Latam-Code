import pandas as pd
from datetime import datetime, timezone
from services.freshdesk_service import FreshdeskService
from utils.file_utils import FileUtils
from utils.validation_utils import ValidationUtils
from utils.api_utils import ApiUtils

class Processes:
    def __init__(self, freshdesk_service):
        self.service = freshdesk_service

    def enviar_notas_internas(self):
        """Proceso principal para enviar notas internas a tickets inactivos"""
        if not self.service.config.validar_configuracion():
            return

        # Seleccionar archivo de tickets
        print("\n📋 Seleccione el archivo de tickets a procesar:")
        ruta_archivo_tickets = FileUtils.seleccionar_archivo("Seleccione el archivo de tickets")
        if not ruta_archivo_tickets:
            print("❌ No se seleccionó ningún archivo.")
            return

        tickets_df = FileUtils.cargar_excel(ruta_archivo_tickets)
        if tickets_df is None or tickets_df.empty:
            print("❌ No se pudieron cargar los tickets o el archivo está vacío.")
            return

        # Verificar que tenga la columna necesaria
        if 'Ticket ID' not in tickets_df.columns:
            print("❌ El archivo debe contener la columna 'Ticket ID'")
            return

        # Cargar archivo de agentes
        print("\n👥 Seleccione el archivo de agentes:")
        ruta_agentes = FileUtils.seleccionar_archivo("Seleccione el archivo de agentes (AGENTES_FD.xlsx)")
        if not ruta_agentes:
            print("❌ No se seleccionó el archivo de agentes.")
            return

        agentes_df = FileUtils.cargar_excel(ruta_agentes)
        if agentes_df is None or agentes_df.empty:
            return

        # Verificar estructura del archivo de agentes
        columnas_requeridas = ['ID', 'Agente', 'MAIL']
        if not all(col in agentes_df.columns for col in columnas_requeridas):
            print(f"❌ El archivo de agentes debe contener las columnas: {columnas_requeridas}")
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

        print(f"\n🔄 Procesando {total_tickets} tickets...")

        # Recorrer tickets
        for index, ticket_row in tickets_df.iterrows():
            ticket_id = ticket_row['Ticket ID']
            print(f"\n--- Procesando Ticket ID: {ticket_id} ({index + 1}/{total_tickets}) ---")

            # Obtener ticket desde Freshdesk
            respuesta = ApiUtils.get_ticket(
                self.service.config.freshdesk_domain, 
                self.service.config.api_key, 
                ticket_id
            )
            
            if respuesta.status_code != 200:
                print(f"❌ Error al obtener ticket {ticket_id}: {respuesta.status_code}")
                errores += 1
                tickets_error.append(ticket_id)
                continue

            ticket = respuesta.json()
            
            # Verificar si es ticket de bitácora
            subject = ticket.get("subject", "")
            if "BITACORA" in subject.upper():
                print(f"⚠ Ticket {ticket_id} saltado (contiene 'BITACORA').")
                rechazados += 1
                continue

            # Verificar inactividad (más de 10 días)
            updated_at_str = ticket.get("updated_at", "")
            if not updated_at_str:
                print(f"⚠ Ticket {ticket_id} sin fecha de actualización. Saltando...")
                rechazados += 1
                continue

            try:
                updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                ahora = datetime.now(timezone.utc)
                dias_inactividad = (ahora - updated_at).days
                
                if dias_inactividad < 10:
                    print(f"⚠ Ticket {ticket_id} saltado. Última actividad hace {dias_inactividad} días.")
                    rechazados += 1
                    continue
            except ValueError as e:
                print(f"⚠ Error al procesar fecha del ticket {ticket_id}: {e}")
                rechazados += 1
                continue

            # Determinar mensaje según estado del ticket
            mensaje = self._generar_mensaje_segun_estado(ticket)
            if not mensaje:
                rechazados += 1
                continue

            # Obtener y procesar agentes
            agentes_info = self._obtener_agentes_ticket(ticket, agentes_dict, agentes_df, ruta_agentes)
            if not agentes_info:
                print(f"❌ Ticket {ticket_id} sin agentes asignados.")
                if not automatico:
                    saltar = input("¿Desea saltar este ticket y continuar? (S/N): ").strip().upper()
                    if saltar != "S":
                        print("⏸ Ejecución detenida para revisión.")
                        break
                rechazados += 1
                continue

            notify_emails, nombres_agentes = agentes_info

            # Personalizar mensaje con nombre del agente
            if "[NOMBRE_DE_AGENTE]" in mensaje:
                mensaje = mensaje.replace("[NOMBRE_DE_AGENTE]", nombres_agentes[0])

            # Confirmar envío (modo manual)
            if not automatico:
                if not self._confirmar_envio(ticket_id, nombres_agentes, mensaje, notify_emails):
                    print(f"❌ Nota NO enviada para el ticket {ticket_id}")
                    rechazados += 1
                    continue

            # Enviar nota interna
            if self._enviar_nota_interna(ticket_id, mensaje, notify_emails):
                enviados_ok += 1
            else:
                errores += 1
                tickets_error.append(ticket_id)

        # Mostrar resumen final
        self._mostrar_resumen(total_tickets, enviados_ok, rechazados, errores, tickets_error)

    def _generar_mensaje_segun_estado(self, ticket):
        """Generar mensaje personalizado según el estado del ticket"""
        status_map = {
            2: "Abierto", 
            4: "Resuelto", 
            5: "Cerrado", 
            6: "Esperando al Cliente",
            7: "Derivado al Fabricante", 
            9: "En Progreso"
        }
        
        status = status_map.get(ticket.get("status"), "Otro/No definido")
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
        """Obtener información de agentes asignados al ticket"""
        notify_emails = []
        nombres_agentes = []
        
        responder_id = ticket.get("responder_id")
        internal_id = ticket.get("internal_agent_id")

        # LÓGICA ESPECIAL: Reemplazar agente específico
        agente_especial_id = 82209238728
        agente_reemplazo_id = 123456789

        if responder_id == agente_especial_id:
            print(f"⚡ Reemplazando agente especial {agente_especial_id} por {agente_reemplazo_id}")
            responder_id = agente_reemplazo_id

        if internal_id == agente_especial_id:
            print(f"⚡ Reemplazando agente especial {agente_especial_id} por {agente_reemplazo_id}")
            internal_id = agente_reemplazo_id

        # Crear conjunto de agentes únicos
        agentes_unicos = set()
        if responder_id is not None:
            agentes_unicos.add(responder_id)
        if internal_id is not None:
            agentes_unicos.add(internal_id)

        if not agentes_unicos:
            return None

        for ag_id in agentes_unicos:
            if ag_id in agentes_dict:
                nombre, mail = agentes_dict[ag_id]
                print(f"👤 Agente: {nombre} ({mail})")
            else:
                print(f"⚠ Agente {ag_id} no identificado.")
                nombre = input("Ingrese nombre del agente: ").strip()
                mail = input("Ingrese mail del agente: ").strip()
                
                if not nombre or not mail:
                    print("❌ Nombre y mail son obligatorios.")
                    continue
                    
                # Agregar a diccionario y actualizar archivo
                agentes_dict[ag_id] = (nombre, mail)
                nuevo_agente = pd.DataFrame([{'ID': ag_id, 'Agente': nombre, 'MAIL': mail}])
                agentes_df = pd.concat([agentes_df, nuevo_agente], ignore_index=True)
                
                try:
                    agentes_df.to_excel(ruta_agentes, index=False)
                    print(f"✅ Agente {nombre} agregado a la base de datos")
                except Exception as e:
                    print(f"❌ Error al guardar agente: {e}")
                    continue

            notify_emails.append(mail)
            nombres_agentes.append(nombre)

        return (notify_emails, nombres_agentes) if notify_emails else None

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