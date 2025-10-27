# 📁 src/menus/classification_menu.py

import os
import sys
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
        """Submenú para clasificación de tickets - SIMPLIFICADO"""
        while True:
            display.clear_screen()
            display.show_header("CLASIFICAR TICKETS")
            
            opciones = [
                "🆔 1. Clasificar ticket por ID (Freshdesk)",
                "🧪 2. Probar precisión desde Excel",
                "📝 3. Clasificar ticket manual", 
                "📦 4. Clasificar múltiples tickets manual",
                "↩️  0. Volver al menú anterior"
            ]
            display.show_bullet_list(opciones)
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.clasificar_ticket_por_id()
            elif opcion == "2":
                self.probar_precision_desde_excel()
            elif opcion == "3":
                self.clasificar_ticket_manual()
            elif opcion == "4":
                self.clasificar_tickets_multiples_manual()
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
        """Actualiza biblioteca existente con nuevos datos"""
        display.show_header("ACTUALIZAR BIBLIOTECA EXISTENTE")
        
        try:
            excel_path = input("Ingrese la ruta del archivo Excel: ").strip()
            
            if not excel_path:
                excel_path = "data/input/tickets_nuevos.xlsx"
                display.show_message(f"Usando ruta predeterminada: {excel_path}", "info")
            
            display.show_message("Actualizando biblioteca...", "info")
            success, result = self.library_generator.update_existing_library(excel_path)
            
            if success:
                display.show_message("Biblioteca actualizada exitosamente!", "success")
                display.show_section("NUEVOS DATOS INCORPORADOS")
                display.show_key_value("Tickets agregados", str(result['new_tickets']))
                display.show_key_value("Archivo", result['library_path'])
                
                self.classification_engine = ClassificationEngine()
            else:
                display.show_message(f"Error: {result}", "error")
                
        except Exception as e:
            display.show_message(f"Error durante la actualización: {e}", "error")
        
        display.press_enter_to_continue()

    def mostrar_estadisticas_biblioteca(self):
        """Muestra estadísticas de la biblioteca actual"""
        display.show_header("ESTADÍSTICAS DE BIBLIOTECA")
        
        stats = self.library_generator.get_library_statistics()
        
        if stats:
            display.show_key_value("Fecha generación", stats['metadata']['fecha_generacion'])
            display.show_key_value("Total tickets", str(stats['metadata']['total_tickets_analizados']))
            display.show_key_value("Patrones", str(stats['metadata']['total_patrones_encontrados']))
            
            display.show_section("DISTRIBUCIÓN")
            for campo, distribucion in stats['estadisticas'].items():
                if isinstance(distribucion, dict) and 'distribucion' in distribucion:
                    display.show_subsection(campo)
                    for categoria, cantidad in list(distribucion['distribucion'].items())[:5]:
                        display.show_key_value(categoria, f"{cantidad} tickets")
                    if len(distribucion['distribucion']) > 5:
                        display.show_message(f"... y {len(distribucion['distribucion']) - 5} más", "info")
        else:
            display.show_message("No se encontró biblioteca cargada", "warning")
        
        display.press_enter_to_continue()

    def mostrar_ubicacion_biblioteca(self):
        """Muestra dónde se guarda la biblioteca"""
        library_path = self.library_generator.get_library_path()
        display.show_header("UBICACIÓN DE BIBLIOTECA")
        display.show_key_value("Ruta", library_path)
        
        if os.path.exists(library_path):
            file_size = os.path.getsize(library_path) / 1024
            display.show_key_value("Tamaño", f"{file_size:.2f} KB")
            display.show_message("Archivo existe", "success")
        else:
            display.show_message("Archivo no encontrado", "error")
        
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
            return
        
        if not self.freshdesk_service:
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
            return
        
        if not self.freshdesk_service:
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
        """Guarda resultado individual en archivo"""
        try:
            output_dir = os.path.join('data', 'output', 'classification')
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            archivo = os.path.join(output_dir, f'clasificacion_individual_{timestamp}.xlsx')
            
            df = pd.DataFrame([resultado])
            df.to_excel(archivo, index=False)
            
            display.show_message(f"Resultado guardado en: {archivo}", "success")
            
        except Exception as e:
            display.show_message(f"Error guardando resultado: {e}", "error")

    def _verificar_biblioteca_cargada(self):
        """Verifica si hay una biblioteca cargada"""
        if self.classification_engine is None:
            self.classification_engine = ClassificationEngine()
        
        if not self.classification_engine.patterns:
            display.show_message("No hay biblioteca de clasificación cargada.", "error")
            display.show_message("Use la opción 'Generar biblioteca desde Excel' primero.", "info")
            
            generar = input("\n¿Desea generar una biblioteca básica ahora? (s/n): ").strip().lower()
            if generar == 's':
                from features.classification.classification_engine import generar_biblioteca_clasificacion
                generar_biblioteca_clasificacion()
                self.classification_engine = ClassificationEngine()
                return True
            else:
                display.press_enter_to_continue()
                return False
        return True

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