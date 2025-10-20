import pandas as pd
import os
from services.freshdesk_service import FreshdeskService
from services.clarity_service import ClarityService
from utils.file_utils import FileUtils
from datetime import datetime
import unicodedata
from config.state_mapping import MAPEO_ESTADOS_FD_TEXTO_A_CLARITY, mapear_estado_desde_texto
from utils.display_utils import display

class SyncProcess:
    def __init__(self, config_manager):
        self.config = config_manager
        self.freshdesk_service = FreshdeskService(config_manager)
        self.clarity_service = ClarityService(config_manager)
        
        # 🎯 USAR MAPEO UNIFICADO
        self.mapeo_estados_exacto = MAPEO_ESTADOS_FD_TEXTO_A_CLARITY    
        

    def sincronizar_estados(self):
        """🎯 ACTUALIZADO: Flujo completo con barras de progreso"""
        display.clear_screen()
        print("╔══════════════════════════════════════════════╗")
        print("║           🔄 SINCRONIZACIÓN ESTADOS          ║")
        print("╚══════════════════════════════════════════════╝")
        print("🚀 INICIANDO SINCRONIZACIÓN DESDE ARCHIVOS EXCEL/CSV")
        print("═" * 60)
        
        if not self.config.validar_configuracion_clarity():
            print("❌ Configuración de Clarity incompleta. Use el menú de configuración primero.")
            display.press_enter_to_continue()
            return False

        try:
            # 1. Cargar archivo de Freshdesk
            self._mostrar_progreso_fase(1, 4, "Cargando archivo Freshdesk...")
            print("\n\n📁 CARGANDO ARCHIVO DE FRESHDESK")
            print("-" * 40)
            ruta_freshdesk = FileUtils.seleccionar_archivo("Seleccione el archivo de Freshdesk", [("Excel files", "*.xlsx *.xls")])
            if not ruta_freshdesk:
                print("❌ No se seleccionó archivo de Freshdesk.")
                return False

            df_freshdesk = FileUtils.cargar_excel(ruta_freshdesk)
            if df_freshdesk is None or df_freshdesk.empty:
                print("❌ No se pudo cargar el archivo de Freshdesk o está vacío.")
                return False

            # 2. Cargar archivo de Clarity
            self._mostrar_progreso_fase(2, 4, "Cargando archivo Clarity...")
            print("\n\n📁 CARGANDO ARCHIVO DE CLARITY")
            print("-" * 40)
            ruta_clarity = FileUtils.seleccionar_archivo("Seleccione el archivo de Clarity", [("CSV files", "*.csv")])
            if not ruta_clarity:
                print("❌ No se seleccionó archivo de Clarity.")
                return False

            df_clarity = FileUtils.cargar_csv(ruta_clarity)
            if df_clarity is None or df_clarity.empty:
                print("🔄 La carga automática falló, intentando carga manual...")
                df_clarity = FileUtils.cargar_csv_manual(ruta_clarity)
            
            if df_clarity is None or df_clarity.empty:
                print("❌ No se pudo cargar el archivo de Clarity o está vacío.")
                return False

            # 3. Verificación de estructura de archivos
            self._mostrar_progreso_fase(3, 4, "Verificando estructura...")
            print("\n\n🔍 VERIFICANDO ESTRUCTURA DE ARCHIVOS")
            print("-" * 40)
            if not self.verificar_estructura_archivos(df_freshdesk, df_clarity):
                return False

            print(f"✅ Archivo Freshdesk cargado: {len(df_freshdesk)} tickets")
            print(f"✅ Archivo Clarity cargado: {len(df_clarity)} tickets")

            # 4. Comparación de estados con barra de progreso
            self._mostrar_progreso_fase(4, 4, "Comparando estados...", 0, len(df_freshdesk), 0)
            print("\n\n📊 ANALIZANDO ESTADOS Y BUSCANDO DIFERENCIAS")
            print("-" * 40)
            
            diferencias_locales = self._comparar_estados_locales(df_freshdesk, df_clarity)
            
            if not diferencias_locales:
                display.clear_line()
                print("\r🎉 No se encontraron diferencias entre Freshdesk y Clarity")
                display.press_enter_to_continue()
                return True

            # 5. Buscar IDs en Clarity para tickets con diferencias
            print(f"\n📥 BUSCANDO IDs EN CLARITY PARA {len(diferencias_locales)} TICKETS CON DIFERENCIAS")
            print("-" * 50)
            diferencias_completas = self._obtener_ids_para_diferencias(diferencias_locales)
            
            if not diferencias_completas:
                print("❌ No se pudieron obtener los IDs de Clarity para los tickets con diferencias")
                return False

            # 6. Mostrar resumen detallado de cambios
            print("\n📋 RESUMEN DETALLADO DE CAMBIOS")
            print("═" * 80)
            self.mostrar_resumen_detallado(diferencias_completas)

            # 7. 🎯 SISTEMA DE CONFIRMACIÓN MEJORADO
            while True:
                print("\n⚠️  CONFIRMACIÓN REQUERIDA")
                print("═" * 50)
                print("Opciones disponibles:")
                print("1. ✅ Aplicar cambios en Clarity")
                print("2. 📥 Descargar Excel con cambios propuestos")
                print("3. ❌ Cancelar proceso y volver al menú")
                print("═" * 50)
                
                opcion = input("\nSeleccione una opción (1-3): ").strip()

                if opcion == "1":
                    break
                elif opcion == "2":
                    if self._descargar_excel_cambios(diferencias_completas):
                        print("🔄 Volviendo al menú de opciones...")
                        continue
                    else:
                        print("❌ Error al descargar el archivo. Volviendo al menú...")
                        continue
                elif opcion == "3":
                    print("🚫 Proceso cancelado por el usuario")
                    return False
                else:
                    print("❌ Opción inválida. Por favor, seleccione 1, 2 o 3.")
                    continue

            # 8. Aplicar cambios
            print("\n🔄 APLICANDO CAMBIOS EN CLARITY")
            print("═" * 50)
            resultado = self.aplicar_cambios_clarity(diferencias_completas)
            
            # 9. 🎯 REPORTE FINAL MEJORADO (con opción de descargar resultados)
            self.mostrar_reporte_final(resultado, diferencias_completas)
        
        except KeyboardInterrupt:
            display.clear_line()
            print(f"\r⏹️  Sincronización cancelada por el usuario")
            return False

        return True
        

    def _buscar_columna_flexible(self, df, palabras_clave):
        """🚀 MÉTODO REUTILIZABLE: Búsqueda flexible de columnas"""
        columnas = df.columns.tolist()
        for col in columnas:
            col_lower = col.lower()
            for palabra in palabras_clave:
                if palabra in col_lower:
                    return col
        return None
    
    def _descargar_excel_resultados(self, resultado):
        """🎯 NUEVO: Descargar Excel con resultados detallados de la sincronización"""
        try:
            print("\n📥 PREPARANDO DESCARGA DE RESULTADOS...")
            
            # 🎯 CREAR DATAFRAME CON RESULTADOS DETALLADOS
            datos_excel = []
            for detalle in resultado['detalles']:
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
            print(f"✅ ARCHIVO DE RESULTADOS DESCARGADO EXITOSAMENTE")
            print(f"📁 Ubicación: {ruta_completa}")
            print(f"📊 Total de registros: {len(resultado['detalles'])} tickets")
            
            # 🎯 MOSTRAR RESUMEN MEJORADO
            print(f"\n📋 CONTENIDO DEL ARCHIVO:")
            print(f"   - Ticket ID: Identificador único del ticket")
            print(f"   - Estado Actual (Clarity): Estado actual en Clarity")
            print(f"   - Estado Propuesto (Freshdesk): Estado que se intentó aplicar")
            print(f"   - Estado Freshdesk Original: Estado original en Freshdesk")
            print(f"   - Resultado: Éxito o Error")
            print(f"   - Error: Motivo del error (si aplica)")
            print(f"   - Investment ID: ID de inversión en Clarity")
            print(f"   - Internal ID: ID interno en Clarity")
            
            # 🎯 ESTADÍSTICAS RÁPIDAS
            exitos = sum(1 for d in resultado['detalles'] if d['resultado'] == 'Éxito')
            fallos = sum(1 for d in resultado['detalles'] if d['resultado'] == 'Error')
            print(f"\n📈 ESTADÍSTICAS INCLUIDAS:")
            print(f"   ✅ Actualizaciones exitosas: {exitos}")
            print(f"   ❌ Actualizaciones fallidas: {fallos}")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR al descargar el archivo de resultados: {str(e)}")
            return False

    def _descargar_excel_cambios(self, diferencias):
        """Descargar archivo Excel con la lista completa de cambios propuestos"""
        try:
            print("\n📥 PREPARANDO DESCARGA DE EXCEL...")
            
            # Crear DataFrame con todos los cambios
            datos_excel = []
            for diff in diferencias:
                datos_excel.append({
                    'Ticket ID': diff['ticket_id'],
                    'Estado Actual (Clarity)': diff['clarity_estado_actual'],
                    'Estado Propuesto (Freshdesk)': diff['clarity_estado_propuesto'],
                    'Estado Freshdesk Original': diff['freshdesk_estado']
                })
            
            df_cambios = pd.DataFrame(datos_excel)
            
            # Obtener ruta de Descargas
            ruta_descargas = self._obtener_ruta_descargas()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"Cambios_Propuestos_Sincronizacion_{timestamp}.xlsx"
            ruta_completa = os.path.join(ruta_descargas, nombre_archivo)
            
            # Guardar Excel
            df_cambios.to_excel(ruta_completa, index=False)
            print(f"✅ ARCHIVO DESCARGADO EXITOSAMENTE")
            print(f"📁 Ubicación: {ruta_completa}")
            print(f"📊 Total de registros: {len(diferencias)} tickets")
            
            # Mostrar resumen del archivo
            print(f"\n📋 CONTENIDO DEL ARCHIVO:")
            print(f"   - Ticket ID: Identificador único del ticket")
            print(f"   - Estado Actual (Clarity): Estado actual en Clarity")
            print(f"   - Estado Propuesto (Freshdesk): Estado que se aplicará desde Freshdesk")
            print(f"   - Estado Freshdesk Original: Estado original en Freshdesk")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR al descargar el archivo: {str(e)}")
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

    def verificar_estructura_archivos(self, df_freshdesk, df_clarity):
        """🎯 VERIFICACIÓN CORREGIDA: Buscar específicamente 'Estado Freshdesk'"""
        errores = []
        
        print(f"📋 Columnas Freshdesk: {list(df_freshdesk.columns)}")
        print(f"📋 Columnas Clarity: {list(df_clarity.columns)}")
        
        # Verificar Freshdesk
        if 'Ticket ID' not in df_freshdesk.columns:
            errores.append("❌ Freshdesk debe contener 'Ticket ID'")
        
        if 'Estado' not in df_freshdesk.columns:
            errores.append("❌ Freshdesk debe contener 'Estado'")
        else:
            estados_freshdesk = df_freshdesk['Estado'].unique()
            print(f"📝 Estados Freshdesk: {list(estados_freshdesk)}")

        # 🎯 BUSCAR ESPECÍFICAMENTE "Estado Freshdesk" EN CLARITY
        columna_id = None
        columna_estado_freshdesk = None
        
        print(f"🔍 Buscando columna 'Estado Freshdesk' en Clarity...")
        
        # Buscar primero la columna exacta "Estado Freshdesk"
        for col in df_clarity.columns:
            if 'estado freshdesk' in col.lower():
                columna_estado_freshdesk = col
                print(f"   ✅ Encontrada columna: '{col}'")
                break
        
        # Si no se encuentra, buscar variantes
        if not columna_estado_freshdesk:
            for col in df_clarity.columns:
                if 'freshdesk' in col.lower():
                    columna_estado_freshdesk = col
                    print(f"   ✅ Encontrada columna relacionada: '{col}'")
                    break
        
        # Buscar columna ID
        for col in df_clarity.columns:
            if 'id' in col.lower():
                columna_id = col
                break

        if not columna_id:
            errores.append("❌ No se encontró columna de ID en Clarity")
        else:
            print(f"✅ Columna ID detectada: '{columna_id}'")
            df_clarity.rename(columns={columna_id: 'ID'}, inplace=True)

        if not columna_estado_freshdesk:
            errores.append("❌ No se encontró columna 'Estado Freshdesk' en Clarity")
            print(f"   🔍 Columnas disponibles en Clarity: {list(df_clarity.columns)}")
        else:
            print(f"🎯 COLUMNA CRÍTICA DETECTADA: '{columna_estado_freshdesk}'")
            df_clarity.rename(columns={columna_estado_freshdesk: 'Estado_Freshdesk_Clarity'}, inplace=True)
            
            if 'Estado_Freshdesk_Clarity' in df_clarity.columns:
                estados_clarity = df_clarity['Estado_Freshdesk_Clarity'].unique()
                print(f"📝 Estados Freshdesk en Clarity: {list(estados_clarity)}")
            else:
                print("⚠️  Advertencia: La columna 'Estado_Freshdesk_Clarity' no se creó correctamente")

        if errores:
            for error in errores:
                print(error)
            return False
        
        print("✅ Estructura de archivos verificada correctamente")
        
        # Verificar compatibilidad de IDs
        ids_freshdesk = set(df_freshdesk['Ticket ID'].astype(str))
        ids_clarity = set(df_clarity['ID'].astype(str))
        coincidencias = ids_freshdesk.intersection(ids_clarity)
        print(f"🔍 Coincidencias de IDs: {len(coincidencias)} tickets")
        print(f"🔍 Solo en Freshdesk: {len(ids_freshdesk - ids_clarity)}")
        print(f"🔍 Solo en Clarity: {len(ids_clarity - ids_freshdesk)}")
        
        return True

    def analizar_estados_archivos(self, df_freshdesk, df_clarity):
        """🎯 ANÁLISIS ACTUALIZADO: Mostrar estados de 'Estado_Freshdesk_Clarity'"""
        analisis = {
            'freshdesk': {
                'total_tickets': len(df_freshdesk),
                'estados': df_freshdesk['Estado'].value_counts().to_dict(),
                'estados_no_mapeados': []
            },
            'clarity': {
                'total_tickets': len(df_clarity),
                'estados': df_clarity['Estado_Freshdesk_Clarity'].value_counts().to_dict()  # 🎯 Usar Estado_Freshdesk_Clarity
            },
            'coincidencias': 0,
            'tickets_sin_coincidencia': 0
        }
        
        # 🎯 IDENTIFICAR ESTADOS NO MAPEADOS CON MAPEO EXACTO
        estados_freshdesk = df_freshdesk['Estado'].unique()
        for estado in estados_freshdesk:
            estado_mapeado = self.mapeo_estados_exacto.get(estado)
            if not estado_mapeado:
                analisis['freshdesk']['estados_no_mapeados'].append(estado)
        
        # Contar coincidencias
        tickets_freshdesk = set(df_freshdesk['Ticket ID'].astype(str))
        tickets_clarity = set(df_clarity['ID'].astype(str))
        analisis['coincidencias'] = len(tickets_freshdesk.intersection(tickets_clarity))
        analisis['tickets_sin_coincidencia'] = len(tickets_freshdesk - tickets_clarity)
        
        return analisis

    def mostrar_analisis_estados(self, analisis):
        """🎯 MUESTRA MAPEO EXACTO"""
        print(f"📈 TOTAL TICKETS:")
        print(f"   Freshdesk: {analisis['freshdesk']['total_tickets']}")
        print(f"   Clarity: {analisis['clarity']['total_tickets']}")
        print(f"   Coincidencias: {analisis['coincidencias']}")
        print(f"   Tickets sin coincidencia: {analisis['tickets_sin_coincidencia']}")
        
        print(f"\n📊 DISTRIBUCIÓN DE ESTADOS FRESHDESK:")
        for estado, cantidad in analisis['freshdesk']['estados'].items():
            estado_mapeado = self.mapeo_estados_exacto.get(estado) or "❌ NO MAPEADO"
            print(f"   {estado}: {cantidad} → {estado_mapeado}")
        
        print(f"\n📊 DISTRIBUCIÓN DE 'ESTADO FRESHDESK' EN CLARITY:")
        for estado, cantidad in analisis['clarity']['estados'].items():
            print(f"   {estado}: {cantidad}")
        
        if analisis['freshdesk']['estados_no_mapeados']:
            print(f"\n⚠️  ESTADOS NO MAPEADOS EN FRESHDESK:")
            for estado in analisis['freshdesk']['estados_no_mapeados']:
                print(f"   ❌ {estado}")

    def mostrar_analisis_estados(self, analisis):
        """🎯 MUESTRA MAPEO EXACTO"""
        print(f"📈 TOTAL TICKETS:")
        print(f"   Freshdesk: {analisis['freshdesk']['total_tickets']}")
        print(f"   Clarity: {analisis['clarity']['total_tickets']}")
        print(f"   Coincidencias: {analisis['coincidencias']}")
        print(f"   Tickets sin coincidencia: {analisis['tickets_sin_coincidencia']}")
        
        print(f"\n📊 DISTRIBUCIÓN DE ESTADOS FRESHDESK:")
        for estado, cantidad in analisis['freshdesk']['estados'].items():
            # 🎯 USAR MAPEO EXACTO
            estado_mapeado = self._obtener_estado_mapeado(estado) or "❌ NO MAPEADO"
            print(f"   {estado}: {cantidad} → {estado_mapeado}")
        
        if analisis['freshdesk']['estados_no_mapeados']:
            print(f"\n⚠️  ESTADOS NO MAPEADOS EN FRESHDESK:")
            for estado in analisis['freshdesk']['estados_no_mapeados']:
                print(f"   ❌ {estado}")

    def _comparar_estados_locales(self, df_freshdesk, df_clarity):
        """🎯 COMPARACIÓN CON BARRA DE PROGRESO"""
        diferencias = []
        total_tickets = len(df_freshdesk)
        
        print(f"🔍 Comparando {total_tickets} tickets...")
        
        for index, ticket_fd in df_freshdesk.iterrows():
            current = index + 1
            
            # Actualizar progreso cada 50 tickets
            if current % 50 == 0 or current == total_tickets:
                self._mostrar_progreso_fase(
                    fase_actual=4, 
                    total_fases=4, 
                    mensaje="Comparando estados",
                    current=current,
                    total=total_tickets,
                    diferencias=len(diferencias)
                )
                
            ticket_id = str(ticket_fd['Ticket ID'])
            estado_fd_original = ticket_fd['Estado']
            
            # 🎯 MAPEO DIRECTO
            estado_clarity_propuesto = self.mapeo_estados_exacto.get(estado_fd_original)
            if not estado_clarity_propuesto:
                continue

            # Buscar en Clarity
            ticket_clarity = df_clarity[df_clarity['ID'].astype(str) == ticket_id]
            if ticket_clarity.empty:
                continue
                
            ticket_clarity = ticket_clarity.iloc[0]
            estado_clarity_actual = ticket_clarity['Estado_Freshdesk_Clarity']
            
            if estado_clarity_actual != estado_clarity_propuesto:
                diferencias.append({
                    'ticket_id': ticket_id,
                    'freshdesk_estado': estado_fd_original,
                    'clarity_estado_actual': estado_clarity_actual,
                    'clarity_estado_propuesto': estado_clarity_propuesto
                })
        
        # Limpiar y mostrar resultado final
        display.clear_line()
        print(f"\r✅ Comparación local completada: {len(diferencias)} diferencias encontradas")
        
        return diferencias
    
    def _obtener_ids_para_diferencias(self, diferencias_locales):
        """🎯 Obtener IDs de Clarity CON BARRA DE PROGRESO"""
        if not diferencias_locales:
            return []
            
        print(f"🔍 Obteniendo IDs de Clarity para {len(diferencias_locales)} tickets...")
        
        diferencias_completas = []
        tickets_encontrados = 0
        
        for i, diff in enumerate(diferencias_locales, 1):
            if i % 10 == 0 or i == len(diferencias_locales):
                display.update_progress(
                    current=i,
                    total=len(diferencias_locales),
                    prefix="🔍 Buscando IDs Clarity:",
                    suffix=f"| Encontrados: {tickets_encontrados}"
                )
            
            ticket_id = diff['ticket_id']
            
            # 🎯 BÚSQUEDA DIRECTA
            ticket_clarity = self.clarity_service.obtener_ticket_por_codigo_directo(ticket_id)
            
            if ticket_clarity:
                investment_id = ticket_clarity.get('_parentId')
                internal_id = ticket_clarity.get('_internalId')
                
                if investment_id and internal_id:
                    diff_completo = diff.copy()
                    diff_completo['investment_id'] = investment_id
                    diff_completo['clarity_internal_id'] = internal_id
                    diferencias_completas.append(diff_completo)
                    tickets_encontrados += 1
        
        # Reporte de resultados
        display.clear_line()
        print(f"\r✅ IDs obtenidos: {tickets_encontrados}/{len(diferencias_locales)} tickets")
        
        return diferencias_completas

    def _obtener_estado_mapeado(self, estado_original):
        """🎯 USAR FUNCIÓN HELPER UNIFICADA"""
        return mapear_estado_desde_texto(estado_original)

    def _normalizar_texto(self, texto):
        """🚀 NORMALIZACIÓN CONSISTENTE: maneja acentos, mayúsculas y espacios"""
        if pd.isna(texto):
            return ""
        
        # Convertir a string y limpiar
        texto_str = str(texto).strip().lower()
        
        # Eliminar acentos y caracteres especiales
        texto_str = unicodedata.normalize('NFKD', texto_str)
        texto_str = ''.join([c for c in texto_str if not unicodedata.combining(c)])
        
        # Eliminar espacios múltiples y caracteres especiales
        texto_str = ' '.join(texto_str.split())
        texto_str = texto_str.replace('-', ' ').replace('_', ' ')
        
        return texto_str

    def obtener_ids_clarity_por_lote_directo(self, tickets_ids):
        """Obtener investment_id e internal_id usando búsqueda directa por ticket"""
        if not tickets_ids:
            return {}
            
        print(f"   🔍 Buscando {len(tickets_ids)} tickets en Clarity (BÚSQUEDA DIRECTA)...")
        
        ids_requeridos = {}
        tickets_encontrados = 0
        tickets_no_encontrados = []
        
        for i, ticket_id in enumerate(tickets_ids, 1):
            if i % 100 == 0:
                print(f"      Procesados {i}/{len(tickets_ids)} tickets...")
            
            # ¡BÚSQUEDA DIRECTA! - No necesita obtener todos los tickets
            ticket_clarity = self.clarity_service.obtener_ticket_por_codigo_directo(ticket_id)
            if ticket_clarity:
                investment_id = ticket_clarity.get('_parentId')
                internal_id = ticket_clarity.get('_internalId')
                
                if investment_id and internal_id:
                    ids_requeridos[ticket_id] = {
                        'investment_id': investment_id,
                        'internal_id': internal_id
                    }
                    tickets_encontrados += 1
                else:
                    tickets_no_encontrados.append(ticket_id)
            else:
                tickets_no_encontrados.append(ticket_id)
        
        # Reporte de resultados
        print(f"   ✅ Tickets encontrados en Clarity: {tickets_encontrados}")
        if tickets_no_encontrados:
            print(f"   ⚠️  Tickets no encontrados: {len(tickets_no_encontrados)}")
            if len(tickets_no_encontrados) <= 10:
                print(f"      {', '.join(tickets_no_encontrados[:10])}")
        
        return ids_requeridos

    def mostrar_resumen_detallado(self, diferencias):
        """🚀 OPTIMIZADO: Eliminada normalización redundante"""
        print(f"🔄 SE ENCONTRARON {len(diferencias)} TICKETS CON DIFERENCIAS")
        print("═" * 80)
        
        # Agrupar cambios por tipo
        cambios_reales = {}
        for diff in diferencias:
            clave = f"{diff['clarity_estado_actual']} → {diff['clarity_estado_propuesto']}"
            cambios_reales[clave] = cambios_reales.get(clave, []) + [diff['ticket_id']]
        
        # Ordenamiento
        print("\n📊 OPCIONES DE ORDENAMIENTO:")
        print("1. 🔢 Por cantidad (mayor a menor)")
        print("2. 🔄 Por estado actual (alfabético)") 
        print("3. 🎯 Por estado propuesto (alfabético)")
        
        opcion_orden = input("\nSeleccione ordenamiento (1-3, Enter=1): ").strip()
        
        if opcion_orden == "2":
            cambios_ordenados = sorted(cambios_reales.items(), key=lambda x: x[0].split(' → ')[0])
            print("📋 CAMBIOS (ordenado por estado actual):")
        elif opcion_orden == "3":
            cambios_ordenados = sorted(cambios_reales.items(), key=lambda x: x[0].split(' → ')[1])
            print("📋 CAMBIOS (ordenado por estado propuesto):")
        else:
            cambios_ordenados = sorted(cambios_reales.items(), key=lambda x: len(x[1]), reverse=True)
            print("📋 CAMBIOS (ordenado por cantidad):")
        
        # Mostrar distribución
        for tipo, tickets in cambios_ordenados:
            print(f"   {tipo}: {len(tickets)} tickets")
        
        # Mostrar detalle
        print(f"\n📝 DETALLE (primeros 20 tickets):")
        print("─" * 80)
        print(f"{'TICKET ID':<12} {'ESTADO ACTUAL':<25} {'ESTADO PROPUESTO':<25}")
        print("─" * 80)
        
        diferencias_ordenadas = sorted(diferencias, key=lambda x: x['ticket_id'])
        
        for diff in diferencias_ordenadas[:20]:
            print(f"{diff['ticket_id']:<12} {diff['clarity_estado_actual']:<25} {diff['clarity_estado_propuesto']:<25}")
        
        if len(diferencias) > 20:
            print(f"... y {len(diferencias) - 20} tickets más")
        
        print("─" * 80)

    def aplicar_cambios_clarity(self, diferencias):
        """🎯 MEJORADO: Captura detalles completos de cada actualización"""
        resultado = {
            'exitos': 0,
            'fallos': 0,
            'detalles': []  # 🎯 NUEVO: Lista con detalles completos de cada operación
        }
        
        for i, diff in enumerate(diferencias, 1):
            print(f"\n[{i}/{len(diferencias)}] Actualizando ticket {diff['ticket_id']}...")
            print(f"   Cambio: {diff['clarity_estado_actual']} → {diff['clarity_estado_propuesto']}")

            try:
                # 🎯 INTENTAR ACTUALIZACIÓN
                exito = self.clarity_service.actualizar_estado_ticket(
                    diff['investment_id'], 
                    diff['clarity_internal_id'], 
                    diff['clarity_estado_propuesto']
                )
                
                if exito:
                    print("   ✅ ACTUALIZACIÓN EXITOSA")
                    resultado['exitos'] += 1
                    # 🎯 GUARDAR DETALLE EXITOSO
                    resultado['detalles'].append({
                        'ticket_id': diff['ticket_id'],
                        'estado_actual': diff['clarity_estado_actual'],
                        'estado_propuesto': diff['clarity_estado_propuesto'],
                        'estado_freshdesk_original': diff['freshdesk_estado'],
                        'resultado': 'Éxito',
                        'error': None,
                        'investment_id': diff['investment_id'],
                        'internal_id': diff['clarity_internal_id']
                    })
                else:
                    print("   ❌ ERROR EN LA ACTUALIZACIÓN")
                    resultado['fallos'] += 1
                    # 🎯 GUARDAR DETALLE CON ERROR
                    resultado['detalles'].append({
                        'ticket_id': diff['ticket_id'],
                        'estado_actual': diff['clarity_estado_actual'],
                        'estado_propuesto': diff['clarity_estado_propuesto'],
                        'estado_freshdesk_original': diff['freshdesk_estado'],
                        'resultado': 'Error',
                        'error': 'Error general en la actualización - API retornó False',
                        'investment_id': diff['investment_id'],
                        'internal_id': diff['clarity_internal_id']
                    })
                    
            except Exception as e:
                print(f"   ❌ ERROR EXCEPCIÓN: {str(e)}")
                resultado['fallos'] += 1
                # 🎯 GUARDAR DETALLE CON EXCEPCIÓN
                resultado['detalles'].append({
                    'ticket_id': diff['ticket_id'],
                    'estado_actual': diff['clarity_estado_actual'],
                    'estado_propuesto': diff['clarity_estado_propuesto'],
                    'estado_freshdesk_original': diff['freshdesk_estado'],
                    'resultado': 'Error',
                    'error': f"Excepción: {str(e)}",
                    'investment_id': diff['investment_id'],
                    'internal_id': diff['clarity_internal_id']
                })
        
        return resultado

    def mostrar_reporte_final(self, resultado, diferencias):
        """🎯 MEJORADO: Incluir opción para descargar resultados"""
        print("\n" + "═" * 80)
        print("🎉 REPORTE FINAL DE SINCRONIZACIÓN")
        print("═" * 80)
        
        print(f"📊 RESUMEN EJECUTIVO:")
        print(f"   ✅ Actualizaciones exitosas: {resultado['exitos']}")
        print(f"   ❌ Actualizaciones fallidas: {resultado['fallos']}")
        print(f"   📋 Total de cambios identificados: {len(diferencias)}")
        
        # 🎯 OBTENER TICKETS EXITOSOS Y FALLIDOS
        tickets_exitosos = [d['ticket_id'] for d in resultado['detalles'] if d['resultado'] == 'Éxito']
        tickets_fallidos = [d['ticket_id'] for d in resultado['detalles'] if d['resultado'] == 'Error']
        
        if tickets_exitosos:
            print(f"\n🎯 TICKETS ACTUALIZADOS EXITOSAMENTE ({len(tickets_exitosos)}):")
            print("   " + ", ".join(tickets_exitosos[:10]))
            if len(tickets_exitosos) > 10:
                print(f"   ... y {len(tickets_exitosos) - 10} más")
        
        if tickets_fallidos:
            print(f"\n🚫 TICKETS CON ERRORES ({len(tickets_fallidos)}):")
            # 🎯 MOSTRAR PRIMEROS 5 ERRORES CON DETALLE
            errores_detallados = [d for d in resultado['detalles'] if d['resultado'] == 'Error']
            for error in errores_detallados[:5]:
                print(f"   ❌ Ticket {error['ticket_id']}: {error['error']}")
            if len(errores_detallados) > 5:
                print(f"   ... y {len(errores_detallados) - 5} errores más")
        
        # 🎯 ESTADÍSTICAS DE CAMBIOS APLICADOS
        if tickets_exitosos:
            cambios_aplicados = {}
            for detalle in resultado['detalles']:
                if detalle['resultado'] == 'Éxito':
                    clave = f"{detalle['estado_actual']} → {detalle['estado_propuesto']}"
                    cambios_aplicados[clave] = cambios_aplicados.get(clave, 0) + 1
            
            print(f"\n📈 ESTADÍSTICAS DE CAMBIOS APLICADOS:")
            for cambio, cantidad in cambios_aplicados.items():
                print(f"   {cambio}: {cantidad} tickets")
        
        print(f"\n⏰ Hora de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 80)
        
        # 🎯 NUEVA OPCIÓN: DESCARGAR REPORTE DE RESULTADOS
        if resultado['detalles']:
            print("\n📊 ¿DESEA DESCARGAR EL REPORTE DETALLADO DE RESULTADOS?")
            print("═" * 50)
            print("1. ✅ Sí, descargar Excel con resultados completos")
            print("2. ❌ No, finalizar proceso")
            print("═" * 50)
            
            opcion = input("\nSeleccione una opción (1-2): ").strip()
            
            if opcion == "1":
                if self._descargar_excel_resultados(resultado):
                    print("🎉 Proceso completado exitosamente")
                else:
                    print("⚠️  Proceso completado con errores en la descarga")
            else:
                print("👋 Proceso finalizado")

    def _mostrar_progreso_fase(self, fase_actual, total_fases, mensaje, current=0, total=0, diferencias=0):
        """Mostrar progreso de una fase específica"""
        display.clear_line()
        if total > 0:
            # Con barra de progreso
            display.update_progress(
                current=current,
                total=total,
                prefix=f"Fase {fase_actual}/{total_fases}: {mensaje}",
                suffix=f"| Diferencias: {diferencias}"
            )
        else:
            # Solo mensaje
            print(f"\r🔄 Fase {fase_actual}/{total_fases}: {mensaje}", end="", flush=True)