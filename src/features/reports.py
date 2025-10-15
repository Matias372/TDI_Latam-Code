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
        """Generar reporte de tickets SIN la etiqueta 'CREATE CLARITY'"""
        from utils.display_utils import display
        
        print("\n=== Generando reporte de tickets SIN etiqueta 'CREATE CLARITY' ===")
        print("⚠️  Este proceso puede tomar varios minutos para 33,500+ tickets...")

        tickets_sin_create_clarity = []
        pagina = 1
        total_tickets_procesados = 0
        pausa_cada_paginas = 10
        
        stats = {
            'con_etiqueta': 0,
            'sin_etiqueta': 0,
            'con_create_clarity': 0,
            'sin_create_clarity': 0
        }

        try:
            while True:
                print(f"📄 Procesando página {pagina}...")
                
                # Obtener tickets con diagnóstico detallado
                tickets = self.service.obtener_tickets_paginados(pagina, por_pagina=100)
                
                # Diagnóstico detallado de la respuesta
                if tickets is None:
                    print(f"❌ La página {pagina} devolvió None. Esto indica un error grave.")
                    break
                    
                if not tickets:
                    print(f"✅ No hay más tickets. Páginas procesadas: {pagina-1}, Total tickets: {total_tickets_procesados}")
                    break

                tickets_en_pagina = len(tickets)
                total_tickets_procesados += tickets_en_pagina
                
                print(f"   🔍 Página {pagina}: {tickets_en_pagina} tickets recibidos")
                
                # Mostrar IDs del primer y último ticket para diagnóstico
                if tickets:
                    primer_id = tickets[0].get('id', 'N/A')
                    ultimo_id = tickets[-1].get('id', 'N/A')
                    print(f"   🔍 IDs: {primer_id} → {ultimo_id}")

                tickets_sin_etiqueta_en_pagina = 0

                for ticket in tickets:
                    etiquetas = ticket.get("tags", [])
                    
                    if etiquetas is None:
                        etiquetas = []
                        stats['sin_etiqueta'] += 1
                    else:
                        stats['con_etiqueta'] += 1
                    
                    tiene_create_clarity = any(
                        tag.upper() == "CREATE CLARITY" 
                        for tag in etiquetas 
                        if tag is not None
                    )
                    
                    if tiene_create_clarity:
                        stats['con_create_clarity'] += 1
                    else:
                        stats['sin_create_clarity'] += 1
                        tickets_sin_etiqueta_en_pagina += 1
                        tickets_sin_create_clarity.append({
                            "ID": ticket.get("id"),
                            "Asunto": ticket.get("subject"),
                            "Estado": ticket.get("status"),
                            "Prioridad": ticket.get("priority"),
                            "Etiquetas": ", ".join(etiquetas) if etiquetas else "Ninguna",
                            "URL": f"{self.service.config.freshdesk_domain}/a/tickets/{ticket.get('id')}"
                        })

                print(f"   📊 Página {pagina}: {tickets_en_pagina} tickets | SIN 'CREATE CLARITY': {tickets_sin_etiqueta_en_pagina}")
                print(f"   📈 Progreso total: {total_tickets_procesados} tickets | Total SIN etiqueta: {len(tickets_sin_create_clarity)}")

                pagina += 1
                
                # Pausa estratégica
                if pagina % pausa_cada_paginas == 0:
                    print(f"⏸️  Pausa de 3 segundos...")
                    import time
                    time.sleep(3)
                
                # Condición de salida por última página
                if tickets_en_pagina < 100:
                    print(f"📭 Última página detectada. Tickets en página: {tickets_en_pagina}")
                    break

                # Límite de seguridad
                if pagina > 400:  # 40,000 tickets máximo
                    print(f"⚠️  Límite de páginas alcanzado: {pagina}")
                    break

        except KeyboardInterrupt:
            print("\n⏹️  Proceso interrumpido por el usuario.")
            
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            import traceback
            traceback.print_exc()

        # Mostrar estadísticas finales
        print(f"\n📈 ESTADÍSTICAS FINALES:")
        print("─" * 50)
        print(f"📊 Total tickets procesados: {total_tickets_procesados}")
        print(f"📄 Total páginas procesadas: {pagina - 1}")
        print(f"✅ Tickets CON etiquetas: {stats['con_etiqueta']}")
        print(f"❌ Tickets SIN etiquetas: {stats['sin_etiqueta']}")
        print(f"🔄 Tickets CON 'CREATE CLARITY': {stats['con_create_clarity']}")
        print(f"🎯 Tickets SIN 'CREATE CLARITY': {stats['sin_create_clarity']}")
        print("─" * 50)

        if not tickets_sin_create_clarity:
            print("🎉 Todos los tickets tienen la etiqueta 'CREATE CLARITY'.")
        else:
            # Crear y guardar reporte
            df = pd.DataFrame(tickets_sin_create_clarity)
            df = df.sort_values('ID')
            
            nombre_archivo = f"Reporte_Tickets_Sin_Create_Clarity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            ruta_guardado = self._guardar_en_descargas(df, nombre_archivo)
            
            if ruta_guardado:
                print(f"✅ Reporte generado con {len(tickets_sin_create_clarity)} tickets SIN 'CREATE CLARITY'.")
                print(f"📁 Archivo: {ruta_guardado}")
                
                # Mostrar muestra
                print(f"\n📋 Muestra de tickets (primeros 5):")
                print("─" * 80)
                for i, ticket in enumerate(tickets_sin_create_clarity[:5]):
                    print(f"   {i+1}. ID: {ticket['ID']} - {ticket['Asunto']}")

        # Pausa final
        print(f"\n💡 Presione Enter para volver al menú de reportes...")
        input()

    def reporte_empresas(self):
        """Generar reporte de empresas"""
        print("\n=== Generando reporte de empresas ===")
        
        try:
            empresas = self.service.obtener_empresas()
            if not empresas:
                print("❌ No se pudieron obtener las empresas.")
                print("\n💡 Presione Enter para volver al menú de reportes...")
                input()
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
            ruta_guardado = self._guardar_en_descargas(df, nombre_archivo)
            
            if ruta_guardado:
                print(f"✅ Reporte generado con {len(datos_empresas)} empresas.")
                print(f"📁 Archivo guardado en: {ruta_guardado}")
            else:
                print("❌ Error al guardar el reporte.")

        except Exception as e:
            print(f"❌ Error inesperado durante la generación del reporte: {str(e)}")
        
        # Pausa final para confirmación
        print(f"\n💡 Presione Enter para volver al menú de reportes...")
        input()
    
    def reporte_productos_diferentes(self):
        """Generar reporte de tickets con productos diferentes entre Freshdesk y Clarity"""
        from utils.display_utils import display  # Importar aquí para evitar circular imports
        
        print("\n=== Generando reporte de productos diferentes ===")
        
        try:
            # Cargar archivo de Freshdesk
            print("\n📁 Seleccione el archivo de Freshdesk (Excel):")
            from utils.file_utils import FileUtils
            ruta_freshdesk = FileUtils.seleccionar_archivo(
                "Seleccione archivo Freshdesk", 
                [("Excel files", "*.xlsx *.xls")]
            )
            
            if not ruta_freshdesk:
                print("❌ No se seleccionó archivo de Freshdesk.")
                print("\n💡 Presione Enter para volver al menú de reportes...")
                input()
                return

            df_freshdesk = FileUtils.cargar_excel(ruta_freshdesk)
            if df_freshdesk is None or df_freshdesk.empty:
                print("❌ No se pudo cargar el archivo de Freshdesk.")
                print("\n💡 Presione Enter para volver al menú de reportes...")
                input()
                return

            # Cargar archivo de Clarity
            print("\n📁 Seleccione el archivo de Clarity (CSV):")
            ruta_clarity = FileUtils.seleccionar_archivo(
                "Seleccione archivo Clarity", 
                [("CSV files", "*.csv")]
            )
            
            if not ruta_clarity:
                print("❌ No se seleccionó archivo de Clarity.")
                print("\n💡 Presione Enter para volver al menú de reportes...")
                input()
                return

            df_clarity = FileUtils.cargar_csv(ruta_clarity)
            if df_clarity is None or df_clarity.empty:
                print("🔄 La carga automática falló, intentando carga manual...")
                df_clarity = FileUtils.cargar_csv_manual(ruta_clarity)
            
            if df_clarity is None or df_clarity.empty:
                print("❌ No se pudo cargar el archivo de Clarity.")
                print("\n💡 Presione Enter para volver al menú de reportes...")
                input()
                return

            # Verificar estructura de archivos
            if not self._verificar_estructura_productos(df_freshdesk, df_clarity):
                print("\n💡 Presione Enter para volver al menú de reportes...")
                input()
                return

            # Procesar y comparar productos
            productos_diferentes = self._comparar_productos(df_freshdesk, df_clarity)
            
            if not productos_diferentes:
                print("🎉 No se encontraron tickets con productos diferentes.")
                print("\n💡 Presione Enter para volver al menú de reportes...")
                input()
                return

            # Crear y guardar reporte
            self._guardar_reporte_productos(productos_diferentes)
            
        except Exception as e:
            print(f"❌ Error inesperado durante la generación del reporte: {str(e)}")
        
        # Pausa final para confirmación
        print(f"\n💡 Presione Enter para volver al menú de reportes...")
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