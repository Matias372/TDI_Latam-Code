# 📁 src/menus/classification_menu.py

import os
import pandas as pd
import json
from utils.display_utils import display
from utils.file_utils import FileUtils
from utils.validation_utils import ValidationUtils
from features.classification.classification_engine import ClassificationEngine, initialize_classification_system
from features.classification.pattern_manager import PatternManager
from features.classification.library_generator import ClassificationLibraryGenerator

class ClassificationMenu:
    def __init__(self, config_manager, freshdesk_service=None):
        self.config_manager = config_manager
        self.freshdesk_service = freshdesk_service
        self.classification_engine = initialize_classification_system()
        self.pattern_manager = PatternManager(config_manager)
        self.library_generator = ClassificationLibraryGenerator()

    def mostrar_menu_principal(self):
        """Menú principal de clasificación"""
        while True:
            display.clear_screen()
            display.show_header("SISTEMA DE CLASIFICACIÓN")
            
            opciones = [
                "📚 1. Gestión de Biblioteca",
                "🔍 2. Clasificar Tickets", 
                "📊 3. Reportes y Estadísticas",
                "⚙️  4. Configuración",
                "↩️  0. Volver al menú principal"
            ]
            display.show_bullet_list(opciones)
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.mostrar_menu_biblioteca()
            elif opcion == "2":
                self.mostrar_menu_clasificacion()
            elif opcion == "3":
                self.mostrar_menu_reportes()
            elif opcion == "4":
                self.mostrar_menu_configuracion()
            elif opcion == "0":
                break
            else:
                display.show_message("Opción inválida", "error")
                display.press_enter_to_continue()

    def mostrar_menu_clasificacion(self):
        """Submenú para clasificación de tickets - ACTUALIZADO"""
        while True:
            display.clear_screen()
            display.show_header("CLASIFICAR TICKETS")
            
            opciones = [
                "🆔 1. Clasificar ticket por ID (Freshdesk)",
                "📝 2. Clasificar ticket manual", 
                "📦 3. Clasificar múltiples tickets manual",
                "↩️  0. Volver al menú anterior"
            ]
            display.show_bullet_list(opciones)
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.clasificar_ticket_por_id()
            elif opcion == "2":
                self.clasificar_ticket_manual()
            elif opcion == "3":
                self.clasificar_tickets_multiples_manual()
            elif opcion == "0":
                break
            else:
                display.show_message("Opción inválida", "error")
                display.press_enter_to_continue()


    def mostrar_menu_biblioteca(self):
        """Submenú para gestión de biblioteca - REORGANIZADO"""
        while True:
            display.clear_screen()
            display.show_header("GESTIÓN DE BIBLIOTECA")
            
            opciones = [
                "📚 1. Generar biblioteca desde Excel",
                "🔄 2. Actualizar biblioteca existente", 
                "🧪 3. Probar precisión desde Excel",
                "🎯 4. Calibrar biblioteca desde reporte",
                "🗑️  5. Eliminar biblioteca actual",
                "↩️  0. Volver al menú anterior"
            ]
            display.show_bullet_list(opciones)
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.generar_biblioteca_desde_excel()
            elif opcion == "2":
                self.actualizar_biblioteca_existente()
            elif opcion == "3":
                self.probar_precision_desde_excel() 
            elif opcion == "4":
                self.calibrar_biblioteca_desde_reporte()
            elif opcion == "5":
                self.eliminar_biblioteca_actual()
            elif opcion == "0":
                break
            else:
                display.show_message("Opción inválida", "error")
                display.press_enter_to_continue()

    # === MÉTODOS DE GESTIÓN DE BIBLIOTECA ===

    def generar_biblioteca_desde_excel(self):
        """Genera biblioteca de clasificación desde archivo Excel"""
        display.show_header("GENERAR BIBLIOTECA DESDE EXCEL")
        
        try:
            display.show_message("Seleccione el archivo Excel con los tickets:", "file")
            excel_path = FileUtils.seleccionar_archivo(
                "Seleccione archivo Excel con tickets", 
                [("Excel files", "*.xlsx *.xls")]
            )
            
            if not excel_path:
                display.show_message("No se seleccionó ningún archivo", "warning")
                display.press_enter_to_continue()
                return
            
            min_tickets = input("Mínimo de tickets por categoría (Enter para 10): ").strip()
            min_tickets = int(min_tickets) if min_tickets.isdigit() else 10
            
            top_keywords = input("Top palabras clave por categoría (Enter para 20): ").strip()
            top_keywords = int(top_keywords) if top_keywords.isdigit() else 20
            
            display.show_message(f"Generando biblioteca desde: {os.path.basename(excel_path)}", "info")
            success, result = self.library_generator.generate_from_excel(
                excel_path=excel_path,
                min_tickets_per_category=min_tickets,
                top_keywords_limit=top_keywords
            )
            
            if success:
                display.show_message("Biblioteca generada exitosamente!", "success")
                display.show_section("ESTADÍSTICAS")
                display.show_key_value("Total tickets analizados", str(result['total_tickets']))
                display.show_key_value("Patrones encontrados", str(result['total_patterns']))
                display.show_key_value("Archivo guardado en", result['output_path'])
                
                self.classification_engine = ClassificationEngine()
            else:
                display.show_message(f"Error: {result}", "error")
                
        except Exception as e:
            display.show_message(f"Error durante la generación: {e}", "error")
        
        display.press_enter_to_continue()

    def actualizar_biblioteca_existente(self):
        """Actualiza biblioteca existente con nuevos datos - MEJORADO"""
        display.show_header("ACTUALIZAR BIBLIOTECA EXISTENTE")
        
        try:
            display.show_message("Seleccione el archivo Excel con los nuevos tickets:", "file")
            excel_path = FileUtils.seleccionar_archivo(
                "Seleccione archivo Excel con tickets", 
                [("Excel files", "*.xlsx *.xls")]
            )
            
            if not excel_path:
                display.show_message("No se seleccionó ningún archivo", "warning")
                display.press_enter_to_continue()
                return
            
            display.show_message("Actualizando biblioteca...", "info")
            success, result = self.library_generator.update_existing_library(excel_path)
            
            if success:
                display.show_message("Biblioteca actualizada exitosamente!", "success")
                display.show_section("NUEVOS DATOS INCORPORADOS")
                display.show_key_value("Tickets agregados", str(result['new_tickets']))
                display.show_key_value("Archivo", result['library_path'])
                
                # Recargar el motor de clasificación
                self.classification_engine = ClassificationEngine()
            else:
                display.show_message(f"Error: {result}", "error")
                
        except Exception as e:
            display.show_message(f"Error durante la actualización: {e}", "error")
        
        display.press_enter_to_continue()

    def eliminar_biblioteca_actual(self):
        """Elimina la biblioteca actual"""
        display.show_header("ELIMINAR BIBLIOTECA ACTUAL")
        
        library_path = self.library_generator.get_library_path()
        display.show_message(f"¿Está seguro de eliminar la biblioteca en:", "warning")
        display.show_key_value("Ruta", library_path)
        
        confirmacion = input("\n❓ Escriba 'ELIMINAR' para confirmar: ").strip()
        
        if confirmacion == "ELIMINAR":
            try:
                if os.path.exists(library_path):
                    os.remove(library_path)
                    self.classification_engine = None
                    display.show_message("Biblioteca eliminada exitosamente", "success")
                else:
                    display.show_message("La biblioteca no existe", "warning")
            except Exception as e:
                display.show_message(f"Error eliminando biblioteca: {e}", "error")
        else:
            display.show_message("Eliminación cancelada", "info")
        
        display.press_enter_to_continue()

    # === MÉTODOS DE CLASIFICACIÓN PRINCIPALES ===

    def clasificar_ticket_por_id(self):
        """Clasifica un ticket individual por ID desde Freshdesk"""
        display.show_header("CLASIFICAR TICKET POR ID")
        
        if not self._verificar_biblioteca_cargada():
            print("DEBUG: Biblioteca no cargada, saliendo")  # 🐛 Depuración
            return
        
        if not self.freshdesk_service:
            print("DEBUG: Freshdesk service no disponible")  # 🐛 Depuración
            display.show_message("Servicio Freshdesk no disponible", "error")
            display.press_enter_to_continue()
            return
        
        try:
            ticket_id = input("Ingrese el ID del ticket de Freshdesk: ").strip()
            
            if not ticket_id.isdigit():
                display.show_message("El ID del ticket debe ser un número", "error")
                display.press_enter_to_continue()
                return
            
            ticket_id = int(ticket_id)
            
            confirmar = ValidationUtils.confirmar_accion(f"¿Clasificar ticket #{ticket_id} desde Freshdesk?")
            if not confirmar:
                display.show_message("Operación cancelada", "info")
                return
            
            resultado = self.classification_engine.clasificar_ticket_individual(
                ticket_id, 
                self.freshdesk_service
            )
            
            if 'error' in resultado:
                display.show_message(f"Error: {resultado['error']}", "error")
                display.press_enter_to_continue()
                return
            
            guardar = ValidationUtils.confirmar_accion("¿Desea guardar este resultado en un archivo?")
            if guardar:
                self._guardar_resultado_individual(resultado)
                display.show_message("Resultado guardado exitosamente", "success")
            else:
                display.show_message("Resultado no guardado", "info")
                
        except Exception as e:
            display.show_message(f"Error al clasificar ticket: {e}", "error")
        
        display.press_enter_to_continue()

    def probar_precision_desde_excel(self):
        """Prueba precisión del sistema desde archivo Excel"""
        display.show_header("PROBAR PRECISIÓN DESDE EXCEL")
        
        if not self._verificar_biblioteca_cargada():
            print("DEBUG: Biblioteca no cargada, saliendo")  # 🐛 Depuración
            return
        
        if not self.freshdesk_service:
            print("DEBUG: Freshdesk service no disponible")  # 🐛 Depuración
            display.show_message("Servicio Freshdesk no disponible", "error")
            display.press_enter_to_continue()
            return
        
        try:
            display.show_message("Seleccione el archivo Excel con los tickets para prueba", "info")
            display.show_bullet_list([
                "El archivo debe contener columnas: id, producto, segmento, fabricante, motivo",
                "La columna 'id' es obligatoria",
                "Las demás columnas se usarán para comparación"
            ])
            
            excel_path = FileUtils.seleccionar_archivo(
                "Seleccione archivo Excel con tickets para prueba", 
                [("Excel files", "*.xlsx *.xls")]
            )
            
            if not excel_path:
                display.show_message("No se seleccionó ningún archivo", "warning")
                display.press_enter_to_continue()
                return
            
            # Cargar el archivo para contar registros
            try:
                df_temp = pd.read_excel(excel_path)
                total_tickets_temp = len(df_temp)
            except:
                total_tickets_temp = "desconocido"
            
            confirmar = ValidationUtils.confirmar_accion(
                f"¿Procesar {total_tickets_temp} tickets desde el archivo?"
            )
            
            if not confirmar:
                display.show_message("Proceso cancelado por el usuario", "info")
                return
            
            display.show_message("Iniciando prueba de precisión...", "info")
            
            resultados = self.classification_engine.clasificar_tickets_prueba(
                excel_path, 
                self.freshdesk_service
            )
            
            if 'error' in resultados:
                display.show_message(f"Error: {resultados['error']}", "error")
                display.press_enter_to_continue()
                return
            
            # Mostrar reporte
            print("\n" + resultados['reporte'])
            
            if resultados['resultados']:
                guardar = ValidationUtils.confirmar_accion("¿Desea guardar los resultados en Excel?")
                if guardar:
                    archivo_resultados = self.classification_engine.guardar_resultados_excel(
                        resultados['resultados']
                    )
                    display.show_message(f"Resultados guardados en: {archivo_resultados}", "success")
                else:
                    display.show_message("Resultados no guardados", "info")
            
            self._mostrar_resumen_rapido(resultados['resultados'])
            
        except Exception as e:
            display.show_message(f"Error en prueba de precisión: {e}", "error")
        
        display.press_enter_to_continue()

    def clasificar_ticket_manual(self):
        """Clasifica un ticket ingresado manualmente"""
        display.show_header("CLASIFICAR TICKET MANUAL")
        
        if not self._verificar_biblioteca_cargada():
            return
        
        asunto = input("Ingrese el asunto del ticket: ").strip()
        descripcion = input("Ingrese la descripción (opcional): ").strip()
        
        if not asunto:
            display.show_message("El asunto es obligatorio", "error")
            display.press_enter_to_continue()
            return
        
        display.show_message("Analizando ticket...", "info")
        reporte = self.classification_engine.generate_detailed_report(asunto, descripcion)
        print(reporte)
        
        display.press_enter_to_continue()

    def clasificar_tickets_multiples_manual(self):
        """Clasifica múltiples tickets ingresados manualmente"""
        display.show_header("CLASIFICAR MÚLTIPLES TICKETS MANUAL")
        
        if not self._verificar_biblioteca_cargada():
            return
        
        tickets = []
        display.show_message("Ingrese los tickets (deje el asunto vacío para terminar):", "info")
        
        while True:
            display.show_subsection(f"Ticket {len(tickets) + 1}")
            asunto = input("Asunto: ").strip()
            
            if not asunto:
                break
                
            descripcion = input("Descripción (opcional): ").strip()
            tickets.append({
                'id': len(tickets) + 1,
                'subject': asunto,
                'description': descripcion
            })
        
        if not tickets:
            display.show_message("No se ingresaron tickets", "warning")
            display.press_enter_to_continue()
            return
        
        display.show_message(f"Procesando {len(tickets)} tickets...", "info")
        resultados = self.classification_engine.batch_classify(tickets)
        
        self._mostrar_resultados_lote(resultados)
        display.press_enter_to_continue()

    # === MÉTODOS AUXILIARES ===

    def _mostrar_resultado_clasificacion_individual(self, resultado: dict):
        """Muestra resultado de clasificación individual"""
        display.show_header(f"RESULTADO DE CLASIFICACIÓN - Ticket #{resultado['id']}")
        display.show_key_value("Asunto", resultado.get('asunto', 'N/A'))
        display.show_key_value("Descripción", resultado.get('descripcion', 'N/A'))
        display.show_divider()
        display.show_key_value("PRODUCTO", resultado.get('producto_recomendado', 'N/A'))
        display.show_key_value("SEGMENTO", resultado.get('segmento_recomendado', 'N/A'))
        display.show_key_value("FABRICANTE", resultado.get('fabricante_recomendado', 'N/A'))
        display.show_key_value("MOTIVO", resultado.get('motivo_recomendado', 'N/A'))
        display.show_key_value("CONFIANZA", f"{resultado.get('confianza_promedio', 0):.2f}")
        display.show_divider()
        display.show_key_value("REGLA APLICADA", resultado.get('regla_aplicada', 'N/A'))

    def _mostrar_resumen_rapido(self, resultados: list):
        """Muestra resumen rápido de los resultados"""
        if not resultados:
            return
        
        df = pd.DataFrame(resultados)
        
        total = len(resultados)
        precision_producto = (df['producto_coincide'].sum() / total) * 100
        precision_general = df['precision_general'].mean()
        
        display.show_section("RESUMEN RÁPIDO")
        display.show_key_value("Total tickets", str(total))
        display.show_key_value("Precisión general", f"{precision_general:.2f}%")
        display.show_key_value("Productos correctos", f"{precision_producto:.2f}%")
        
        discrepancias = df[df['precision_general'] < 100]
        if not discrepancias.empty:
            display.show_section(f"Tickets con discrepancias: {len(discrepancias)}")
            for _, ticket in discrepancias.head(3).iterrows():
                display.show_message(
                    f"Ticket #{ticket['id']}: {ticket['producto_original']} → {ticket['producto_recomendado']}", 
                    "warning"
                )

    def _guardar_resultado_individual(self, resultado: dict):
        """Guarda resultado individual en archivo usando FileUtils"""
        try:
            # Usar FileUtils para obtener la carpeta de reportes
            reports_folder = FileUtils.get_classification_reports_folder()
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            archivo = os.path.join(reports_folder, f'clasificacion_individual_{timestamp}.xlsx')
            
            df = pd.DataFrame([resultado])
            df.to_excel(archivo, index=False)
            
            display.show_message(f"✅ Resultado guardado en: {archivo}", "success")
            display.show_message(f"📁 Carpeta: {reports_folder}", "info")
            
        except Exception as e:
            display.show_message(f"❌ Error guardando resultado: {e}", "error")

    def _verificar_biblioteca_cargada(self):
        """Verifica si hay una biblioteca cargada - MEJORADA"""
        try:
            if self.classification_engine is None:
                self.classification_engine = initialize_classification_system()
            
            # Verificar si la biblioteca tiene patrones
            if not self.classification_engine.patterns:
                display.show_message("❌ No hay biblioteca de clasificación cargada.", "error")
                display.show_message("💡 Use la opción 'Gestión de Biblioteca' para generar una.", "info")
                
                # Preguntar si quiere generar una básica
                generar = input("\n¿Desea generar una biblioteca básica ahora? (s/n): ").strip().lower()
                if generar == 's':
                    from features.classification.classification_engine import generar_biblioteca_clasificacion
                    generar_biblioteca_clasificacion()
                    self.classification_engine = initialize_classification_system()
                    
                    # Verificar si se creó correctamente
                    if self.classification_engine.patterns:
                        display.show_message("✅ Biblioteca básica creada exitosamente", "success")
                        return True
                    else:
                        display.show_message("❌ No se pudo crear la biblioteca básica", "error")
                        return False
                else:
                    display.press_enter_to_continue()
                    return False
            
            # Si llegamos aquí, la biblioteca está cargada
            total_campos = len(self.classification_engine.patterns)
            total_categorias = sum(len(categorias) for categorias in self.classification_engine.patterns.values())
            
            display.show_message(f"✅ Biblioteca cargada: {total_campos} campos, {total_categorias} categorías", "success")
            return True
            
        except Exception as e:
            display.show_message(f"❌ Error verificando biblioteca: {e}", "error")
            return False

    def _mostrar_resultados_lote(self, resultados):
        """Muestra resultados de clasificación por lote"""
        display.show_section("RESULTADOS DEL LOTE")
        display.show_key_value(
            "Tickets procesados", 
            f"{resultados['classified_tickets']}/{resultados['total_tickets']}"
        )
        
        display.show_section("RESUMEN POR CAMPO")
        for campo, categorias in resultados['summary'].items():
            display.show_subsection(campo)
            for categoria, cantidad in categorias.items():
                display.show_key_value(categoria, f"{cantidad} tickets")
        
        if resultados['results']:
            display.show_section("EJEMPLOS DETALLADOS (primeros 3)")
            for resultado in resultados['results'][:3]:
                display.show_subsection(f"Ticket {resultado['ticket_id']}")
                display.show_key_value("Asunto", resultado['subject'][:50] + "...")
                for campo, recomendaciones in resultado['classification'].items():
                    if campo != 'siglas_detectadas' and recomendaciones:
                        top_rec = recomendaciones[0]
                        display.show_key_value(
                            campo, 
                            f"{top_rec['category']} (score: {top_rec['score']})"
                        )

    # === MÉTODOS DE REPORTES Y CONFIGURACIÓN ===

    def mostrar_menu_reportes(self):
        """Submenú para reportes y estadísticas"""
        while True:
            display.clear_screen()
            display.show_header("REPORTES Y ESTADÍSTICAS")
            
            opciones = [
                "📈 1. Resumen de clasificaciones",
                "🔤 2. Estadísticas de palabras clave", 
                "🏷️  3. Distribución por categorías",
                "📋 4. Exportar reporte completo",
                "↩️  0. Volver al menú anterior"
            ]
            display.show_bullet_list(opciones)
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.generar_resumen_clasificaciones()
            elif opcion == "2":
                self.mostrar_estadisticas_palabras_clave()
            elif opcion == "3":
                self.mostrar_distribucion_categorias()
            elif opcion == "4":
                self.exportar_reporte_completo()
            elif opcion == "0":
                break
            else:
                display.show_message("Opción inválida", "error")
                display.press_enter_to_continue()

    def mostrar_menu_configuracion(self):
        """Submenú para configuración del sistema"""
        while True:
            display.clear_screen()
            display.show_header("CONFIGURACIÓN")
            
            opciones = [
                "📏 1. Ajustar umbrales de confianza",
                "🔤 2. Gestionar siglas personalizadas",
                "🔄 3. Gestionar patrones variables", 
                "📁 4. Configurar rutas de archivos",
                "🧹 5. Limpiar caché y datos temporales",
                "↩️  0. Volver al menú anterior"
            ]
            display.show_bullet_list(opciones)
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.ajustar_umbrales_confianza()
            elif opcion == "2":
                self.gestionar_siglas_personalizadas()
            elif opcion == "3":
                self.pattern_manager.mostrar_menu_gestion_patrones()
            elif opcion == "4":
                self.configurar_rutas_archivos()
            elif opcion == "5":
                self.limpiar_cache_datos()
            elif opcion == "0":
                break
            else:
                display.show_message("Opción inválida", "error")
                display.press_enter_to_continue()
    
    def calibrar_biblioteca_desde_reporte(self):
        """Calibra la biblioteca usando un reporte de precisión para mejorar la clasificación"""
        display.show_header("CALIBRAR BIBLIOTECA DESDE REPORTE")
        
        if not self._verificar_biblioteca_cargada():
            return
        
        if not self.freshdesk_service:
            display.show_message("Servicio Freshdesk no disponible", "error")
            display.press_enter_to_continue()
            return

        try:
            # Seleccionar archivo de reporte
            display.show_message("Seleccione el archivo Excel de reporte de precisión", "file")
            reporte_path = FileUtils.seleccionar_archivo(
                "Seleccione archivo de reporte de precisión", 
                [("Excel files", "*.xlsx *.xls")]
            )
            
            if not reporte_path:
                display.show_message("No se seleccionó ningún archivo", "warning")
                display.press_enter_to_continue()
                return

            # Cargar el reporte
            df_reporte = pd.read_excel(reporte_path)
            
            # Verificar que tenga las columnas necesarias
            columnas_necesarias = ['id', 'precision_general', 'producto_original', 'segmento_original', 
                                'fabricante_original', 'motivo_original']
            if not all(col in df_reporte.columns for col in columnas_necesarias):
                display.show_message("El archivo no tiene las columnas necesarias", "error")
                display.press_enter_to_continue()
                return

            # Filtrar tickets con baja precisión (por ejemplo, menos de 100%)
            df_baja_precision = df_reporte[df_reporte['precision_general'] < 100]
            
            if df_baja_precision.empty:
                display.show_message("No hay tickets con baja precisión en el reporte", "info")
                display.press_enter_to_continue()
                return

            # 🆕 CORRECCIÓN: Resetear índice para evitar problemas
            df_baja_precision = df_baja_precision.reset_index(drop=True)
            
            # 🆕 VERIFICACIÓN ADICIONAL: Mostrar información del DataFrame
            display.show_message(f"Encontrados {len(df_baja_precision)} tickets con baja precisión", "info")
            display.show_message(f"Rango de IDs en el reporte: {df_baja_precision['id'].min()} a {df_baja_precision['id'].max()}", "info")
            
            # Preguntar al usuario si desea continuar
            if not ValidationUtils.confirmar_accion("¿Desea calibrar la biblioteca con estos tickets?"):
                display.show_message("Calibración cancelada", "info")
                return

            # 🆕 CORRECCIÓN: Usar contador propio en lugar del índice del DataFrame
            total = len(df_baja_precision)
            exitosos = 0
            procesados = 0
            
            # 🆕 CORRECCIÓN: Iterar con enumerate para tener control del índice
            for idx, row in df_baja_precision.iterrows():
                ticket_id = row['id']
                procesados += 1
                
                # 🆕 VERIFICACIÓN: Mostrar información del ticket actual
                display.show_processing_message(f"#{ticket_id}", procesados, total, "Calibrando")
                
                # 🆕 VERIFICACIÓN: Limitar el número de tickets para pruebas
                if procesados > 1000:  # Límite de seguridad
                    display.show_message("⚠️  Límite de seguridad alcanzado (1000 tickets)", "warning")
                    break
                
                try:
                    # Obtener ticket desde Freshdesk
                    resultado = self.classification_engine.clasificar_ticket_individual(ticket_id, self.freshdesk_service)
                    
                    if 'error' in resultado:
                        display.show_message(f"❌ Error al obtener ticket #{ticket_id}: {resultado['error']}", "error")
                        continue

                    # Extraer los valores originales (correctos) del reporte
                    valores_correctos = {
                        'Producto': row['producto_original'],
                        'Segmento': row['segmento_original'],
                        'Fabricante': row['fabricante_original'],
                        'Tipo de Ticket': row['motivo_original']
                    }

                    # Actualizar la biblioteca con los valores correctos
                    if self._actualizar_biblioteca_con_valores_correctos(resultado, valores_correctos):
                        exitosos += 1
                        
                except Exception as ticket_error:
                    display.show_message(f"❌ Error procesando ticket #{ticket_id}: {ticket_error}", "error")
                    continue

            display.clear_line()
            display.show_message(f"✅ Calibración completada: {exitosos}/{procesados} tickets procesados exitosamente", "success")
            
            # Recargar la biblioteca para reflejar los cambios
            if exitosos > 0:
                self.classification_engine.load_library()
                display.show_message("✅ Biblioteca recargada con los nuevos patrones", "success")
            
        except Exception as e:
            display.show_message(f"❌ Error durante la calibración: {e}", "error")
        
        display.press_enter_to_continue()

    def _actualizar_biblioteca_con_valores_correctos(self, resultado_ticket: dict, valores_correctos: dict):
        """
        Actualiza la biblioteca con las palabras clave del ticket asociadas a los valores correctos.
        """
        try:
            # Obtener el asunto y descripción del ticket
            asunto = resultado_ticket.get('asunto', '')
            descripcion = resultado_ticket.get('descripcion', '')
            
            # Combinar texto para análisis
            texto_completo = f"{asunto} {descripcion}"
            
            # 🆕 VERIFICACIÓN: Asegurarse de que el método existe
            if not hasattr(self.classification_engine, 'extraer_palabras_clave_avanzado'):
                display.show_message("❌ Error: Método 'extraer_palabras_clave_avanzado' no encontrado", "error")
                return False
            
            # Extraer palabras clave - MÉTODO PÚBLICO
            palabras_clave = self.classification_engine.extraer_palabras_clave_avanzado(texto_completo)
            
            if not palabras_clave:
                return False

            # Cargar la biblioteca actual
            library_path = self.classification_engine.library_path
            
            # 🆕 VERIFICACIÓN: Asegurarse de que el archivo existe
            if not os.path.exists(library_path):
                display.show_message(f"❌ Biblioteca no encontrada en: {library_path}", "error")
                return False
                
            with open(library_path, 'r', encoding='utf-8') as f:
                biblioteca = json.load(f)

            # Actualizar cada campo con los valores correctos
            for campo, valor_correcto in valores_correctos.items():
                if valor_correcto and valor_correcto != 'No especificado':
                    if campo not in biblioteca['patrones_clasificacion']:
                        biblioteca['patrones_clasificacion'][campo] = {}
                    
                    if valor_correcto not in biblioteca['patrones_clasificacion'][campo]:
                        # Crear nueva categoría
                        biblioteca['patrones_clasificacion'][campo][valor_correcto] = {
                            'total_tickets': 1,
                            'palabras_clave': palabras_clave,
                            'ejemplos_asuntos': [asunto],
                            'frecuencia_palabras': sum(palabras_clave.values())
                        }
                    else:
                        # Actualizar categoría existente
                        categoria = biblioteca['patrones_clasificacion'][campo][valor_correcto]
                        
                        # Combinar palabras clave
                        palabras_existentes = categoria.get('palabras_clave', {})
                        for palabra, frecuencia in palabras_clave.items():
                            if palabra in palabras_existentes:
                                palabras_existentes[palabra] += frecuencia
                            else:
                                palabras_existentes[palabra] = frecuencia
                        
                        # Ordenar y limitar palabras clave
                        palabras_combinadas = dict(
                            sorted(palabras_existentes.items(), key=lambda x: x[1], reverse=True)[:20]
                        )
                        
                        categoria['palabras_clave'] = palabras_combinadas
                        categoria['total_tickets'] += 1
                        categoria['frecuencia_palabras'] = sum(palabras_combinadas.values())
                        
                        # Agregar asunto a ejemplos si no está
                        if asunto not in categoria['ejemplos_asuntos']:
                            categoria['ejemplos_asuntos'].append(asunto)
                            # Mantener solo los últimos 10 ejemplos
                            if len(categoria['ejemplos_asuntos']) > 10:
                                categoria['ejemplos_asuntos'] = categoria['ejemplos_asuntos'][-10:]

            # Guardar biblioteca actualizada
            with open(library_path, 'w', encoding='utf-8') as f:
                json.dump(biblioteca, f, indent=2, ensure_ascii=False)
            
            return True
                
        except Exception as e:
            display.show_message(f"❌ Error actualizando biblioteca: {e}", "error")
            return False

    # Métodos de reportes y configuración (placeholders)
    def generar_resumen_clasificaciones(self):
        display.show_header("RESUMEN DE CLASIFICACIONES")
        display.show_message("Función en desarrollo...", "warning")
        display.press_enter_to_continue()

    def mostrar_estadisticas_palabras_clave(self):
        display.show_header("ESTADÍSTICAS DE PALABRAS CLAVE")
        display.show_message("Función en desarrollo...", "warning")
        display.press_enter_to_continue()

    def mostrar_distribucion_categorias(self):
        display.show_header("DISTRIBUCIÓN POR CATEGORÍAS")
        display.show_message("Función en desarrollo...", "warning")
        display.press_enter_to_continue()

    def exportar_reporte_completo(self):
        display.show_header("EXPORTAR REPORTE COMPLETO")
        display.show_message("Función en desarrollo...", "warning")
        display.press_enter_to_continue()

    def ajustar_umbrales_confianza(self):
        display.show_header("AJUSTAR UMBRALES DE CONFIANZA")
        display.show_message("Función en desarrollo...", "warning")
        display.press_enter_to_continue()

    def gestionar_siglas_personalizadas(self):
        display.show_header("GESTIONAR SIGLAS PERSONALIZADAS")
        display.show_message("Función en desarrollo...", "warning")
        display.press_enter_to_continue()

    def configurar_rutas_archivos(self):
        display.show_header("CONFIGURAR RUTAS DE ARCHIVOS")
        display.show_message("Función en desarrollo...", "warning")
        display.press_enter_to_continue()

    def limpiar_cache_datos(self):
        display.show_header("LIMPIAR CACHÉ Y DATOS TEMPORALES")
        display.show_message("Función en desarrollo...", "warning")
        display.press_enter_to_continue()