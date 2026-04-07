import pandas as pd
from utils.file_utils import FileUtils
from utils.display_utils import display
from .models import FileValidationResult

class FileValidator:
    def __init__(self, logger):
        self.logger = logger

    def cargar_y_validar_archivos(self) -> FileValidationResult:
        """Cargar y validar archivos de Freshdesk y Clarity - INTERFAZ LIMPIA"""
        display.clear_screen()
        display.show_header(" VALIDACIÓN DE ARCHIVOS")
        display.show_message("Cargando archivos para sincronización...", "file")
        display.show_divider(50)
        
        # Cargar Freshdesk
        display.show_section("ARCHIVO FRESHDESK")
        ruta_freshdesk = self._seleccionar_archivo_freshdesk()
        if not ruta_freshdesk:
            display.show_message("No se seleccionó archivo Freshdesk", "error")
            return FileValidationResult(False, "No se seleccionó archivo Freshdesk")
        
        df_freshdesk = FileUtils.cargar_excel(ruta_freshdesk)
        if not self._validar_dataframe(df_freshdesk, "Freshdesk"):
            display.show_message("Archivo Freshdesk inválido", "error")
            return FileValidationResult(False, "Archivo Freshdesk inválido")
        
        # Cargar Clarity
        display.show_section("ARCHIVO CLARITY")
        ruta_clarity = self._seleccionar_archivo_clarity()
        if not ruta_clarity:
            display.show_message("No se seleccionó archivo Clarity", "error")
            return FileValidationResult(False, "No se seleccionó archivo Clarity")
        
        df_clarity = FileUtils.cargar_csv(ruta_clarity)
        if df_clarity is None:
            display.show_message("La carga automática falló, intentando carga manual...", "warning")
            df_clarity = FileUtils.cargar_csv_manual(ruta_clarity)
        
        if not self._validar_dataframe(df_clarity, "Clarity"):
            display.show_message("Archivo Clarity inválido", "error")
            return FileValidationResult(False, "Archivo Clarity inválido")
        
        # Validar estructura
        display.show_section("VALIDACIÓN DE ESTRUCTURA")
        if not self._validar_estructura_archivos(df_freshdesk, df_clarity):
            display.show_message("Estructura de archivos inválida", "error")
            return FileValidationResult(False, "Estructura de archivos inválida")
        
        df_freshdesk.attrs['file_path'] = ruta_freshdesk
        df_clarity.attrs['file_path'] = ruta_clarity
        
        display.show_message("Archivos validados correctamente", "success")
        return FileValidationResult(True, "Archivos válidos", df_freshdesk, df_clarity)
    
    def _seleccionar_archivo_freshdesk(self):
        return FileUtils.seleccionar_archivo(
            "Seleccione el archivo de Freshdesk", 
            [("Excel files", "*.xlsx *.xls")]
        )
    
    def _seleccionar_archivo_clarity(self):
        return FileUtils.seleccionar_archivo(
            "Seleccione el archivo de Clarity", 
            [("CSV files", "*.csv")]
        )
    
    def _validar_dataframe(self, df, nombre_archivo):
        if df is None or df.empty:
            display.show_message(f"{nombre_archivo}: No se pudo cargar o está vacío", "error")
            return False
        return True
    
    def _validar_estructura_archivos(self, df_freshdesk, df_clarity):
        """ VALIDACIÓN COMPLETA: Adaptación del código original con DisplayUtils"""
        errores = []
        
        display.show_message(f"Columnas Freshdesk: {list(df_freshdesk.columns)}", "debug")
        display.show_message(f"Columnas Clarity: {list(df_clarity.columns)}", "debug")
        
        # Verificar Freshdesk
        if 'Ticket ID' not in df_freshdesk.columns:
            errores.append("Freshdesk debe contener 'Ticket ID'")
        
        if 'Estado' not in df_freshdesk.columns:
            errores.append("Freshdesk debe contener 'Estado'")
        else:
            estados_freshdesk = df_freshdesk['Estado'].unique()
            display.show_message(f"Estados Freshdesk: {list(estados_freshdesk)}", "debug")

        #  BUSCAR ESPECÍFICAMENTE "Estado Freshdesk" EN CLARITY
        columna_id = None
        columna_estado_freshdesk = None
        
        display.show_message("Buscando columna 'Estado Freshdesk' en Clarity...", "search")
        
        # Buscar primero la columna exacta "Estado Freshdesk"
        for col in df_clarity.columns:
            if 'estado freshdesk' in col.lower():
                columna_estado_freshdesk = col
                display.show_message(f"Encontrada columna: '{col}'", "success")
                break
        
        # Si no se encuentra, buscar variantes
        if not columna_estado_freshdesk:
            for col in df_clarity.columns:
                if 'freshdesk' in col.lower():
                    columna_estado_freshdesk = col
                    display.show_message(f"Encontrada columna relacionada: '{col}'", "success")
                    break
        
        # Buscar columna ID
        for col in df_clarity.columns:
            if 'id' in col.lower():
                columna_id = col
                break

        if not columna_id:
            errores.append("No se encontró columna de ID en Clarity")
        else:
            display.show_message(f"Columna ID detectada: '{columna_id}'", "success")
            df_clarity.rename(columns={columna_id: 'ID'}, inplace=True)

        if not columna_estado_freshdesk:
            errores.append("No se encontró columna 'Estado Freshdesk' en Clarity")
            display.show_message(f"Columnas disponibles en Clarity: {list(df_clarity.columns)}", "debug")
        else:
            display.show_message(f"COLUMNA CRÍTICA DETECTADA: '{columna_estado_freshdesk}'", "success")
            df_clarity.rename(columns={columna_estado_freshdesk: 'Estado_Freshdesk_Clarity'}, inplace=True)
            
            if 'Estado_Freshdesk_Clarity' in df_clarity.columns:
                estados_clarity = df_clarity['Estado_Freshdesk_Clarity'].unique()
                display.show_message(f"Estados Freshdesk en Clarity: {list(estados_clarity)}", "debug")
            else:
                display.show_message("Advertencia: La columna 'Estado_Freshdesk_Clarity' no se creó correctamente", "warning")

        if errores:
            for error in errores:
                display.show_message(error, "error")
            return False
        
        display.show_message("Estructura de archivos verificada correctamente", "success")
        
        # Verificar compatibilidad de IDs
        ids_freshdesk = set(df_freshdesk['Ticket ID'].astype(str))
        ids_clarity = set(df_clarity['ID'].astype(str))
        coincidencias = ids_freshdesk.intersection(ids_clarity)
        
        display.show_message(f"Coincidencias de IDs: {len(coincidencias)} tickets", "info")
        display.show_message(f"Solo en Freshdesk: {len(ids_freshdesk - ids_clarity)}", "info")
        display.show_message(f"Solo en Clarity: {len(ids_clarity - ids_freshdesk)}", "info")
        
        return True

    def _buscar_columna_flexible(self, df, palabras_clave):
        """ MÉTODO REUTILIZABLE: Búsqueda flexible de columnas"""
        columnas = df.columns.tolist()
        for col in columnas:
            col_lower = col.lower()
            for palabra in palabras_clave:
                if palabra in col_lower:
                    return col
        return None