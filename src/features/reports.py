import pandas as pd
import os
from datetime import datetime
from services.freshdesk_service import FreshdeskService
from utils.file_utils import FileUtils

class Reports:
    def __init__(self, freshdesk_service):
        self.service = freshdesk_service

    def _obtener_ruta_descargas(self):
        """Obtiene la ruta de la carpeta de Descargas del usuario actual"""
        # Para Windows
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes, windll
            
            # Usar SHGetFolderPath para obtener la carpeta Downloads
            CSIDL_PERSONAL = 5  # My Documents
            SHGFP_TYPE_CURRENT = 0
            
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
            
            # En Windows, Downloads está dentro de Documents
            downloads_path = os.path.join(buf.value, "Downloads")
        else:
            # Para Linux/Mac
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Crear la carpeta si no existe
        os.makedirs(downloads_path, exist_ok=True)
        return downloads_path

    def _guardar_en_descargas(self, df, nombre_archivo):
        """Guarda un DataFrame en la carpeta de Descargas"""
        ruta_descargas = self._obtener_ruta_descargas()
        ruta_completa = os.path.join(ruta_descargas, nombre_archivo)
        
        try:
            df.to_excel(ruta_completa, index=False)
            print(f"📁 Archivo guardado en: {ruta_completa}")
            return ruta_completa
        except Exception as e:
            print(f"❌ Error al guardar el archivo: {str(e)}")
            # Fallback: guardar en la carpeta output original
            return FileUtils.guardar_excel(df, nombre_archivo)

    def reporte_tickets_sin_etiquetas(self):
        """Generar reporte de tickets sin etiquetas"""
        print("\n=== Generando reporte de tickets sin etiquetas ===")

        tickets_sin_etiquetas = []
        pagina = 1

        while True:
            tickets = self.service.obtener_tickets_paginados(pagina)
            if not tickets:
                break

            for ticket in tickets:
                etiquetas = ticket.get("tags")
                if not etiquetas:  # None o lista vacía
                    tickets_sin_etiquetas.append({
                        "ID": ticket.get("id"),
                        "Asunto": ticket.get("subject"),
                        "Estado": ticket.get("status"),
                        "Prioridad": ticket.get("priority"),
                        "URL": f"{self.service.config.freshdesk_domain}/a/tickets/{ticket.get('id')}"
                    })

            pagina += 1
            if len(tickets) < 100:  # Última página
                break

        if not tickets_sin_etiquetas:
            print("✅ Todos los tickets tienen al menos una etiqueta.")
            return

        # Crear DataFrame y guardar en Descargas
        df = pd.DataFrame(tickets_sin_etiquetas)
        nombre_archivo = f"Reporte_Tickets_Sin_Etiquetas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self._guardar_en_descargas(df, nombre_archivo)
        print(f"✅ Reporte generado con {len(tickets_sin_etiquetas)} tickets sin etiquetas.")

    def reporte_empresas(self):
        """Generar reporte de empresas"""
        print("\n=== Generando reporte de empresas ===")
        
        empresas = self.service.obtener_empresas()
        if not empresas:
            print("❌ No se pudieron obtener las empresas.")
            return

        datos_empresas = []
        for empresa in empresas:
            datos_empresas.append({
                "ID": empresa.get("id"),
                "Nombre": empresa.get("name"),
                "Dominio": empresa.get("domains", [""])[0] if empresa.get("domains") else "",
                "Creado": empresa.get("created_at")
            })

        df = pd.DataFrame(datos_empresas)
        nombre_archivo = f"Reporte_Empresas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self._guardar_en_descargas(df, nombre_archivo)
        print(f"✅ Reporte generado con {len(datos_empresas)} empresas.")
    
    def reporte_productos_diferentes(self):
        """Generar reporte de tickets con productos diferentes entre Freshdesk y Clarity"""
        from utils.display_utils import display  # Importar aquí para evitar circular imports
        
        print("\n=== Generando reporte de productos diferentes ===")
        
        # Cargar archivo de Freshdesk
        print("\n📁 Seleccione el archivo de Freshdesk (Excel):")
        from utils.file_utils import FileUtils
        ruta_freshdesk = FileUtils.seleccionar_archivo(
            "Seleccione archivo Freshdesk", 
            [("Excel files", "*.xlsx *.xls")]
        )
        
        if not ruta_freshdesk:
            print("❌ No se seleccionó archivo de Freshdesk.")
            display.press_enter_to_continue()
            return

        df_freshdesk = FileUtils.cargar_excel(ruta_freshdesk)
        if df_freshdesk is None or df_freshdesk.empty:
            print("❌ No se pudo cargar el archivo de Freshdesk.")
            display.press_enter_to_continue()
            return

        # Cargar archivo de Clarity
        print("\n📁 Seleccione el archivo de Clarity (CSV):")
        ruta_clarity = FileUtils.seleccionar_archivo(
            "Seleccione archivo Clarity", 
            [("CSV files", "*.csv")]
        )
        
        if not ruta_clarity:
            print("❌ No se seleccionó archivo de Clarity.")
            display.press_enter_to_continue()
            return

        df_clarity = FileUtils.cargar_csv(ruta_clarity)
        if df_clarity is None or df_clarity.empty:
            print("🔄 La carga automática falló, intentando carga manual...")
            df_clarity = FileUtils.cargar_csv_manual(ruta_clarity)
        
        if df_clarity is None or df_clarity.empty:
            print("❌ No se pudo cargar el archivo de Clarity.")
            display.press_enter_to_continue()
            return

        # Verificar estructura de archivos
        if not self._verificar_estructura_productos(df_freshdesk, df_clarity):
            display.press_enter_to_continue()
            return

        # Procesar y comparar productos
        productos_diferentes = self._comparar_productos(df_freshdesk, df_clarity)
        
        if not productos_diferentes:
            print("🎉 No se encontraron tickets con productos diferentes.")
            display.press_enter_to_continue()
            return

        # Crear y guardar reporte
        self._guardar_reporte_productos(productos_diferentes)
        
        # 🆕 NUEVO: Esperar confirmación del usuario antes de volver al menú
        print(f"\n✅ Reporte generado exitosamente y guardado en la carpeta de Descargas")
        print("💡 Presione Enter para volver al menú de reportes...")
        input()

    def _verificar_estructura_productos(self, df_freshdesk, df_clarity):
        """Verificar que los archivos tengan las columnas necesarias"""
        errores = []
        
        # Verificar Freshdesk
        if 'Ticket ID' not in df_freshdesk.columns:
            errores.append("❌ Freshdesk debe contener 'Ticket ID'")
        
        columna_producto_fd = None
        for col in df_freshdesk.columns:
            if 'seleccione el producto' in col.lower():
                columna_producto_fd = col
                break
        
        if not columna_producto_fd:
            errores.append("❌ No se encontró columna 'Seleccione el producto' en Freshdesk")
        else:
            print(f"✅ Columna producto Freshdesk: '{columna_producto_fd}'")

        # Verificar Clarity
        columna_id_clarity = None
        columna_producto_clarity = None
        
        for col in df_clarity.columns:
            col_lower = col.lower()
            if 'id' in col_lower and not columna_id_clarity:
                columna_id_clarity = col
            if 'producto tdi' in col_lower:
                columna_producto_clarity = col
        
        if not columna_id_clarity:
            errores.append("❌ No se encontró columna de ID en Clarity")
        else:
            print(f"✅ Columna ID Clarity: '{columna_id_clarity}'")
            # Renombrar para consistencia
            df_clarity.rename(columns={columna_id_clarity: 'ID'}, inplace=True)

        if not columna_producto_clarity:
            errores.append("❌ No se encontró columna 'Producto TDI' en Clarity")
        else:
            print(f"✅ Columna producto Clarity: '{columna_producto_clarity}'")
            df_clarity.rename(columns={columna_producto_clarity: 'Producto_TDI_Clarity'}, inplace=True)

        if errores:
            for error in errores:
                print(error)
            return False
        
        # Renombrar columna de producto en Freshdesk para consistencia
        df_freshdesk.rename(columns={columna_producto_fd: 'Producto_Freshdesk'}, inplace=True)
        
        print("✅ Estructura de archivos verificada correctamente")
        return True

    def _comparar_productos(self, df_freshdesk, df_clarity):
        """Comparar productos entre Freshdesk y Clarity"""
        print("\n🔍 Comparando productos...")
        
        productos_diferentes = []
        total_tickets = len(df_freshdesk)
        coincidencias = 0
        
        for index, ticket_fd in df_freshdesk.iterrows():
            ticket_id = str(ticket_fd['Ticket ID'])
            producto_fd = str(ticket_fd['Producto_Freshdesk']).strip() if pd.notna(ticket_fd['Producto_Freshdesk']) else ""
            
            # Buscar en Clarity
            ticket_clarity = df_clarity[df_clarity['ID'].astype(str) == ticket_id]
            if ticket_clarity.empty:
                continue
                
            ticket_clarity = ticket_clarity.iloc[0]
            producto_clarity = str(ticket_clarity['Producto_TDI_Clarity']).strip() if pd.notna(ticket_clarity['Producto_TDI_Clarity']) else ""
            
            # Comparar productos (case insensitive y ignorando espacios)
            if producto_fd.lower() != producto_clarity.lower():
                productos_diferentes.append({
                    'Ticket_ID': ticket_id,
                    'Producto_Clarity': producto_clarity,
                    'Producto_Freshdesk': producto_fd
                })
            else:
                coincidencias += 1
            
            # Mostrar progreso cada 100 tickets
            if (index + 1) % 100 == 0:
                print(f"   Procesados {index + 1}/{total_tickets} tickets...")
        
        print(f"✅ Comparación completada:")
        print(f"   📊 Tickets con productos diferentes: {len(productos_diferentes)}")
        print(f"   ✅ Tickets con productos iguales: {coincidencias}")
        
        return productos_diferentes

    def _guardar_reporte_productos(self, productos_diferentes):
        """Guardar reporte de productos diferentes"""
        if not productos_diferentes:
            return
        
        # Crear DataFrame
        df_reporte = pd.DataFrame(productos_diferentes)
        
        # Ordenar por Ticket ID
        df_reporte = df_reporte.sort_values('Ticket_ID')
        
        # Guardar en Descargas
        nombre_archivo = f"Reporte_Productos_Diferentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        ruta_guardado = self._guardar_en_descargas(df_reporte, nombre_archivo)
        
        if ruta_guardado:
            print(f"\n🎉 Reporte generado exitosamente!")
            print(f"📁 Archivo: {ruta_guardado}")
            print(f"📊 Total de registros: {len(productos_diferentes)}")
            
            # Mostrar resumen estadístico
            self._mostrar_estadisticas_productos(df_reporte)
        else:
            print("❌ Error al guardar el reporte.")

    def _mostrar_estadisticas_productos(self, df_reporte):
        """Mostrar estadísticas del reporte de productos"""
        print(f"\n📈 ESTADÍSTICAS DEL REPORTE:")
        print("─" * 50)
        
        # Productos más comunes en cada sistema
        productos_fd_comunes = df_reporte['Producto_Freshdesk'].value_counts().head(5)
        productos_clarity_comunes = df_reporte['Producto_Clarity'].value_counts().head(5)
        
        print(f"🔄 TOP 5 PRODUCTOS DIFERENTES - FRESHDESK:")
        for producto, cantidad in productos_fd_comunes.items():
            print(f"   {producto}: {cantidad} tickets")
        
        print(f"\n🔄 TOP 5 PRODUCTOS DIFERENTES - CLARITY:")
        for producto, cantidad in productos_clarity_comunes.items():
            print(f"   {producto}: {cantidad} tickets")
        
        # Tickets sin producto en alguno de los sistemas
        sin_producto_fd = len(df_reporte[df_reporte['Producto_Freshdesk'] == ''])
        sin_producto_clarity = len(df_reporte[df_reporte['Producto_Clarity'] == ''])
        
        print(f"\n📝 RESUMEN:")
        print(f"   🎫 Tickets sin producto en Freshdesk: {sin_producto_fd}")
        print(f"   🎫 Tickets sin producto en Clarity: {sin_producto_clarity}")
        print(f"   📋 Total de discrepancias: {len(df_reporte)}")