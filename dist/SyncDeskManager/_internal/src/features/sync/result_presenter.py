from utils.display_utils import display
from utils.file_utils import FileUtils
from datetime import datetime
import pandas as pd
import os

class ResultPresenter:
    def __init__(self, logger):
        self.logger = logger
    
    def mostrar_resumen_detallado(self, diferencias):
        """🚀 OPTIMIZADO: Mostrar resumen detallado de cambios con DisplayUtils"""
        display.show_section("RESUMEN DE CAMBIOS DETECTADOS")
        display.show_message(f"Se encontraron {len(diferencias)} tickets con diferencias", "sync")
        display.show_divider(80)
        
        # Agrupar cambios por tipo
        cambios_reales = {}
        for diff in diferencias:
            clave = f"{diff.clarity_estado_actual} → {diff.clarity_estado_propuesto}"
            cambios_reales[clave] = cambios_reales.get(clave, []) + [diff.ticket_id]
        
        # Opciones de ordenamiento
        display.show_message("Opciones de ordenamiento:", "info")
        display.show_message("1. 🔢 Por cantidad (mayor a menor)", "info")
        display.show_message("2. 🔄 Por estado actual (alfabético)", "info") 
        display.show_message("3. 🎯 Por estado propuesto (alfabético)", "info")
        
        opcion_orden = input("\nSeleccione ordenamiento (1-3, Enter=1): ").strip()
        
        if opcion_orden == "2":
            cambios_ordenados = sorted(cambios_reales.items(), key=lambda x: x[0].split(' → ')[0])
            display.show_message("Cambios (ordenado por estado actual):", "info")
        elif opcion_orden == "3":
            cambios_ordenados = sorted(cambios_reales.items(), key=lambda x: x[0].split(' → ')[1])
            display.show_message("Cambios (ordenado por estado propuesto):", "info")
        else:
            cambios_ordenados = sorted(cambios_reales.items(), key=lambda x: len(x[1]), reverse=True)
            display.show_message("Cambios (ordenado por cantidad):", "info")
        
        # Mostrar distribución
        for tipo, tickets in cambios_ordenados:
            display.show_message(f"   {tipo}: {len(tickets)} tickets", "info")
        
        # Mostrar detalle
        display.show_message("", "info")  # Línea en blanco
        display.show_message("📝 DETALLE (primeros 20 tickets):", "header")
        display.show_divider(80)
        
        # Crear tabla para mostrar detalle
        headers = ["TICKET ID", "ESTADO ACTUAL", "ESTADO PROPUESTO"]
        rows = []
        
        diferencias_ordenadas = sorted(diferencias, key=lambda x: x.ticket_id)
        
        for diff in diferencias_ordenadas[:20]:
            rows.append([
                diff.ticket_id,
                diff.clarity_estado_actual,
                diff.clarity_estado_propuesto
            ])
        
        display.show_table(headers, rows, [12, 25, 25])
        
        if len(diferencias) > 20:
            display.show_message(f"... y {len(diferencias) - 20} tickets más", "info")
        
        display.show_divider(80)
    
    def mostrar_reporte_final(self, resultado, diferencias):
        """🎯 MEJORADO: Reporte final con DisplayUtils"""
        display.show_section("REPORTE FINAL DE SINCRONIZACIÓN")
        display.show_divider(80)
        
        # Resumen ejecutivo
        display.show_message("📊 RESUMEN EJECUTIVO", "header")
        display.show_key_value("Actualizaciones exitosas", f"{resultado.exitos}", 3)
        display.show_key_value("Actualizaciones fallidas", f"{resultado.fallos}", 3)
        display.show_key_value("Total de cambios identificados", f"{resultado.total_cambios}", 3)
        
        # 🎯 OBTENER TICKETS EXITOSOS Y FALLIDOS
        tickets_exitosos = [d['ticket_id'] for d in resultado.detalles if d['resultado'] == 'Éxito']
        tickets_fallidos = [d['ticket_id'] for d in resultado.detalles if d['resultado'] == 'Error']
        
        if tickets_exitosos:
            display.show_message("", "info")  # Línea en blanco
            display.show_message(f"🎯 TICKETS ACTUALIZADOS EXITOSAMENTE ({len(tickets_exitosos)}):", "success")
            display.show_bullet_list(tickets_exitosos[:10], "✅")
            if len(tickets_exitosos) > 10:
                display.show_message(f"   ... y {len(tickets_exitosos) - 10} más", "info")
        
        if tickets_fallidos:
            display.show_message("", "info")  # Línea en blanco
            display.show_message(f"🚫 TICKETS CON ERRORES ({len(tickets_fallidos)}):", "error")
            # 🎯 MOSTRAR PRIMEROS 5 ERRORES CON DETALLE
            errores_detallados = [d for d in resultado.detalles if d['resultado'] == 'Error']
            for error in errores_detallados[:5]:
                display.show_message(f"   ❌ Ticket {error['ticket_id']}: {error['error']}", "error")
            if len(errores_detallados) > 5:
                display.show_message(f"   ... y {len(errores_detallados) - 5} errores más", "info")
        
        # 🎯 ESTADÍSTICAS DE CAMBIOS APLICADOS
        if tickets_exitosos:
            cambios_aplicados = {}
            for detalle in resultado.detalles:
                if detalle['resultado'] == 'Éxito':
                    clave = f"{detalle['estado_actual']} → {detalle['estado_propuesto']}"
                    cambios_aplicados[clave] = cambios_aplicados.get(clave, 0) + 1
            
            display.show_message("", "info")  # Línea en blanco
            display.show_message("📈 ESTADÍSTICAS DE CAMBIOS APLICADOS:", "header")
            for cambio, cantidad in cambios_aplicados.items():
                display.show_key_value(cambio, f"{cantidad} tickets", 3)
        
        display.show_message("", "info")  # Línea en blanco
        display.show_message(f"⏰ Hora de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
        display.show_divider(80)
        
        # 🎯 OPCIÓN: DESCARGAR REPORTE DE RESULTADOS
        if resultado.detalles:
            display.show_message("¿DESEA DESCARGAR EL REPORTE DETALLADO DE RESULTADOS?", "info")
            display.show_divider(50)
            display.show_message("1. ✅ Sí, descargar Excel con resultados completos", "info")
            display.show_message("2. ❌ No, finalizar proceso", "info")
            display.show_divider(50)
            
            opcion = input("\nSeleccione una opción (1-2): ").strip()
            
            if opcion == "1":
                if self._descargar_excel_resultados(resultado):
                    display.show_message("Proceso completado exitosamente", "success")
                else:
                    display.show_message("Proceso completado con errores en la descarga", "warning")
            else:
                display.show_message("Proceso finalizado", "info")
    
    def _descargar_excel_cambios(self, diferencias):
        """Descargar archivo Excel con la lista completa de cambios propuestos"""
        try:
            display.show_message("Preparando descarga de Excel...", "file")
            
            # Crear DataFrame con todos los cambios
            datos_excel = []
            for diff in diferencias:
                datos_excel.append({
                    'Ticket ID': diff.ticket_id,
                    'Estado Actual (Clarity)': diff.clarity_estado_actual,
                    'Estado Propuesto (Freshdesk)': diff.clarity_estado_propuesto,
                    'Estado Freshdesk Original': diff.freshdesk_estado
                })
            
            df_cambios = pd.DataFrame(datos_excel)
            
            # Obtener ruta de Descargas
            ruta_descargas = self._obtener_ruta_descargas()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"Cambios_Propuestos_Sincronizacion_{timestamp}.xlsx"
            ruta_completa = os.path.join(ruta_descargas, nombre_archivo)
            
            # Guardar Excel
            df_cambios.to_excel(ruta_completa, index=False)
            display.show_message("Archivo descargado exitosamente", "success")
            display.show_message(f"Ubicación: {ruta_completa}", "info")
            display.show_message(f"Total de registros: {len(diferencias)} tickets", "info")
            
            # Mostrar resumen del archivo
            display.show_message("", "info")  # Línea en blanco
            display.show_message("📋 CONTENIDO DEL ARCHIVO:", "header")
            display.show_bullet_list([
                "Ticket ID: Identificador único del ticket",
                "Estado Actual (Clarity): Estado actual en Clarity",
                "Estado Propuesto (Freshdesk): Estado que se aplicará desde Freshdesk",
                "Estado Freshdesk Original: Estado original en Freshdesk"
            ])
            
            return True
            
        except Exception as e:
            display.show_message(f"Error al descargar el archivo: {str(e)}", "error")
            return False

    def _descargar_excel_resultados(self, resultado):
        """🎯 NUEVO: Descargar Excel con resultados detallados de la sincronización"""
        try:
            display.show_message("Preparando descarga de resultados...", "file")
            
            # 🎯 CREAR DATAFRAME CON RESULTADOS DETALLADOS
            datos_excel = []
            for detalle in resultado.detalles:
                datos_excel.append({
                    'Ticket ID': detalle['ticket_id'],
                    'Estado Actual (Clarity)': detalle['estado_actual'],
                    'Estado Propuesto (Freshdesk)': detalle['estado_propuesto'],
                    'Estado Freshdesk Original': detalle['estado_freshdesk_original'],
                    'Resultado': detalle['resultado'],
                    'Error': detalle['error'] or '',  # 🎯 INCLUIR MOTIVO DE ERROR
                    'Investment ID': detalle['investment_id'],
                    'Internal ID': detalle['internal_id']
                })
            
            df_resultados = pd.DataFrame(datos_excel)
            
            # Obtener ruta de Descargas
            ruta_descargas = self._obtener_ruta_descargas()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"Resultados_Sincronizacion_{timestamp}.xlsx"
            ruta_completa = os.path.join(ruta_descargas, nombre_archivo)
            
            # Guardar Excel
            df_resultados.to_excel(ruta_completa, index=False)
            display.show_message("Archivo de resultados descargado exitosamente", "success")
            display.show_message(f"Ubicación: {ruta_completa}", "info")
            display.show_message(f"Total de registros: {len(resultado.detalles)} tickets", "info")
            
            # 🎯 MOSTRAR RESUMEN MEJORADO
            display.show_message("", "info")  # Línea en blanco
            display.show_message("📋 CONTENIDO DEL ARCHIVO:", "header")
            display.show_bullet_list([
                "Ticket ID: Identificador único del ticket",
                "Estado Actual (Clarity): Estado actual en Clarity",
                "Estado Propuesto (Freshdesk): Estado que se intentó aplicar",
                "Estado Freshdesk Original: Estado original en Freshdesk",
                "Resultado: Éxito o Error",
                "Error: Motivo del error (si aplica)",
                "Investment ID: ID de inversión en Clarity",
                "Internal ID: ID interno en Clarity"
            ])
            
            # 🎯 ESTADÍSTICAS RÁPIDAS
            exitos = sum(1 for d in resultado.detalles if d['resultado'] == 'Éxito')
            fallos = sum(1 for d in resultado.detalles if d['resultado'] == 'Error')
            
            display.show_message("", "info")  # Línea en blanco
            display.show_message("📈 ESTADÍSTICAS INCLUIDAS:", "header")
            display.show_key_value("Actualizaciones exitosas", f"{exitos}", 3)
            display.show_key_value("Actualizaciones fallidas", f"{fallos}", 3)
            
            return True
            
        except Exception as e:
            display.show_message(f"Error al descargar el archivo de resultados: {str(e)}", "error")
            return False

    def _obtener_ruta_descargas(self):
        """Obtiene la ruta de la carpeta de Descargas del usuario actual"""
        # Para Windows
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes, windll
            
            CSIDL_PERSONAL = 5  # My Documents
            SHGFP_TYPE_CURRENT = 0
            
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
            
            downloads_path = os.path.join(buf.value, "Downloads")
        else:
            # Para Linux/Mac
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Crear la carpeta si no existe
        os.makedirs(downloads_path, exist_ok=True)
        return downloads_path

    def solicitar_confirmacion(self):
        """Solicitar confirmación al usuario con DisplayUtils"""
        display.show_message("CONFIRMACIÓN REQUERIDA", "warning")
        display.show_divider(50)
        display.show_message("Opciones disponibles:", "info")
        display.show_message("1. ✅ Aplicar cambios en Clarity", "info")
        display.show_message("2. 📥 Descargar Excel con cambios propuestos", "info")
        display.show_message("3. ❌ Cancelar proceso y volver al menú", "info")
        display.show_divider(50)
        
        while True:
            opcion = input("\nSeleccione una opción (1-3): ").strip()
            if opcion in ['1', '2', '3']:
                return opcion
            display.show_message("Opción inválida. Por favor, seleccione 1, 2 o 3.", "error")