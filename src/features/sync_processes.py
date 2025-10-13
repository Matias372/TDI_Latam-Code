import pandas as pd
import os
from services.freshdesk_service import FreshdeskService
from services.clarity_service import ClarityService
from utils.file_utils import FileUtils
from datetime import datetime
import unicodedata

class SyncProcess:
    def __init__(self, config_manager):
        self.config = config_manager
        self.freshdesk_service = FreshdeskService(config_manager)
        self.clarity_service = ClarityService(config_manager)
        
        # 🎯 MAPEO EXACTO BASADO EN LOS VALORES REALES DE LOS ARCHIVOS
        # Freshdesk -> Clarity
        self.mapeo_estados_exacto = {
            # Estados de Freshdesk -> Estados de Clarity
            "Closed": "Cerrada",
            "Derivado al Fabricante": "Derivado al Fabricante",
            "En evaluación": "En evaluación", 
            "En progreso": "En progreso",
            "Esperando al cliente": "Esperando al cliente",
            "Open": "Abierta",
            "Resolved": "Resuelto"
        }

    def sincronizar_estados(self):
        """Proceso principal de sincronización desde archivos Excel/CSV"""
        print("🚀 INICIANDO SINCRONIZACIÓN DESDE ARCHIVOS EXCEL/CSV")
        print("═" * 60)
        
        if not self.config.validar_configuracion_clarity():
            print("❌ Configuración de Clarity incompleta. Use el menú de configuración primero.")
            return False

        # 1. Cargar archivo de Freshdesk
        print("\n📁 CARGANDO ARCHIVO DE FRESHDESK")
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
        print("\n📁 CARGANDO ARCHIVO DE CLARITY")
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

        # 3. Verificación de estructura de archivos CORREGIDA
        print("\n🔍 VERIFICANDO ESTRUCTURA DE ARCHIVOS")
        print("-" * 40)
        if not self.verificar_estructura_archivos(df_freshdesk, df_clarity):
            return False

        print(f"✅ Archivo Freshdesk cargado: {len(df_freshdesk)} tickets")
        print(f"✅ Archivo Clarity cargado: {len(df_clarity)} tickets")

        # 4. Análisis de estados y comparación LOCAL
        print("\n📊 ANALIZANDO ESTADOS Y BUSCANDO DIFERENCIAS")
        print("-" * 40)
        analisis_estados = self.analizar_estados_archivos(df_freshdesk, df_clarity)
        self.mostrar_analisis_estados(analisis_estados)
        
        # 🎯 COMPARACIÓN SOLO LOCAL - CON COLUMNA CORRECTA
        diferencias_locales = self._comparar_estados_locales(df_freshdesk, df_clarity)
        
        if not diferencias_locales:
            print("🎉 No se encontraron diferencias entre Freshdesk y Clarity")
            return True

        # 5. 🎯 SOLO AHORA buscar IDs en Clarity para tickets con diferencias REALES
        print(f"\n📥 BUSCANDO IDs EN CLARITY PARA {len(diferencias_locales)} TICKETS CON DIFERENCIAS REALES")
        print("-" * 50)
        diferencias_completas = self._obtener_ids_para_diferencias(diferencias_locales)
        
        if not diferencias_completas:
            print("❌ No se pudieron obtener los IDs de Clarity para los tickets con diferencias")
            return False

        # 6. Mostrar resumen detallado de cambios
        print("\n📋 RESUMEN DETALLADO DE CAMBIOS")
        print("═" * 80)
        self.mostrar_resumen_detallado(diferencias_completas)

        # 7. 🎯 SISTEMA DE CONFIRMACIÓN CON OPCIONES
        while True:
            print("\n⚠️  CONFIRMACIÓN REQUERIDA")
            print("═" * 50)
            print("Opciones disponibles:")
            print("1. ✅ Aplicar cambios en Clarity")
            print("2. 📥 Descargar Excel con lista completa de cambios")
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
        
        # 9. Reporte final
        self.mostrar_reporte_final(resultado, diferencias_completas)
        
        return resultado['exitos'] > 0 or resultado['fallos'] == 0
        

    def _buscar_columna_flexible(self, df, palabras_clave):
        """🚀 MÉTODO REUTILIZABLE: Búsqueda flexible de columnas"""
        columnas = df.columns.tolist()
        for col in columnas:
            col_lower = col.lower()
            for palabra in palabras_clave:
                if palabra in col_lower:
                    return col
        return None

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
        """🎯 COMPARACIÓN CORREGIDA: Usar 'Estado_Freshdesk_Clarity'"""
        diferencias = []
        
        print(f"🔍 COMPARANDO {len(df_freshdesk)} TICKETS LOCALMENTE...")
        print(f"   🎯 Comparando 'Estado' de Freshdesk vs 'Estado_Freshdesk_Clarity' de Clarity")
        
        tickets_procesados = 0
        tickets_con_diferencias = 0
        tickets_sin_mapeo = 0
        tickets_no_encontrados = 0
        
        for index, ticket_fd in df_freshdesk.iterrows():
            tickets_procesados += 1
            if tickets_procesados % 1000 == 0:
                print(f"   📊 Procesados {tickets_procesados}/{len(df_freshdesk)} tickets...")
                
            ticket_id = str(ticket_fd['Ticket ID'])
            estado_fd_original = ticket_fd['Estado']
            
            # 🎯 MAPEO DIRECTO SIN NORMALIZACIÓN
            estado_clarity_propuesto = self.mapeo_estados_exacto.get(estado_fd_original)
            if not estado_clarity_propuesto:
                tickets_sin_mapeo += 1
                continue  # Saltar estados no mapeados

            # Buscar en Clarity (localmente en el DataFrame)
            ticket_clarity = df_clarity[df_clarity['ID'].astype(str) == ticket_id]
            if ticket_clarity.empty:
                tickets_no_encontrados += 1
                continue  # Ticket no existe en Clarity
                
            ticket_clarity = ticket_clarity.iloc[0]
            estado_clarity_actual = ticket_clarity['Estado_Freshdesk_Clarity']
            
            # 🎯 COMPARACIÓN DIRECTA - SIN NORMALIZACIÓN
            if estado_clarity_actual != estado_clarity_propuesto:
                diferencias.append({
                    'ticket_id': ticket_id,
                    'freshdesk_estado': estado_fd_original,
                    'clarity_estado_actual': estado_clarity_actual,
                    'clarity_estado_propuesto': estado_clarity_propuesto
                })
                tickets_con_diferencias += 1
        
        print(f"✅ Comparación local completada:")
        print(f"   📋 Tickets procesados: {tickets_procesados}")
        print(f"   🔍 Diferencias encontradas: {tickets_con_diferencias}")
        print(f"   ❌ Tickets sin mapeo: {tickets_sin_mapeo}")
        print(f"   ❌ Tickets no encontrados en Clarity: {tickets_no_encontrados}")
        print(f"   ✅ Tickets sin diferencias: {tickets_procesados - tickets_con_diferencias - tickets_sin_mapeo - tickets_no_encontrados}")
        
        # 🎯 DEBUG: Mostrar distribución de diferencias
        if diferencias:
            print(f"\n🔍 DISTRIBUCIÓN DE DIFERENCIAS (Estado_Freshdesk):")
            cambios_tipos = {}
            for diff in diferencias:
                clave = f"{diff['clarity_estado_actual']} -> {diff['clarity_estado_propuesto']}"
                cambios_tipos[clave] = cambios_tipos.get(clave, 0) + 1
            
            # Mostrar solo los top 10 cambios
            for cambio, cantidad in sorted(cambios_tipos.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   {cambio}: {cantidad} tickets")
        
        return diferencias
    
    def _obtener_ids_para_diferencias(self, diferencias_locales):
        """🎯 Obtener IDs de Clarity SOLO para tickets con diferencias REALES"""
        if not diferencias_locales:
            return []
            
        print(f"🔍 Obteniendo IDs de Clarity para {len(diferencias_locales)} tickets con diferencias REALES...")
        
        diferencias_completas = []
        tickets_encontrados = 0
        tickets_no_encontrados = []
        
        for i, diff in enumerate(diferencias_locales, 1):
            if i % 50 == 0:
                print(f"   Procesados {i}/{len(diferencias_locales)} tickets...")
            
            ticket_id = diff['ticket_id']
            
            # 🎯 BÚSQUEDA DIRECTA SOLO PARA ESTE TICKET
            ticket_clarity = self.clarity_service.obtener_ticket_por_codigo_directo(ticket_id)
            
            if ticket_clarity:
                investment_id = ticket_clarity.get('_parentId')
                internal_id = ticket_clarity.get('_internalId')
                
                if investment_id and internal_id:
                    # Combinar información local con IDs de Clarity
                    diff_completo = diff.copy()
                    diff_completo['investment_id'] = investment_id
                    diff_completo['clarity_internal_id'] = internal_id
                    diferencias_completas.append(diff_completo)
                    tickets_encontrados += 1
                else:
                    tickets_no_encontrados.append(ticket_id)
            else:
                tickets_no_encontrados.append(ticket_id)
        
        # Reporte de resultados
        print(f"✅ Tickets encontrados en Clarity: {tickets_encontrados}")
        if tickets_no_encontrados:
            print(f"⚠️  Tickets no encontrados en Clarity: {len(tickets_no_encontrados)}")
            if len(tickets_no_encontrados) <= 10:
                print(f"   {', '.join(tickets_no_encontrados)}")
        
        return diferencias_completas

    # 🚀 MÉTODOS DE NORMALIZACIÓN (se mantienen igual)
    def _obtener_estado_mapeado(self, estado_original):
        """🎯 MAPEO SIMPLE: Directo sin normalización"""
        return self.mapeo_estados_exacto.get(estado_original)

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
        """Aplicar cambios en Clarity con seguimiento detallado"""
        resultado = {
            'exitos': 0,
            'fallos': 0,
            'tickets_exitosos': [],
            'tickets_fallidos': [],
            'errores_detallados': []
        }
        
        for i, diff in enumerate(diferencias, 1):
            print(f"\n[{i}/{len(diferencias)}] Actualizando ticket {diff['ticket_id']}...")
            print(f"   Cambio: {diff['clarity_estado_actual']} → {diff['clarity_estado_propuesto']}")

            try:
                if self.clarity_service.actualizar_estado_ticket(
                    diff['investment_id'], 
                    diff['clarity_internal_id'], 
                    diff['clarity_estado_propuesto']
                ):
                    print("   ✅ ACTUALIZACIÓN EXITOSA")
                    resultado['exitos'] += 1
                    resultado['tickets_exitosos'].append(diff['ticket_id'])
                else:
                    print("   ❌ ERROR EN LA ACTUALIZACIÓN")
                    resultado['fallos'] += 1
                    resultado['tickets_fallidos'].append(diff['ticket_id'])
                    resultado['errores_detallados'].append({
                        'ticket_id': diff['ticket_id'],
                        'error': 'Error general en la actualización'
                    })
            except Exception as e:
                print(f"   ❌ ERROR EXCEPCIÓN: {str(e)}")
                resultado['fallos'] += 1
                resultado['tickets_fallidos'].append(diff['ticket_id'])
                resultado['errores_detallados'].append({
                    'ticket_id': diff['ticket_id'],
                    'error': str(e)
                })
        
        return resultado

    def mostrar_reporte_final(self, resultado, diferencias):
        """Mostrar reporte final detallado"""
        print("\n" + "═" * 80)
        print("🎉 REPORTE FINAL DE SINCRONIZACIÓN")
        print("═" * 80)
        
        print(f"📊 RESUMEN EJECUTIVO:")
        print(f"   ✅ Actualizaciones exitosas: {resultado['exitos']}")
        print(f"   ❌ Actualizaciones fallidas: {resultado['fallos']}")
        print(f"   📋 Total de cambios identificados: {len(diferencias)}")
        
        if resultado['exitos'] > 0:
            print(f"\n🎯 TICKETS ACTUALIZADOS EXITOSAMENTE ({resultado['exitos']}):")
            print("   " + ", ".join(resultado['tickets_exitosos'][:10]))
            if len(resultado['tickets_exitosos']) > 10:
                print(f"   ... y {len(resultado['tickets_exitosos']) - 10} más")
        
        if resultado['fallos'] > 0:
            print(f"\n🚫 TICKETS CON ERRORES ({resultado['fallos']}):")
            for error in resultado['errores_detallados'][:5]:
                print(f"   ❌ Ticket {error['ticket_id']}: {error['error']}")
            if len(resultado['errores_detallados']) > 5:
                print(f"   ... y {len(resultado['errores_detallados']) - 5} errores más")
        
        # Estadísticas de cambios aplicados
        if resultado['exitos'] > 0:
            cambios_aplicados = {}
            for diff in diferencias:
                if diff['ticket_id'] in resultado['tickets_exitosos']:
                    clave = f"{diff['clarity_estado_actual']} → {diff['clarity_estado_propuesto']}"
                    cambios_aplicados[clave] = cambios_aplicados.get(clave, 0) + 1
            
            print(f"\n📈 ESTADÍSTICAS DE CAMBIOS APLICADOS:")
            for cambio, cantidad in cambios_aplicados.items():
                print(f"   {cambio}: {cantidad} tickets")
        
        print(f"\n⏰ Hora de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 80)