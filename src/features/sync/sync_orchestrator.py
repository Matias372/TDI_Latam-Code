from utils.display_utils import display
from utils.logging import logger
from services.clarity_service import ClarityService
from .file_validator import FileValidator
from .state_comparator import StateComparator
from .clarity_id_resolver import ClarityIdResolver
from .change_applier import ChangeApplier
from .result_presenter import ResultPresenter
from .models import FileValidationResult
import os

class SyncOrchestrator:
    def __init__(self, config_manager):
        self.config = config_manager
        self.clarity_service = ClarityService(config_manager)
        
        # Inicializar componentes
        self.file_validator = FileValidator(logger)
        self.state_comparator = StateComparator(logger)
        self.id_resolver = ClarityIdResolver(self.clarity_service, logger)
        self.change_applier = ChangeApplier(self.clarity_service, logger)
        self.result_presenter = ResultPresenter(logger)
        self.transaction_id = None
    
    def sincronizar_estados(self):
        """Método principal de sincronización - INTERFAZ MEJORADA"""
        self._mostrar_cabecera()
        
        if not self.config.validar_configuracion_clarity():
            display.show_message("Configuración de Clarity incompleta", "error")
            display.press_enter_to_continue()
            return False

        try:
            display.show_message("Iniciando transacción de sincronización...", "info")
            self.transaction_id = self._iniciar_transaccion()
            
            # 1. VALIDACIÓN DE ARCHIVOS
            display.show_section("VALIDACIÓN DE ARCHIVOS")
            validacion = self.file_validator.cargar_y_validar_archivos()
            if not validacion.es_valido:
                display.show_message(f"Error en validación: {validacion.mensaje}", "error")
                display.press_enter_to_continue()
                self._completar_transaccion_fallida(validacion.mensaje)
                return False

            display.show_message("Archivos validados correctamente", "success")
            display.show_message(f"Freshdesk: {len(validacion.df_freshdesk)} tickets", "info")
            display.show_message(f"Clarity: {len(validacion.df_clarity)} tickets", "info")

            # ANÁLISIS DE ESTADOS
            display.show_section("ANÁLISIS DE ESTADOS")
            analisis = self.state_comparator.analizar_estados_archivos(
                validacion.df_freshdesk, 
                validacion.df_clarity
            )
            self.state_comparator.mostrar_analisis_estados(analisis)
            
            # MEJORA: Mostrar opciones de manera más clara
            display.show_message("", "info")
            display.show_message("¿Desea continuar con la comparación detallada?", "info")
            display.show_bullet_list([
                "✅ Sí, continuar con la sincronización",
                "❌ No, volver al menú"
            ])
            
            opcion_analisis = input("\nSeleccione opción (1/2): ").strip()
            if opcion_analisis != "1":
                display.show_message("Proceso cancelado por el usuario después del análisis", "warning")
                self._completar_transaccion_cancelada("Usuario canceló después del análisis")
                display.press_enter_to_continue()  # 🆕 Asegurar que espere
                return False

            # Actualizar metadatos
            self._actualizar_metadatos_transaccion(validacion)

            # 2. COMPARACIÓN DE ESTADOS - MEJORAR ACTUALIZACIÓN
            display.show_section("COMPARACIÓN DE ESTADOS")
            display.show_message("Comparando estados entre sistemas...", "sync")
            
            # 🆕 MEJORA: La barra de progreso se maneja internamente en state_comparator
            diferencias = self.state_comparator.comparar_estados(
                validacion.df_freshdesk, 
                validacion.df_clarity
            )
            
            # 🆕 LIMPIAR LÍNEA DE PROGRESO AL FINAL
            display.clear_line()
            
            if not diferencias:
                display.show_message("No se encontraron diferencias entre Freshdesk y Clarity", "success")
                display.press_enter_to_continue()
                self._completar_transaccion_exitosa(0, 0, 0)
                return True

            # 3. RESOLUCIÓN DE IDs DE CLARITY - MEJORAR MANEJO DE ERRORES
            display.show_section("RESOLUCIÓN DE IDs")
            display.show_message(f"Buscando IDs de Clarity para {len(diferencias)} tickets...", "search")
            
            diferencias_completas = self.id_resolver.resolver_ids_clarity(diferencias)
            
            # 🆕 LIMPIAR LÍNEA DE PROGRESO AL FINAL
            display.clear_line()
            
            if not diferencias_completas:
                display.show_message("❌ No se pudieron obtener los IDs de Clarity", "error")
                display.show_message("🔍 Posibles causas:", "warning")
                display.show_bullet_list([
                    "Credenciales de Clarity incorrectas o expiradas",
                    "Problemas de conexión con el servidor de Clarity",
                    "Los tickets no existen en Clarity",
                    "Problemas de permisos en la API de Clarity",
                    "El dominio de Clarity no es accesible"
                ])
                
                # 🆕 ESPERAR A QUE EL USUARIO VEA EL ERROR ANTES DE CONTINUAR
                display.press_enter_to_continue()
                self._completar_transaccion_fallida("No se pudieron obtener los IDs de Clarity")
                return False

            # 4. PRESENTACIÓN Y CONFIRMACIÓN
            display.show_section("CONFIRMACIÓN DE CAMBIOS")
            self.result_presenter.mostrar_resumen_detallado(diferencias_completas)
            
            opcion = self.result_presenter.solicitar_confirmacion()
            if opcion == "2":
                self.result_presenter._descargar_excel_cambios(diferencias_completas)
                self._completar_transaccion_cancelada("Usuario descargó Excel sin aplicar cambios")
                display.press_enter_to_continue()  # 🆕 Asegurar que espere
                return True
            elif opcion == "3":
                display.show_message("Proceso cancelado por el usuario", "warning")
                self._completar_transaccion_cancelada("Usuario canceló el proceso")
                display.press_enter_to_continue()  # 🆕 Asegurar que espere
                return False

            # 5. APLICACIÓN DE CAMBIOS
            display.show_section("APLICACIÓN DE CAMBIOS")
            display.show_message("Aplicando cambios en Clarity...", "sync")
            resultado = self.change_applier.aplicar_cambios_clarity(diferencias_completas, self.transaction_id)

            # 6. REPORTE FINAL
            display.show_section("REPORTE FINAL")
            self.result_presenter.mostrar_reporte_final(resultado, diferencias_completas)

            # COMPLETAR TRANSACCIÓN EXITOSA
            self._completar_transaccion_exitosa(
                resultado.total_cambios, 
                resultado.exitos, 
                resultado.fallos,
                resultado.detalles
            )
            
            # 🆕 ESPERAR ANTES DE VOLVER AL MENÚ
            display.press_enter_to_continue()
            return resultado.exitos > 0

        except KeyboardInterrupt:
            display.clear_line()
            display.show_message("Sincronización cancelada por el usuario", "warning")
            self._completar_transaccion_cancelada("Cancelado por usuario (KeyboardInterrupt)")
            display.press_enter_to_continue()  # 🆕 Asegurar que espere
            return False
        except Exception as e:
            logger.log_error(f"Error en sincronización: {str(e)}")
            display.show_message(f"❌ Error inesperado: {str(e)}", "error")
            display.show_message("📋 Revisa el archivo de logs para más detalles", "info")
            self._completar_transaccion_fallida(f"Excepción: {str(e)}")
            display.press_enter_to_continue()  # 🆕 Asegurar que espere
            return False
    
    def _mostrar_cabecera(self):
        """🎯 INTERFAZ LIMPIA: Cabecera con DisplayUtils"""
        display.clear_screen()
        display.show_header("🔄 SINCRONIZACIÓN ESTADOS")
        display.show_message("Iniciando sincronización desde archivos Excel/CSV", "header")
        display.show_message("Log transaccional activado - Todos los cambios serán registrados", "info")
        display.show_divider(60)
    
    def _iniciar_transaccion(self):
        """Iniciar transacción de logging"""
        transaction_id = logger.transaction_logger.start_transaction(
            process_type="SYNC_STATES",
            description="Sincronización estados Freshdesk → Clarity",
            metadata={
                'configuracion': 'volatile',
                'inicio_timestamp': self._get_current_timestamp()
            }
        )
        logger.log_info(f"Transacción iniciada: {transaction_id}")
        return transaction_id
    
    def _get_current_timestamp(self):
        """Obtener timestamp actual formateado"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _actualizar_metadatos_transaccion(self, validacion):
        """Actualizar metadatos de la transacción con info de archivos"""
        metadata = {
            'freshdesk_file': os.path.basename(validacion.df_freshdesk.attrs.get('file_path', 'desconocido')),
            'clarity_file': os.path.basename(validacion.df_clarity.attrs.get('file_path', 'desconocido')),
            'total_tickets_freshdesk': len(validacion.df_freshdesk),
            'total_tickets_clarity': len(validacion.df_clarity),
            'diferencias_iniciales': len(validacion.df_freshdesk)
        }
        
        logger.transaction_logger._update_transaction(self.transaction_id, 'metadata', metadata)
    
    def _completar_transaccion_exitosa(self, total, exitos, fallos, detalles=None):
        """Completar transacción exitosa"""
        summary = {
            'total_cambios': total,
            'cambios_exitosos': exitos,
            'cambios_fallidos': fallos,
            'estado': 'COMPLETED'
        }
        
        if detalles and len(detalles) > 0:
            tickets_exitosos = [d['ticket_id'] for d in detalles if d['resultado'] == 'Éxito'][:5]
            tickets_fallidos = [d['ticket_id'] for d in detalles if d['resultado'] == 'Error'][:5]
            summary['ejemplos_exitosos'] = tickets_exitosos
            summary['ejemplos_fallidos'] = tickets_fallidos
        
        logger.transaction_logger.complete_transaction(self.transaction_id, summary)
        logger.log_info(f"Transacción completada exitosamente: {self.transaction_id}")
    
    def _completar_transaccion_fallida(self, error_msg):
        """Completar transacción fallida"""
        logger.transaction_logger.fail_transaction(self.transaction_id, {
            'estado': 'FAILED',
            'error': error_msg
        })
        logger.log_error(f"Transacción fallida: {self.transaction_id} - {error_msg}")
    
    def _completar_transaccion_cancelada(self, motivo):
        """Completar transacción cancelada"""
        logger.transaction_logger.fail_transaction(self.transaction_id, {
            'estado': 'CANCELLED',
            'motivo': motivo
        })
        logger.log_warning(f"Transacción cancelada: {self.transaction_id} - {motivo}")