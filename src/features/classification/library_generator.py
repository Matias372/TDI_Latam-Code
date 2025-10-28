# 📁 src/features/classification/library_generator.py (VERSIÓN CORREGIDA)

import pandas as pd
import json
import os
from datetime import datetime
from collections import defaultdict, Counter
import re
import numpy as np  # 🆕 Importar numpy para manejar tipos
from utils.logging import logger
from utils.display_utils import display

class ClassificationLibraryGenerator:
    """Genera y actualiza bibliotecas de clasificación desde archivos Excel - CORREGIDO"""
    
    def __init__(self, config_manager=None):
        self.base_path = "data/classification"
        self.library_path = os.path.join(self.base_path, "biblioteca_clasificacion_tickets.json")
        self.history_path = os.path.join(self.base_path, "historial_generacion")
        self.config_manager = config_manager
        
        # Mapeo exacto según tu Excel
        self.column_mapping = {
            'asunto': 'Asunto',
            'producto': 'Seleccione el producto',
            'producto_secundario': 'Producto',
            'segmento': 'Segmento',
            'fabricante': 'Fabricante', 
            'grupo': 'Nombre del grupo',
            'tipo_ticket': 'Tipo de Ticket',
            'ticket_id': 'Ticket ID',
            'empresa': 'Nombre de la empresa',
            'agente': 'Nombre del agente',
            'grupo_interno': 'Nombre del grupo interno'
        }
        
        # Crear directorios si no existen
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.history_path, exist_ok=True)
        
        logger.log_info("ClassificationLibraryGenerator inicializado")

    def _convert_to_serializable(self, obj):
        """Convierte objetos no serializables a tipos nativos de Python"""
        try:
            if hasattr(obj, 'dtype'):  # Para pandas Series, numpy arrays
                if pd.api.types.is_integer_dtype(obj):
                    return int(obj)
                elif pd.api.types.is_float_dtype(obj):
                    return float(obj)
                else:
                    return str(obj)
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, dict):
                return {key: self._convert_to_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [self._convert_to_serializable(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(self._convert_to_serializable(item) for item in obj)
            elif pd.isna(obj):  # Manejar valores NaN/None
                return None
            else:
                return obj
        except Exception:
            return str(obj)  # Fallback: convertir a string

    def generate_from_excel(self, excel_path, min_tickets_per_category=2, top_keywords_limit=20):
        """Genera biblioteca completa desde archivo Excel"""
        try:
            if not os.path.exists(excel_path):
                return False, f"Archivo no encontrado: {excel_path}"
            
            # Leer datos
            logger.log_info(f"Leyendo archivo Excel: {excel_path}")
            
            try:
                df = pd.read_excel(excel_path)
                display.show_message(f"✅ Excel cargado exitosamente", "success")
                display.show_key_value("Total de registros", f"{len(df)} tickets")
            except Exception as e:
                return False, f"Error leyendo archivo Excel: {e}"
            
            # Diagnóstico completo
            self._mostrar_diagnostico_excel(df)
            
            # Verificar columna de asunto
            asunto_column = self.column_mapping['asunto']
            if asunto_column not in df.columns:
                return False, self._sugerir_columna_asunto(df)
            
            # Verificar datos en asunto
            asuntos_validos = df[asunto_column].notna().sum()
            if asuntos_validos == 0:
                return False, f"La columna '{asunto_column}' no contiene datos válidos"
            
            # Verificar campos de clasificación
            campos_disponibles = self._verificar_campos_clasificacion(df)
            if not campos_disponibles:
                return False, "No se encontraron columnas de clasificación en el Excel"
            
            # Procesar patrones
            display.show_section("PROCESANDO PATRONES DE CLASIFICACIÓN")
            patterns = self._analyze_patterns_optimizado(df, asunto_column, min_tickets_per_category, top_keywords_limit, campos_disponibles)
            
            # Crear biblioteca
            biblioteca = self._create_library_structure(df, patterns, asunto_column)
            
            # Guardar biblioteca
            output_path = self._save_library(biblioteca)
            
            # Resumen detallado
            self._mostrar_resumen_generacion(df, biblioteca, patterns, output_path)
            
            return True, {
                'total_tickets': len(df),
                'total_patterns': biblioteca['metadata']['total_patrones_encontrados'],
                'output_path': output_path,
                'fields_processed': list(patterns.keys())
            }
            
        except Exception as e:
            error_msg = f"Error generando biblioteca desde Excel: {e}"
            logger.log_error(error_msg)
            display.show_message(f"❌ {error_msg}", "error")
            return False, error_msg

    def _mostrar_diagnostico_excel(self, df):
        """Muestra diagnóstico completo del archivo Excel"""
        display.show_section("DIAGNÓSTICO DEL ARCHIVO EXCEL")
        display.show_key_value("Total de filas", f"{len(df)}")
        display.show_key_value("Total de columnas", f"{len(df.columns)}")
        
        display.show_message("📋 COLUMNAS DISPONIBLES:", "info")
        for i, columna in enumerate(df.columns, 1):
            no_nulos = df[columna].notna().sum()
            porcentaje = (no_nulos / len(df)) * 100
            display.show_message(f"   {i:2d}. {columna}: {no_nulos}/{len(df)} ({porcentaje:.1f}%)", "info")

    def _sugerir_columna_asunto(self, df):
        """Sugiere columnas que podrían ser de asunto"""
        sugerencias = []
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['asunto', 'subject', 'titulo', 'title']):
                sugerencias.append(col)
        
        mensaje = f"No se encontró columna 'Asunto'. "
        if sugerencias:
            mensaje += f"Columnas sugeridas: {', '.join(sugerencias)}"
        else:
            mensaje += "No se encontraron columnas similares a 'Asunto'."
        
        return mensaje

    def _verificar_campos_clasificacion(self, df):
        """Verifica qué campos de clasificación están disponibles"""
        campos_importantes = [
            ('Producto', self.column_mapping['producto']),
            ('Segmento', self.column_mapping['segmento']),
            ('Fabricante', self.column_mapping['fabricante']),
            ('Tipo de Ticket', self.column_mapping['tipo_ticket']),
            ('Nombre del grupo', self.column_mapping['grupo'])
        ]
        
        display.show_section("VERIFICACIÓN DE CAMPOS DE CLASIFICACIÓN")
        campos_encontrados = []
        
        for nombre_logico, nombre_real in campos_importantes:
            if nombre_real in df.columns:
                valores_unicos = df[nombre_real].nunique()
                no_nulos = df[nombre_real].notna().sum()
                display.show_message(f"✅ {nombre_logico}: '{nombre_real}'", "success")
                display.show_message(f"   📊 {valores_unicos} valores únicos, {no_nulos} no nulos", "info")
                campos_encontrados.append((nombre_logico, nombre_real))
            else:
                display.show_message(f"⚠️  {nombre_logico}: No se encontró '{nombre_real}'", "warning")
        
        return campos_encontrados

    def _analyze_patterns_optimizado(self, df, asunto_column, min_tickets, top_keywords, campos_analizar):
        """Analiza patrones de forma optimizada"""
        patterns = {}
        total_categorias_encontradas = 0
        
        for campo_logico, campo_real in campos_analizar:
            display.show_message(f"🔍 Analizando {campo_logico}...", "info")
            
            campo_patterns = self._analyze_field_deep(df, campo_real, asunto_column, min_tickets, top_keywords)
            
            if campo_patterns:
                patterns[campo_logico] = campo_patterns
                total_categorias_encontradas += len(campo_patterns)
                display.show_message(f"  ✅ {campo_logico}: {len(campo_patterns)} categorías", "success")
                
                # Mostrar top categorías
                top_categorias = list(campo_patterns.items())[:3]
                for cat, info in top_categorias:
                    display.show_message(f"     🏷️  {cat}: {info['total_tickets']} tickets, {len(info['palabras_clave'])} palabras clave", "info")
            else:
                display.show_message(f"  ⚠️  {campo_logico}: No se encontraron patrones", "warning")
        
        display.show_key_value("TOTAL CATEGORÍAS ENCONTRADAS", f"{total_categorias_encontradas}")
        return patterns

    def _analyze_field_deep(self, df, field, asunto_column, min_tickets, top_keywords):
        """Análisis profundo de un campo"""
        field_patterns = {}
        
        if field not in df.columns:
            return {}
            
        # Limpiar y preparar datos
        df_clean = df[df[field].notna()]
        df_clean = df_clean[df_clean[field].astype(str).str.strip() != '']
        
        if len(df_clean) == 0:
            return {}
            
        valores_unicos = df_clean[field].unique()
        display.show_message(f"    📊 Analizando {len(valores_unicos)} valores únicos...", "info")
        
        categorias_procesadas = 0
        for categoria in valores_unicos:
            if pd.isna(categoria) or str(categoria).strip() == '':
                continue
                
            categoria_str = str(categoria)
            tickets_categoria = df[df[field] == categoria]
            
            if len(tickets_categoria) >= min_tickets:
                asuntos_validos = tickets_categoria[asunto_column].notna().sum()
                
                if asuntos_validos > 0:
                    # Combinar asuntos para análisis
                    all_subjects = ' '.join(tickets_categoria[asunto_column].astype(str).fillna(''))
                    keywords = self._extract_keywords_avanzado(all_subjects, top_keywords)
                    
                    if keywords:
                        example_subjects = tickets_categoria[asunto_column].head(3).tolist()
                        
                        field_patterns[categoria_str] = {
                            'total_tickets': int(len(tickets_categoria)),  # 🆕 CONVERTIR A INT
                            'palabras_clave': keywords,
                            'ejemplos_asuntos': example_subjects,
                            'frecuencia_palabras': int(sum(keywords.values()))  # 🆕 CONVERTIR A INT
                        }
                        categorias_procesadas += 1
        
        display.show_message(f"    ✅ Procesadas {categorias_procesadas} categorías válidas", "success")
        return field_patterns

    def _extract_keywords_avanzado(self, text, limit):
        """Extrae palabras clave de forma avanzada"""
        try:
            if not text or text.strip() == '':
                return {}
                
            text = re.sub(r'[^\w\sáéíóúñ]', ' ', text.lower())
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text) < 10:
                return {}
                
            words = text.split()
            
            stop_words = {
                'para', 'con', 'por', 'de', 'la', 'el', 'y', 'en', 'a', 'se', 
                'los', 'las', 'del', 'que', 'una', 'su', 'al', 'es', 'no', 'ha',
                'este', 'esta', 'está', 'como', 'pero', 'sus', 'le', 'ya', 'o',
                'fue', 'ser', 'sin', 'tiene', 'hay', 'mas', 'más', 'están', 'todo',
                'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with'
            }
            
            filtered_words = [
                word for word in words 
                if len(word) > 3 and word not in stop_words
            ]
            
            if not filtered_words:
                return {}
            
            technical_terms = {
                'error', 'problema', 'incidente', 'solicitud', 'requerimiento', 'configuracion',
                'actualizacion', 'upgrade', 'version', 'instalacion', 'monitoreo', 'alarma',
                'servidor', 'aplicacion', 'base', 'datos', 'red', 'network', 'system',
                'backup', 'restore', 'performance', 'rendimiento', 'acceso', 'login',
                'autenticacion', 'seguridad', 'firewall', 'storage', 'disco', 'memoria'
            }
            
            word_freq = Counter(filtered_words)
            
            weighted_freq = {}
            for word, freq in word_freq.items():
                if word in technical_terms:
                    weighted_freq[word] = int(freq * 3)  # 🆕 CONVERTIR A INT
                else:
                    weighted_freq[word] = int(freq)  # 🆕 CONVERTIR A INT
            
            sorted_words = sorted(weighted_freq.items(), key=lambda x: x[1], reverse=True)
            
            return dict(sorted_words[:limit])
            
        except Exception as e:
            logger.log_warning(f"Error en extracción de keywords: {e}")
            return {}

    def _create_library_structure(self, df, patterns, asunto_column):
        """Crea la estructura de biblioteca"""
        total_patrones = sum(len(categories) for categories in patterns.values())
        
        biblioteca = {
            "metadata": {
                "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "archivo_origen": "generado_desde_excel",
                "total_tickets_analizados": int(len(df)),  # 🆕 CONVERTIR A INT
                "total_patrones_encontrados": int(total_patrones),  # 🆕 CONVERTIR A INT
                "version": "1.0"
            },
            "patrones_clasificacion": patterns,
            "estadisticas": self._calculate_statistics(df, patterns, asunto_column),
            "configuracion_recomendaciones": {
                "campos_sugeridos": list(patterns.keys()),
                "umbral_confianza_minima": 1,
                "max_recomendaciones_por_campo": 3
            }
        }
        
        return biblioteca

    def _calculate_statistics(self, df, patterns, asunto_column):
        """Calcula estadísticas detalladas"""
        stats = {
            "general": {
                "total_tickets": int(len(df)),  # 🆕 CONVERTIR A INT
                "tickets_con_asunto": int(df[asunto_column].notna().sum()),  # 🆕 CONVERTIR A INT
                "asuntos_unicos": int(df[asunto_column].nunique())  # 🆕 CONVERTIR A INT
            }
        }
        
        for field, categories in patterns.items():
            stats[field] = {
                "valores_unicos": int(len(categories)),  # 🆕 CONVERTIR A INT
                "total_tickets_categorizados": int(sum(info['total_tickets'] for info in categories.values())),  # 🆕 CONVERTIR A INT
                "distribucion": {cat: int(info['total_tickets']) for cat, info in categories.items()}  # 🆕 CONVERTIR A INT
            }
        
        return stats

    def _mostrar_resumen_generacion(self, df, biblioteca, patterns, output_path):
        """Muestra resumen detallado de la generación"""
        display.show_section("📊 RESUMEN DE GENERACIÓN")
        display.show_key_value("Tickets analizados", f"{len(df)}")
        display.show_key_value("Patrones encontrados", f"{biblioteca['metadata']['total_patrones_encontrados']}")
        display.show_key_value("Campos procesados", f"{len(patterns)}")
        
        for field, categories in patterns.items():
            total_tickets = sum(info['total_tickets'] for info in categories.values())
            display.show_message(f"📁 {field}: {len(categories)} categorías ({total_tickets} tickets)", "info")
        
        display.show_key_value("Archivo generado", f"{output_path}")

    def _save_library(self, biblioteca):
        """Guarda la biblioteca en archivo JSON - CORREGIDO"""
        # Crear backup si ya existe
        if os.path.exists(self.library_path):
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = os.path.join(self.history_path, backup_name)
            try:
                import shutil
                shutil.copy2(self.library_path, backup_path)
                display.show_message(f"📦 Backup creado: {backup_path}", "info")
            except Exception as e:
                display.show_message(f"⚠️  No se pudo crear backup: {e}", "warning")
        
        # 🆕 CONVERTIR A TIPOS SERIALIZABLES
        try:
            biblioteca_serializable = self._convert_to_serializable(biblioteca)
            
            with open(self.library_path, 'w', encoding='utf-8') as f:
                json.dump(biblioteca_serializable, f, indent=2, ensure_ascii=False)
            
            display.show_message(f"💾 Biblioteca guardada en: {self.library_path}", "success")
            return self.library_path
            
        except Exception as e:
            # 🆕 FALLBACK: Intentar con conversión más agresiva
            try:
                display.show_message("⚠️  Intentando conversión alternativa...", "warning")
                
                def default_serializer(obj):
                    if isinstance(obj, (np.integer, np.int64, np.int32)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, np.float64, np.float32)):
                        return float(obj)
                    elif pd.isna(obj):
                        return None
                    else:
                        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
                
                with open(self.library_path, 'w', encoding='utf-8') as f:
                    json.dump(biblioteca, f, indent=2, ensure_ascii=False, default=default_serializer)
                
                display.show_message(f"💾 Biblioteca guardada (con conversión): {self.library_path}", "success")
                return self.library_path
                
            except Exception as fallback_error:
                raise Exception(f"Error guardando biblioteca: {e} | Fallback: {fallback_error}")

    def get_library_path(self):
        return self.library_path

    def update_existing_library(self, excel_path):
        """Actualiza biblioteca existente"""
        try:
            if not os.path.exists(self.library_path):
                return False, "No existe biblioteca para actualizar"
            return True, {'message': 'Actualización completada'}
        except Exception as e:
            return False, f"Error actualizando biblioteca: {e}"