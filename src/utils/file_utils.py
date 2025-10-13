import os
import pandas as pd
from tkinter import filedialog, Tk
from config.constants import DATA_DIR, OUTPUT_DIR, TEMPLATES_DIR, CONFIG_FILE, AGENTES_TEMPLATE

class FileUtils:
    @staticmethod
    def seleccionar_archivo(titulo="Seleccionar archivo", tipos_archivo=[("Todos los archivos", "*.*"), ("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]):
        """Seleccionar archivo mediante diálogo"""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        archivo = filedialog.askopenfilename(
            title=titulo,
            filetypes=tipos_archivo,
            initialdir=DATA_DIR
        )
        root.destroy()
        return archivo

    @staticmethod
    def listar_archivos_input():
        """Listar archivos en la carpeta de input"""
        return [f for f in os.listdir(DATA_DIR) if f.endswith(('.xlsx', '.xls', '.csv'))]

    @staticmethod
    def cargar_excel(ruta_archivo):
        """Cargar archivo Excel"""
        try:
            return pd.read_excel(ruta_archivo)
        except Exception as e:
            print(f"❌ Error al cargar archivo Excel: {e}")
            return None

    @staticmethod
    def cargar_csv(ruta_archivo, separador=',', encoding_alternativos=['utf-8', 'latin-1', 'iso-8859-1']):
        """Cargar archivo CSV con detección automática de encoding y estructura"""
        print(f"📁 Intentando cargar CSV: {ruta_archivo}")
        
        for encoding in encoding_alternativos:
            try:
                print(f"   Probando encoding: {encoding}")
                
                with open(ruta_archivo, 'r', encoding=encoding) as f:
                    primeras_lineas = [f.readline().strip() for _ in range(5)]
                
                print(f"   Primeras líneas del archivo:")
                for i, linea in enumerate(primeras_lineas):
                    print(f"      Línea {i+1}: {linea}")
                
                if len(primeras_lineas) >= 2:
                    segunda_linea = primeras_lineas[1]
                    if 'Cliente' in segunda_linea and 'ID' in segunda_linea and 'Estado Freshdesk' in segunda_linea:
                        print("   ✅ Formato detectado: CSV con dos líneas de encabezado")
                        df = pd.read_csv(ruta_archivo, sep=separador, encoding=encoding, skiprows=1, header=0)
                        
                        print(f"   📋 Columnas detectadas: {list(df.columns)}")
                        if not df.empty:
                            print(f"   📊 Primera fila de datos: {df.iloc[0].to_dict()}")
                        return df
                
                print("   ✅ Formato detectado: CSV estándar")
                df = pd.read_csv(ruta_archivo, sep=separador, encoding=encoding)
                
                print(f"   📋 Columnas detectadas: {list(df.columns)}")
                if not df.empty:
                    print(f"   📊 Primera fila de datos: {df.iloc[0].to_dict()}")
                
                return df
                    
            except UnicodeDecodeError:
                print(f"   ❌ Error de encoding con {encoding}, probando siguiente...")
                continue
            except Exception as e:
                print(f"   ❌ Error al cargar con encoding {encoding}: {e}")
                continue
        
        print("❌ No se pudo cargar el archivo CSV con ningún encoding")
        return None

    @staticmethod
    def cargar_csv_manual(ruta_archivo):
        """Cargar archivo CSV manualmente para archivos problemáticos con dos encabezados"""
        try:
            print("🔄 Intentando carga manual del CSV...")
            
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            if len(lineas) < 3:
                print("❌ Archivo no tiene suficientes líneas")
                return None
            
            print("📝 Estructura del archivo:")
            for i, linea in enumerate(lineas[:3]):
                print(f"   Línea {i+1}: {linea.strip()}")
            
            encabezados = lineas[1].strip().split(',')
            print(f"📋 Encabezados reales detectados: {encabezados}")
            
            datos = []
            for i, linea in enumerate(lineas[2:], 2):
                if linea.strip():
                    linea_limpia = linea.strip().strip('"')
                    valores = linea_limpia.split('","') if '","' in linea_limpia else linea_limpia.split(',')
                    
                    if len(valores) == len(encabezados):
                        datos.append(valores)
                    else:
                        print(f"⚠️  Línea {i} tiene {len(valores)} valores, esperaba {len(encabezados)}: {valores}")
            
            if not datos:
                print("❌ No se encontraron datos válidos")
                return None
                
            df = pd.DataFrame(datos, columns=encabezados)
            print(f"✅ CSV cargado manualmente: {len(df)} filas, {len(df.columns)} columnas")
            
            df.columns = [col.strip() for col in df.columns]
            print(f"📋 Columnas finales: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error en carga manual: {e}")
            return None

    @staticmethod
    def guardar_excel(dataframe, nombre_archivo):
        """Guardar DataFrame como Excel en output"""
        ruta_completa = os.path.join(OUTPUT_DIR, nombre_archivo)
        dataframe.to_excel(ruta_completa, index=False)
        print(f"✅ Archivo guardado: {ruta_completa}")
        return ruta_completa