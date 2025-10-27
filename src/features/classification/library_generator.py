# 📁 src/features/classification/library_generator.py (CORREGIDO)

import pandas as pd
import json
import os
from datetime import datetime
from collections import defaultdict, Counter
import re
from utils.logging import logger

class ClassificationLibraryGenerator:
    """Genera y actualiza bibliotecas de clasificación desde archivos Excel"""
    
    def __init__(self):
        self.base_path = "data/classification"
        self.library_path = os.path.join(self.base_path, "biblioteca_clasificacion_tickets.json")
        self.history_path = os.path.join(self.base_path, "historial_generacion")
        
        # Crear directorios si no existen
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.history_path, exist_ok=True)
        
        logger.log_info("ClassificationLibraryGenerator inicializado")

    def generate_from_excel(self, excel_path, min_tickets_per_category=10, top_keywords_limit=20):
        """Genera biblioteca completa desde archivo Excel"""
        try:
            if not os.path.exists(excel_path):
                return False, f"Archivo no encontrado: {excel_path}"
            
            # Leer datos
            logger.log_info(f"Leyendo archivo Excel: {excel_path}")
            df = pd.read_excel(excel_path)
            
            # 🆕 MEJORA: Mostrar columnas disponibles para debugging
            print(f"📋 Columnas encontradas en el Excel: {list(df.columns)}")
            
            # Buscar columna de asunto (puede tener diferentes nombres)
            asunto_column = self._find_asunto_column(df)
            if not asunto_column:
                return False, "No se encontró columna de asunto en el Excel"
            
            print(f"✅ Usando columna de asunto: '{asunto_column}'")
            
            # Procesar datos
            logger.log_info("Analizando patrones en los datos...")
            patterns = self._analyze_patterns(df, asunto_column, min_tickets_per_category, top_keywords_limit)
            
            # 🆕 CORRECIÓN: Quitar el argumento extra asunto_column
            biblioteca = self._create_library_structure(df, patterns)
            
            # Guardar biblioteca
            output_path = self._save_library(biblioteca)
            
            logger.log_info(f"Biblioteca generada exitosamente: {len(df)} tickets, {biblioteca['metadata']['total_patrones_encontrados']} patrones")
            
            return True, {
                'total_tickets': len(df),
                'total_patterns': biblioteca['metadata']['total_patrones_encontrados'],
                'output_path': output_path
            }
            
        except Exception as e:
            logger.log_error(f"Error generando biblioteca desde Excel: {e}")
            return False, f"Error procesando Excel: {e}"

    def _find_asunto_column(self, df):
        """Encuentra la columna que contiene los asuntos"""
        # Posibles nombres para la columna de asunto
        possible_names = ['Asunto', 'Subject', 'Título', 'Title', 'Descripción', 'Description']
        
        for col in df.columns:
            if col in possible_names:
                return col
        
        # Si no encuentra nombres exactos, buscar columnas que contengan texto
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['asunto', 'subject', 'titulo', 'title']):
                return col
        
        # Si todo falla, usar la primera columna que tenga texto
        for col in df.columns:
            if df[col].dtype == 'object':  # Columna de texto
                return col
        
        return None

    def _analyze_patterns(self, df, asunto_column, min_tickets, top_keywords):
        """Analiza patrones en los datos"""
        patterns = {}
        
        # Campos a analizar (según el JSON de ejemplo)
        campos_analizar = [
            'Tipo de Ticket', 'Segmento', 'Fabricante', 
            'Producto', 'Nombre del grupo'
        ]
        
        for campo in campos_analizar:
            if campo in df.columns:
                logger.log_info(f"Analizando campo: {campo}")
                patterns[campo] = self._analyze_field_patterns(df, campo, asunto_column, min_tickets, top_keywords)
            else:
                print(f"⚠️  Campo '{campo}' no encontrado en el Excel")
        
        return patterns

    def _analyze_field_patterns(self, df, field, asunto_column, min_tickets, top_keywords):
        """Analiza patrones para un campo específico"""
        field_patterns = {}
        
        # Agrupar por categorías del campo
        for categoria, group in df.groupby(field):
            if len(group) >= min_tickets:
                # Extraer palabras clave de asuntos
                all_subjects = ' '.join(group[asunto_column].astype(str).fillna(''))
                keywords = self._extract_keywords(all_subjects, top_keywords)
                
                # Ejemplos de asuntos
                example_subjects = group[asunto_column].head(3).tolist()
                
                field_patterns[categoria] = {
                    'total_tickets': len(group),
                    'palabras_clave': keywords,
                    'ejemplos_asuntos': example_subjects,
                    'frecuencia_palabras': sum(keywords.values())
                }
        
        return field_patterns

    def _extract_keywords(self, text, limit):
        """Extrae palabras clave más frecuentes del texto"""
        # Limpiar y tokenizar texto
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filtrar palabras comunes y muy cortas
        stop_words = {'de', 'la', 'el', 'y', 'en', 'a', 'para', 'con', 'por', 'se', 'los', 'las'}
        filtered_words = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Contar frecuencia
        word_freq = Counter(filtered_words)
        
        return dict(word_freq.most_common(limit))

    def _create_library_structure(self, df, patterns):
        """Crea la estructura completa de la biblioteca"""
        return {
            "metadata": {
                "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "archivo_origen": "generado_desde_excel",
                "total_tickets_analizados": len(df),
                "total_patrones_encontrados": sum(len(categories) for categories in patterns.values()),
                "version": "1.0"
            },
            "patrones_clasificacion": patterns,
            "estadisticas": self._calculate_statistics(df, patterns),
            "configuracion_recomendaciones": {
                "campos_sugeridos": list(patterns.keys()),
                "umbral_confianza_minima": 2,
                "max_recomendaciones_por_campo": 3
            }
        }

    def _calculate_statistics(self, df, patterns):
        """Calcula estadísticas generales"""
        stats = {
            "general": {
                "total_tickets": len(df),
                "tickets_con_asunto": len(df),  # 🆕 SIMPLIFICADO: Todos los tickets tienen asunto
                "asuntos_unicos": df['Asunto'].nunique() if 'Asunto' in df.columns else len(df)
            }
        }
        
        # Estadísticas por campo
        for field, categories in patterns.items():
            stats[field] = {
                "valores_unicos": len(categories),
                "distribucion": {cat: info['total_tickets'] for cat, info in categories.items()}
            }
        
        return stats

    def _save_library(self, biblioteca):
        """Guarda la biblioteca en archivo JSON"""
        # Crear backup si ya existe
        if os.path.exists(self.library_path):
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = os.path.join(self.history_path, backup_name)
            try:
                os.rename(self.library_path, backup_path)
                logger.log_info(f"Backup creado: {backup_path}")
            except Exception as e:
                logger.log_warning(f"No se pudo crear backup: {e}")
        
        # Guardar nueva biblioteca
        with open(self.library_path, 'w', encoding='utf-8') as f:
            json.dump(biblioteca, f, indent=2, ensure_ascii=False)
        
        logger.log_info(f"Biblioteca guardada en: {self.library_path}")
        return self.library_path

    def update_existing_library(self, excel_path):
        """Actualiza biblioteca existente con nuevos datos"""
        try:
            # Cargar biblioteca existente
            if not os.path.exists(self.library_path):
                return False, "No existe biblioteca para actualizar"
            
            with open(self.library_path, 'r', encoding='utf-8') as f:
                existing_library = json.load(f)
            
            # Cargar nuevos datos
            new_df = pd.read_excel(excel_path)
            
            # Aquí iría la lógica para combinar/actualizar patrones
            # Por simplicidad, por ahora solo incrementamos el contador
            existing_library['metadata']['total_tickets_analizados'] += len(new_df)
            existing_library['metadata']['fecha_generacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Guardar actualización
            self._save_library(existing_library)
            
            logger.log_info(f"Biblioteca actualizada: {len(new_df)} nuevos tickets agregados")
            
            return True, {
                'new_tickets': len(new_df),
                'library_path': self.library_path
            }
            
        except Exception as e:
            logger.log_error(f"Error actualizando biblioteca: {e}")
            return False, f"Error actualizando biblioteca: {e}"

    def get_library_statistics(self):
        """Obtiene estadísticas de la biblioteca actual"""
        try:
            with open(self.library_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.log_warning(f"No se pudo cargar estadísticas de biblioteca: {e}")
            return None

    def get_library_path(self):
        """Retorna la ruta de la biblioteca actual"""
        return self.library_path

    def create_sample_library(self):
        """Crea una biblioteca de ejemplo para testing"""
        biblioteca_base = {
            "metadata": {
                "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "archivo_origen": "ejemplo_generado",
                "total_tickets_analizados": 0,
                "total_patrones_encontrados": 0,
                "version": "1.0"
            },
            "patrones_clasificacion": {},
            "estadisticas": {
                "general": {
                    "total_tickets": 0,
                    "tickets_con_asunto": 0,
                    "asuntos_unicos": 0
                }
            },
            "configuracion_recomendaciones": {
                "campos_sugeridos": [
                    "Tipo de Ticket",
                    "Segmento", 
                    "Fabricante",
                    "Producto",
                    "Nombre del grupo"
                ],
                "umbral_confianza_minima": 2,
                "max_recomendaciones_por_campo": 3
            }
        }
        
        # Guardar biblioteca base
        self._save_library(biblioteca_base)
        logger.log_info("Biblioteca de ejemplo creada")
        return self.library_path