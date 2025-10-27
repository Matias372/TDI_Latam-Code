# 📁 src/features/classification/classification_engine.py (MEJORADO)

import json
import os
import re
import pandas as pd
import time 
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple
from datetime import datetime
from .classification_config_manager import ClassificationConfigManager
from utils.display_utils import display 
from utils.file_utils import FileUtils    
from utils.validation_utils import ValidationUtils
from utils.api_utils import ApiUtils

# MOVER las funciones al inicio, antes de la clase
def initialize_classification_system():
    """Inicializa el sistema de clasificación integrado con SyncDesk"""
    
    # Ruta a la biblioteca JSON - ajustar según la estructura del proyecto
    library_path = os.path.join('data', 'classification', 'biblioteca_clasificacion_tickets.json')
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(library_path), exist_ok=True)
    
    engine = ClassificationEngine(library_path)
    
    if not engine.patterns:
        display.show_message("Sistema de clasificación inicializado sin biblioteca de patrones", "warning")
        display.show_message("Ejecuta 'generar_biblioteca_clasificacion()' para crear la biblioteca inicial", "info")
    
    return engine

def generar_biblioteca_clasificacion():
    """Función para generar biblioteca inicial desde datos existentes"""
    biblioteca_base = {
        "metadata": {
            "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "total_patrones_encontrados": 0
        },
        "patrones_clasificacion": {},
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
    library_path = os.path.join('data', 'classification', 'biblioteca_clasificacion_tickets.json')
    os.makedirs(os.path.dirname(library_path), exist_ok=True)
    
    with open(library_path, 'w', encoding='utf-8') as f:
        json.dump(biblioteca_base, f, indent=2, ensure_ascii=False)
    
    display.show_message(f"Biblioteca base creada en: {library_path}", "success")
    return library_path

class ClassificationEngine:
    """
    Motor de clasificación automática de tickets basado en patrones históricos
    """
    
    def __init__(self, library_path: str = None):
        self.config_manager = ClassificationConfigManager()
        self.config = self.config_manager.config
        self.library_path = library_path or self.config['library_path']
        
        self.siglas_map = self._build_siglas_dictionary()
        self.siglas_map.update(self.config.get('siglas_additional', {}))
        
        self.patterns = {}
        self.library_config = {}
        self.stats = {}
        self.load_library()

    def _build_siglas_dictionary(self) -> Dict[str, str]:
        """Construye diccionario de siglas técnicas comunes"""
        return {
            # BMC Truesight
            'TSSR': 'tssr', 'TSSA': 'tssa', 'TSAC': 'tsac',
            # Broadcom DX
            'UIM': 'uim', 'DXO2': 'dxo2', 'DX O2': 'dxo2', 'DX IM': 'uim',
            # General IT
            'CMDB': 'cmdb', 'OTEL': 'otel', 'RSCD': 'rscd', 
            'HELIX': 'helix', 'REMEDY': 'remedy', 'CLARITY': 'clarity',
            'API': 'api', 'SSL': 'ssl', 'CPU': 'cpu'
        }
    
    def load_library(self, library_path: str = None) -> bool:
        """Carga la biblioteca de patrones desde JSON"""
        if library_path:
            self.library_path = library_path
        
        if not self.library_path:
            display.show_message("❌ Ruta de biblioteca no especificada", "error")
            return False
            
        if not os.path.exists(self.library_path):
            display.show_message(f"❌ No se encontró biblioteca en: {self.library_path}", "error")
            return False
        
        try:
            with open(self.library_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.patterns = data.get("patrones_clasificacion", {})
                self.library_config = data.get("configuracion_recomendaciones", {})
                self.stats = data.get("estadisticas", {})
            
            # 🆕 VERIFICAR SI LA BIBLIOTECA TIENE PATRONES VÁLIDOS
            if not self.patterns:
                display.show_message("⚠️ Biblioteca cargada pero no contiene patrones", "warning")
            else:
                total_campos = len(self.patterns)
                total_categorias = sum(len(categorias) for categorias in self.patterns.values())
                display.show_message(f"✅ Biblioteca cargada: {total_campos} campos, {total_categorias} categorías", "success")
            
            return True
        except Exception as e:
            display.show_message(f"❌ Error cargando biblioteca: {e}", "error")
            return False
    
    def preprocess_text(self, text: str) -> str:
        """Mejorado con normalización de patrones variables"""
        if not text:
            return ""
        
        text = text.lower()
        
        # 1. Normalizar siglas conocidas
        for sigla, normalizada in self.siglas_map.items():
            text = re.sub(r'\b' + re.escape(sigla.lower()) + r'\b', normalizada, text)
        
        # 2. Normalizar patrones variables si está habilitado
        if self.config.get('variable_patterns', {}).get('enabled', True):
            text = self._normalize_variable_patterns(text)
        
        # 3. Limpiar caracteres especiales
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _normalize_variable_patterns(self, text: str) -> str:
        """Normaliza patrones variables como nombres de servidores"""
        variable_config = self.config.get('variable_patterns', {})
        
        if not variable_config:
            return text
        
        # Combinar patrones predefinidos y personalizados
        server_patterns = variable_config.get('server_patterns', [])
        custom_patterns = list(variable_config.get('custom_patterns', {}).keys())
        all_patterns = server_patterns + custom_patterns
        
        # Combinar mapeos
        normalized_to = variable_config.get('normalized_to', {})
        custom_mappings = variable_config.get('custom_patterns', {})
        all_mappings = {**normalized_to, **custom_mappings}
        
        for pattern in all_patterns:
            try:
                # Encontrar todas las coincidencias del patrón
                matches = re.finditer(pattern, text)
                for match in matches:
                    original = match.group()
                    
                    # Extraer la parte base (sin números) para buscar en mapeos
                    base_pattern = re.sub(r'\d+', '', original)
                    
                    # Buscar en los mapeos
                    normalized = None
                    for base, meaning in all_mappings.items():
                        if base in base_pattern or base_pattern in base:
                            normalized = meaning
                            break
                    
                    # Si encontramos un mapeo, reemplazar
                    if normalized:
                        text = text.replace(original, normalized)
                        
            except re.error as e:
                display.show_message(f"Error en patrón '{pattern}': {e}", "warning")
                continue
        
        return text
    
    def calculate_match_score(self, text: str, keywords: Dict[str, int]) -> int:
        """Calcula puntaje de coincidencia con palabras clave"""
        score = 0
        processed_text = self.preprocess_text(text)
        
        for keyword, frequency in keywords.items():
            keyword_clean = keyword.lower()
            # Búsqueda exacta de palabras
            if re.search(r'\b' + re.escape(keyword_clean) + r'\b', processed_text):
                score += frequency
        
        return score
    
    def classify_ticket(self, subject: str, description: str = "") -> Dict[str, List[Dict]]:
        """Clasifica un ticket basado en asunto y descripción"""
        full_text = f"{subject} {description}"
        results = {}
        
        if not self.patterns:
            return {"error": "Biblioteca de patrones no cargada"}
        
        # Usar library_config en lugar de config para campos de biblioteca
        fields = self.library_config.get("campos_sugeridos", [])
        threshold = self.library_config.get("umbral_confianza_minima", 2)
        max_recommendations = self.library_config.get("max_recomendaciones_por_campo", 3)
        
        for field in fields:
            if field in self.patterns:
                scores = []
                
                for category, info in self.patterns[field].items():
                    score = self.calculate_match_score(full_text, info["palabras_clave"])
                    if score >= threshold:
                        scores.append({
                            'category': category,
                            'score': score,
                            'total_tickets': info['total_tickets'],
                            'confidence': self._get_confidence_level(score)
                        })
                
                # Ordenar por score y limitar recomendaciones
                scores.sort(key=lambda x: x['score'], reverse=True)
                results[field] = scores[:max_recommendations]
        
        # Agregar detección de siglas
        results['siglas_detectadas'] = self._detect_siglas(full_text)
        
        return results
    
    def _get_confidence_level(self, score: int) -> str:
        """Determina nivel de confianza basado en el score"""
        thresholds = self.config.get('confidence_thresholds', {
            'high': 100,
            'medium': 50, 
            'low': 10
        })
        
        if score >= thresholds.get('high', 100):
            return "🔴 ALTA"
        elif score >= thresholds.get('medium', 50):
            return "🟡 MEDIA"
        elif score >= thresholds.get('low', 10):
            return "🟢 BAJA"
        else:
            return "⚪ MUY BAJA"
    
    def _detect_siglas(self, text: str) -> List[Dict]:
        """Detecta siglas técnicas en el texto"""
        detected = []
        text_lower = text.lower()
        
        for sigla, normalizada in self.siglas_map.items():
            if re.search(r'\b' + re.escape(sigla.lower()) + r'\b', text_lower):
                related_categories = self._find_related_categories(normalizada)
                detected.append({
                    'sigla': sigla,
                    'normalized': normalizada,
                    'related_categories': related_categories
                })
        
        return detected
    
    def _find_related_categories(self, term: str) -> List[str]:
        """Encuentra categorías relacionadas con un término"""
        related = []
        
        for field, categories in self.patterns.items():
            for category, info in categories.items():
                if term in info["palabras_clave"]:
                    related.append(f"{field}: {category}")
        
        return related
    
    def generate_detailed_report(self, subject: str, description: str = "") -> str:
        """Genera un reporte detallado de clasificación"""
        classification = self.classify_ticket(subject, description)
        
        report = []
        report.append("=" * 70)
        report.append("🔍 REPORTE DE CLASIFICACIÓN AUTOMÁTICA")
        report.append("=" * 70)
        report.append(f"📝 Asunto: {subject}")
        if description:
            report.append(f"📄 Descripción: {description[:200]}...")
        report.append("-" * 70)
        
        # Siglas detectadas
        if classification.get('siglas_detectadas'):
            report.append("\n🔤 SIGLAS DETECTADAS:")
            for sigla_info in classification['siglas_detectadas']:
                report.append(f"   • {sigla_info['sigla']} -> '{sigla_info['normalized']}'")
                if sigla_info['related_categories']:
                    report.append(f"     📍 Relacionado con: {', '.join(sigla_info['related_categories'][:3])}")
        
        # Clasificación por campo
        report.append("\n🎯 CLASIFICACIÓN RECOMENDADA:")
        for field, recommendations in classification.items():
            if field == 'siglas_detectadas':
                continue
                
            report.append(f"\n🏷️  {field.upper()}:")
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    report.append(f"   {i}. {rec['category']}")
                    report.append(f"      📊 Score: {rec['score']} | Confianza: {rec['confidence']}")
                    report.append(f"      📈 Tickets históricos: {rec['total_tickets']}")
            else:
                report.append("   🤔 No se encontraron coincidencias significativas")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def batch_classify(self, tickets: List[Dict]) -> Dict[str, Any]:
        """Clasifica múltiples tickets en lote"""
        results = {
            'total_tickets': len(tickets),
            'classified_tickets': 0,
            'results': [],
            'summary': defaultdict(lambda: defaultdict(int))
        }
        
        for i, ticket in enumerate(tickets):
            subject = ticket.get('subject', '')
            description = ticket.get('description', '')
            
            classification = self.classify_ticket(subject, description)
            ticket_result = {
                'ticket_id': ticket.get('id', i+1),
                'subject': subject,
                'classification': classification
            }
            
            results['results'].append(ticket_result)
            results['classified_tickets'] += 1
            
            # Actualizar summary
            for field, recommendations in classification.items():
                if field != 'siglas_detectadas' and recommendations:
                    top_category = recommendations[0]['category']
                    results['summary'][field][top_category] += 1
        
        return results

    # 🆕 NUEVAS FUNCIONES PARA ACTUALIZACIÓN AUTOMÁTICA DE BIBLIOTECA
    def actualizar_biblioteca_desde_ticket(self, subject: str, description: str, classification_result: Dict = None):
        """
        Actualiza la biblioteca de clasificación con palabras clave extraídas 
        del asunto y descripción del ticket actual.
        
        Args:
            subject (str): Asunto del ticket
            description (str): Descripción del ticket  
            classification_result (Dict): Resultado de la clasificación (opcional)
        
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Cargar la biblioteca actual
            if not os.path.exists(self.library_path):
                display.show_message("⚠️ No existe biblioteca para actualizar", "warning")
                return False
            
            with open(self.library_path, 'r', encoding='utf-8') as f:
                biblioteca = json.load(f)
            
            # Combinar asunto y descripción para análisis
            texto_completo = f"{subject} {description}"
            texto_procesado = self.preprocess_text(texto_completo)
            
            # Extraer palabras clave del texto
            palabras_clave = self._extraer_palabras_clave_avanzado(texto_procesado)
            
            # 🆕 VERIFICAR SI SE EXTRAJERON PALABRAS CLAVE
            if not palabras_clave:
                display.show_message("⚠️ No se pudieron extraer palabras clave del texto", "warning")
                return False
            
            # Si tenemos resultado de clasificación, usarlo para enriquecer los patrones
            if classification_result and 'error' not in classification_result:
                self._actualizar_patrones_con_clasificacion(biblioteca, classification_result, palabras_clave)
            else:
                # Si no hay clasificación, actualizar patrones generales
                self._actualizar_patrones_generales(biblioteca, palabras_clave)
            
            # Guardar biblioteca actualizada
            with open(self.library_path, 'w', encoding='utf-8') as f:
                json.dump(biblioteca, f, indent=2, ensure_ascii=False)
            
            display.show_message("✅ Biblioteca actualizada con palabras clave del ticket", "success")
            return True
            
        except Exception as e:
            display.show_message(f"❌ Error actualizando biblioteca: {e}", "error")
            return False

    def _extraer_palabras_clave_avanzado(self, texto: str, limit: int = 15) -> Dict[str, int]:
        """
        Extrae palabras clave más relevantes del texto, enfocándose en términos técnicos.
        
        Args:
            texto (str): Texto procesado
            limit (int): Límite de palabras clave a extraer
        
        Returns:
            Dict[str, int]: Diccionario de palabra -> frecuencia
        """
        # Palabras comunes a excluir
        stop_words = {
            'para', 'con', 'por', 'de', 'la', 'el', 'y', 'en', 'a', 'se', 
            'los', 'las', 'del', 'que', 'una', 'su', 'al', 'es', 'no', 'ha',
            'este', 'esta', 'está', 'como', 'pero', 'sus', 'le', 'ya', 'o',
            'fue', 'ser', 'sin', 'tiene', 'hay', 'mas', 'más', 'están', 'todo'
        }
        
        # Términos técnicos comunes a priorizar
        terminos_tecnicos = {
            'servidor', 'aplicacion', 'base', 'datos', 'red', 'network', 'system',
            'error', 'problema', 'incidente', 'solicitud', 'requerimiento', 'configuracion',
            'actualizacion', 'upgrade', 'version', 'instalacion', 'monitoreo', 'alarma',
            'backup', 'restore', 'performance', 'rendimiento', 'acceso', 'login',
            'autenticacion', 'seguridad', 'firewall', 'backup', 'storage', 'disco',
            'memoria', 'cpu', 'network', 'conexion', 'database', 'tabla', 'consulta',
            'api', 'webservice', 'interface', 'interfaz', 'usuario', 'cliente'
        }
        
        # Tokenizar y limpiar texto
        palabras = re.findall(r'\b[a-záéíóúñ]{4,}\b', texto.lower())
        
        # Filtrar palabras
        palabras_filtradas = [
            palabra for palabra in palabras 
            if palabra not in stop_words and len(palabra) > 3
        ]
        
        # Contar frecuencia
        contador = Counter(palabras_filtradas)
        
        # Priorizar términos técnicos
        palabras_priorizadas = {}
        for palabra, frecuencia in contador.most_common(limit * 2):  # Tomar el doble para filtrar
            if palabra in terminos_tecnicos:
                # Duplicar peso para términos técnicos
                palabras_priorizadas[palabra] = frecuencia * 2
            else:
                palabras_priorizadas[palabra] = frecuencia
        
        # Ordenar por frecuencia ponderada y tomar el límite
        palabras_ordenadas = dict(
            sorted(palabras_priorizadas.items(), key=lambda x: x[1], reverse=True)[:limit]
        )
        
        return palabras_ordenadas

    def _actualizar_patrones_con_clasificacion(self, biblioteca: Dict, classification_result: Dict, palabras_clave: Dict):
        """
        Actualiza patrones específicos basados en el resultado de clasificación.
        """
        campos_actualizables = ['Producto', 'Segmento', 'Fabricante', 'Tipo de Ticket']
        
        for campo in campos_actualizables:
            if campo in classification_result and classification_result[campo]:
                # Tomar la categoría con mayor score
                mejor_categoria = classification_result[campo][0]
                nombre_categoria = mejor_categoria['category']
                
                # Buscar o crear la categoría en la biblioteca
                if campo not in biblioteca['patrones_clasificacion']:
                    biblioteca['patrones_clasificacion'][campo] = {}
                
                if nombre_categoria not in biblioteca['patrones_clasificacion'][campo]:
                    # Crear nueva categoría
                    biblioteca['patrones_clasificacion'][campo][nombre_categoria] = {
                        'total_tickets': 1,
                        'palabras_clave': palabras_clave,
                        'ejemplos_asuntos': [],
                        'frecuencia_palabras': sum(palabras_clave.values())
                    }
                else:
                    # Actualizar categoría existente
                    categoria = biblioteca['patrones_clasificacion'][campo][nombre_categoria]
                    
                    # Combinar palabras clave existentes con nuevas
                    palabras_existentes = categoria.get('palabras_clave', {})
                    
                    for palabra, frecuencia in palabras_clave.items():
                        if palabra in palabras_existentes:
                            palabras_existentes[palabra] += frecuencia
                        else:
                            palabras_existentes[palabra] = frecuencia
                    
                    # Ordenar y limitar palabras clave
                    palabras_combinadas = dict(
                        sorted(palabras_existentes.items(), key=lambda x: x[1], reverse=True)[:20]
                    )
                    
                    categoria['palabras_clave'] = palabras_combinadas
                    categoria['total_tickets'] += 1
                    categoria['frecuencia_palabras'] = sum(palabras_combinadas.values())

    def _actualizar_patrones_generales(self, biblioteca: Dict, palabras_clave: Dict):
        """
        Actualiza patrones generales cuando no hay clasificación específica.
        """
        campo_general = 'General'
        
        if campo_general not in biblioteca['patrones_clasificacion']:
            biblioteca['patrones_clasificacion'][campo_general] = {}
        
        categoria_general = 'Tickets Recientes'
        
        if categoria_general not in biblioteca['patrones_clasificacion'][campo_general]:
            biblioteca['patrones_clasificacion'][campo_general][categoria_general] = {
                'total_tickets': 1,
                'palabras_clave': palabras_clave,
                'ejemplos_asuntos': [],
                'frecuencia_palabras': sum(palabras_clave.values())
            }
        else:
            categoria = biblioteca['patrones_clasificacion'][campo_general][categoria_general]
            
            # Combinar palabras clave
            palabras_existentes = categoria.get('palabras_clave', {})
            
            for palabra, frecuencia in palabras_clave.items():
                if palabra in palabras_existentes:
                    palabras_existentes[palabra] += frecuencia
                else:
                    palabras_existentes[palabra] = frecuencia
            
            # Ordenar y limitar
            palabras_combinadas = dict(
                sorted(palabras_existentes.items(), key=lambda x: x[1], reverse=True)[:20]
            )
            
            categoria['palabras_clave'] = palabras_combinadas
            categoria['total_tickets'] += 1
            categoria['frecuencia_palabras'] = sum(palabras_combinadas.values())

    def clasificar_ticket_individual(self, ticket_id: int, freshdesk_service) -> Dict[str, Any]:
        """
        Clasifica un ticket individual por ID desde Freshdesk y actualiza la biblioteca
        """
        try:
            # 🆕 VERIFICACIÓN MEJORADA DEL SERVICIO FRESHDESK
            if freshdesk_service is None:
                display.show_message("❌ Servicio Freshdesk no disponible", "error")
                return {
                    'id': ticket_id,
                    'error': 'Servicio Freshdesk no disponible'
                }
            
            # 🆕 VERIFICAR SI EL SERVICIO TIENE CONFIGURACIÓN VÁLIDA
            try:
                if not hasattr(freshdesk_service, 'config'):
                    display.show_message("❌ Configuración de Freshdesk no encontrada", "error")
                    return {
                        'id': ticket_id,
                        'error': 'Configuración de Freshdesk no encontrada'
                    }
                
                # Verificar credenciales
                config_status = freshdesk_service.config.validar_configuracion()
                if not config_status:
                    display.show_message("❌ Credenciales de Freshdesk no configuradas", "error")
                    display.show_message("💡 Configure primero la conexión a Freshdesk", "info")
                    return {
                        'id': ticket_id,
                        'error': 'Credenciales de Freshdesk no configuradas'
                    }
                    
            except Exception as config_error:
                display.show_message(f"❌ Error en configuración de Freshdesk: {config_error}", "error")
                return {
                    'id': ticket_id,
                    'error': f'Error en configuración de Freshdesk: {config_error}'
                }

            display.show_message(f"Obteniendo ticket #{ticket_id} desde Freshdesk...", "info")
            
            # 🆕 CORRECCIÓN: USAR ApiUtils.get_ticket EN LUGAR DE freshdesk_service.get_ticket
            from utils.api_utils import ApiUtils  # 🆕 Importar aquí o al inicio del archivo
            
            # Obtener configuración del servicio
            domain = freshdesk_service.config.freshdesk_domain
            api_key = freshdesk_service.config.api_key
            
            if not domain or not api_key:
                display.show_message("❌ Dominio o API Key no configurados", "error")
                return {
                    'id': ticket_id,
                    'error': 'Dominio o API Key no configurados'
                }
            
            # 🆕 LLAMAR CORRECTAMENTE A ApiUtils.get_ticket
            response = ApiUtils.get_ticket(domain, api_key, ticket_id)
            
            # 🆕 VERIFICAR LA RESPUESTA
            if response.status_code != 200:
                display.show_message(f"❌ Error al obtener ticket #{ticket_id}: {response.status_code}", "error")
                return {
                    'id': ticket_id,
                    'error': f'Error {response.status_code} al obtener ticket'
                }
            
            ticket_data = response.json()
            
            # 🆕 EXTRAER DATOS CORRECTAMENTE - USAR description_text QUE ES MÁS LIMPIO
            subject = ticket_data.get('subject', '')
            description = ticket_data.get('description', '')
            description_text = ticket_data.get('description_text', '')
            
            # Preferir description_text sobre description (sin HTML)
            texto_descripcion = description_text if description_text else description
            
            # 🆕 VERIFICAR QUE EL TICKET TENGA DATOS VÁLIDOS
            if not subject and not texto_descripcion:
                display.show_message(f"⚠️  Ticket #{ticket_id} no tiene asunto ni descripción", "warning")
            
            display.show_header(f"CLASIFICANDO TICKET #{ticket_id}")
            display.show_key_value("Asunto", subject if subject else "No disponible")
            
            if texto_descripcion:
                display.show_key_value("Descripción", texto_descripcion[:100] + "..." if len(texto_descripcion) > 100 else texto_descripcion)
            else:
                display.show_key_value("Descripción", "No disponible")
            
            # Clasificar el ticket
            classification_result = self.classify_ticket(subject, texto_descripcion)
            
            # 🆕 VERIFICAR SI LA CLASIFICACIÓN FUE EXITOSA
            if 'error' in classification_result:
                display.show_message(f"❌ Error en clasificación: {classification_result['error']}", "error")
                return {
                    'id': ticket_id,
                    'error': classification_result['error']
                }
            
            # 🆕 ACTUALIZAR BIBLIOTECA con las palabras clave de este ticket
            display.show_message("📚 Actualizando biblioteca con palabras clave del ticket...", "info")
            actualizacion_exitosa = self.actualizar_biblioteca_desde_ticket(subject, texto_descripcion, classification_result)
            
            recomendaciones = self._extraer_recomendaciones_principales(classification_result)
            
            resultado = {
                'id': ticket_id,
                'asunto': subject,
                'descripcion': texto_descripcion[:200] + '...' if len(texto_descripcion) > 200 else texto_descripcion,
                'producto_recomendado': recomendaciones.get('Producto', 'No determinado'),
                'segmento_recomendado': recomendaciones.get('Segmento', 'No determinado'),
                'fabricante_recomendado': recomendaciones.get('Fabricante', 'No determinado'),
                'motivo_recomendado': recomendaciones.get('Tipo de Ticket', 'No determinado'),
                'regla_aplicada': recomendaciones.get('regla_aplicada', 'Sin regla específica'),
                'confianza_promedio': recomendaciones.get('confianza_promedio', 0),
                'campos_clasificados': list(recomendaciones.keys()),
                'biblioteca_actualizada': actualizacion_exitosa
            }
            
            self._mostrar_resultados_clasificacion(resultado)
            
            return resultado
            
        except Exception as e:
            display.show_message(f"❌ Error inesperado al clasificar ticket: {str(e)}", "error")
            return {
                'id': ticket_id,
                'error': f'Error inesperado al clasificar ticket: {str(e)}'
            }

    def _mostrar_resultados_clasificacion(self, resultado: dict):
        """Mostrar resultados de clasificación con formato bonito"""
        display.show_section("RESULTADOS DE CLASIFICACIÓN")
        display.show_key_value("Producto Recomendado", resultado['producto_recomendado'])
        display.show_key_value("Segmento Recomendado", resultado['segmento_recomendado'])
        display.show_key_value("Fabricante Recomendado", resultado['fabricante_recomendado'])
        display.show_key_value("Motivo Recomendado", resultado['motivo_recomendado'])
        display.show_key_value("Confianza", f"{resultado['confianza_promedio']:.2f}")
        display.show_key_value("Regla Aplicada", resultado['regla_aplicada'])
        if resultado.get('biblioteca_actualizada'):
            display.show_key_value("Biblioteca", "✅ Actualizada con palabras clave")
        else:
            display.show_key_value("Biblioteca", "⚠️ No se pudo actualizar")
        
    def _extraer_recomendaciones_principales(self, classification_result: Dict) -> Dict[str, Any]:
        """
        Extrae las recomendaciones principales de cada campo
        """
        recomendaciones = {}
        confianzas = []
        reglas_aplicadas = []
        
        # Campos que nos interesan
        campos_objetivo = ['Producto', 'Segmento', 'Fabricante', 'Tipo de Ticket']
        
        for campo in campos_objetivo:
            if campo in classification_result and classification_result[campo]:
                # Tomar la mejor recomendación (primera de la lista ordenada)
                mejor_recomendacion = classification_result[campo][0]
                recomendaciones[campo] = mejor_recomendacion['category']
                confianzas.append(mejor_recomendacion['score'])
                
                # Construir regla aplicada
                regla = f"{campo}: {mejor_recomendacion['category']} (score: {mejor_recomendacion['score']})"
                reglas_aplicadas.append(regla)
            else:
                recomendaciones[campo] = 'No determinado'
        
        # Calcular métricas
        if confianzas:
            recomendaciones['confianza_promedio'] = sum(confianzas) / len(confianzas)
        else:
            recomendaciones['confianza_promedio'] = 0
            
        if reglas_aplicadas:
            recomendaciones['regla_aplicada'] = ' | '.join(reglas_aplicadas)
        else:
            recomendaciones['regla_aplicada'] = 'Sin coincidencias significativas'
        
        return recomendaciones

    def clasificar_tickets_prueba(self, archivo_excel: str, freshdesk_service) -> Dict[str, Any]:
        """
        Clasifica múltiples tickets desde Excel y compara con valores originales
        """
        try:
            # Usar FileUtils para cargar Excel
            display.show_message(f"Cargando archivo Excel: {archivo_excel}", "file")
            df_original = FileUtils.cargar_excel(archivo_excel)
            
            if df_original is None:
                return {'error': 'No se pudo cargar el archivo Excel'}
            
            # 🆕 CORRECCIÓN: BUSCAR "Ticket ID" EN LUGAR DE "id"
            if 'Ticket ID' not in df_original.columns:
                # Mostrar las columnas disponibles para debugging
                columnas_disponibles = list(df_original.columns)
                display.show_message(f"❌ Columnas disponibles: {columnas_disponibles}", "error")
                return {'error': 'El archivo Excel debe tener una columna "Ticket ID"'}
            
            resultados = []
            total_tickets = len(df_original)
            
            display.show_message(f"Iniciando clasificación de {total_tickets} tickets...", "info")
            
            for index, row in df_original.iterrows():
                # 🆕 CORRECCIÓN: USAR "Ticket ID" EN LUGAR DE "id"
                ticket_id = row['Ticket ID']
                
                # 🆕 VERIFICAR QUE EL TICKET ID SEA VÁLIDO
                if pd.isna(ticket_id) or ticket_id == '':
                    display.show_message(f"⚠️ Fila {index+1}: Ticket ID vacío o inválido", "warning")
                    continue
                
                # Convertir a entero si es necesario
                try:
                    ticket_id = int(ticket_id)
                except (ValueError, TypeError):
                    display.show_message(f"⚠️ Fila {index+1}: Ticket ID '{ticket_id}' no es válido", "warning")
                    continue
                
                # Usar DisplayUtils para mostrar progreso
                display.show_processing_message(
                    str(ticket_id), 
                    index + 1, 
                    total_tickets, 
                    "Clasificando"
                )
                
                resultado = self.clasificar_ticket_individual(ticket_id, freshdesk_service)
                
                if 'error' not in resultado:
                    # 🆕 CORRECCIÓN: FILTRAR POR "Ticket ID" EN LUGAR DE "id"
                    fila_original = df_original[df_original['Ticket ID'] == ticket_id]
                    if not fila_original.empty:
                        comparacion = self._comparar_con_original(resultado, fila_original.iloc[0])
                        resultados.append(comparacion)
                
                # Pequeña pausa para evitar sobrecargar la API
                if (index + 1) % 10 == 0:
                    time.sleep(1)
            
            display.clear_line()
            display.show_message(f"Procesados {len(resultados)}/{total_tickets} tickets exitosamente", "success")
            
            reporte = self._generar_reporte_comparativo(resultados)
            return {
                'resultados': resultados,
                'reporte': reporte,
                'total_tickets': total_tickets,
                'procesados': len(resultados)
            }
            
        except Exception as e:
            display.show_message(f"Error en clasificación múltiple: {str(e)}", "error")
            return {'error': f'Error en clasificación múltiple: {str(e)}'}

    def _comparar_con_original(self, resultado_clasificacion: Dict, fila_original: pd.Series) -> Dict[str, Any]:
        """
        Compara resultado de clasificación con valores originales - CORREGIDA
        """
        def encontrar_valor_original(fila, nombres_posibles, default='No especificado'):
            """Busca un valor en múltiples nombres de columna posibles"""
            for nombre in nombres_posibles:
                if nombre in fila:
                    valor = fila[nombre]
                    if pd.notna(valor) and str(valor).strip() != '':
                        return str(valor).strip()
            return default
        
        # 🆕 MAPEO ACTUALIZADO CON TUS COLUMNAS EXACTAS
        mapeo_columnas = {
            'producto': ['Seleccione el producto', 'Producto', 'producto', 'product'],
            'segmento': ['Segmento', 'segmento', 'segment'], 
            'fabricante': ['Fabricante', 'fabricante', 'manufacturer'],
            'motivo': ['Tipo de Ticket', 'motivo', 'reason', 'tipo']
        }
        
        comparacion = {
            'id': resultado_clasificacion['id'],
            'asunto': resultado_clasificacion.get('asunto', ''),
            'producto_recomendado': resultado_clasificacion.get('producto_recomendado', 'No determinado'),
            'segmento_recomendado': resultado_clasificacion.get('segmento_recomendado', 'No determinado'),
            'fabricante_recomendado': resultado_clasificacion.get('fabricante_recomendado', 'No determinado'),
            'motivo_recomendado': resultado_clasificacion.get('motivo_recomendado', 'No determinado'),
            'regla_aplicada': resultado_clasificacion.get('regla_aplicada', 'Sin regla'),
            'confianza': resultado_clasificacion.get('confianza_promedio', 0),
            'biblioteca_actualizada': resultado_clasificacion.get('biblioteca_actualizada', False)
        }
        
        # 🆕 OBTENER VALORES ORIGINALES DE TUS COLUMNAS EXACTAS
        comparacion['producto_original'] = encontrar_valor_original(fila_original, mapeo_columnas['producto'])
        comparacion['segmento_original'] = encontrar_valor_original(fila_original, mapeo_columnas['segmento'])
        comparacion['fabricante_original'] = encontrar_valor_original(fila_original, mapeo_columnas['fabricante'])
        comparacion['motivo_original'] = encontrar_valor_original(fila_original, mapeo_columnas['motivo'])
        
        # Comparación flexible (case-insensitive)
        def comparar_flexible(valor1, valor2):
            if valor1 == valor2:
                return True
            v1 = str(valor1).lower().strip() if valor1 not in ['No determinado', 'No especificado'] else valor1
            v2 = str(valor2).lower().strip() if valor2 not in ['No determinado', 'No especificado'] else valor2
            return v1 == v2
        
        comparacion['producto_coincide'] = comparar_flexible(
            comparacion['producto_recomendado'], comparacion['producto_original'])
        comparacion['segmento_coincide'] = comparar_flexible(
            comparacion['segmento_recomendado'], comparacion['segmento_original'])
        comparacion['fabricante_coincide'] = comparar_flexible(
            comparacion['fabricante_recomendado'], comparacion['fabricante_original'])
        comparacion['motivo_coincide'] = comparar_flexible(
            comparacion['motivo_recomendado'], comparacion['motivo_original'])
        
        # Calcular precisión general
        campos_coinciden = [
            comparacion['producto_coincide'],
            comparacion['segmento_coincide'], 
            comparacion['fabricante_coincide'],
            comparacion['motivo_coincide']
        ]
        
        campos_validos = sum(1 for campo in campos_coinciden if comparacion['producto_original'] != 'No especificado')
        if campos_validos > 0:
            comparacion['precision_general'] = sum(campos_coinciden) / campos_validos * 100
        else:
            comparacion['precision_general'] = 0
        
        return comparacion

    def _generar_reporte_comparativo(self, resultados: List[Dict]) -> str:
        """
        Genera reporte estadístico de la comparación
        """
        if not resultados:
            return "No hay resultados para generar reporte"
        
        df_resultados = pd.DataFrame(resultados)
        
        # Calcular estadísticas
        total_tickets = len(resultados)
        precision_producto = (df_resultados['producto_coincide'].sum() / total_tickets) * 100
        precision_segmento = (df_resultados['segmento_coincide'].sum() / total_tickets) * 100
        precision_fabricante = (df_resultados['fabricante_coincide'].sum() / total_tickets) * 100
        precision_motivo = (df_resultados['motivo_coincide'].sum() / total_tickets) * 100
        precision_promedio = df_resultados['precision_general'].mean()
        bibliotecas_actualizadas = df_resultados['biblioteca_actualizada'].sum()
        
        reporte = f"""
📊 REPORTE DE PRECISIÓN - CLASIFICACIÓN AUTOMÁTICA
==================================================
📈 ESTADÍSTICAS GENERALES:
   • Total de tickets procesados: {total_tickets}
   • Precisión promedio: {precision_promedio:.2f}%
   • Bibliotecas actualizadas: {bibliotecas_actualizadas}

🎯 PRECISIÓN POR CAMPO:
   • Producto: {precision_producto:.2f}%
   • Segmento: {precision_segmento:.2f}%
   • Fabricante: {precision_fabricante:.2f}%
   • Motivo: {precision_motivo:.2f}%

📋 DISTRIBUCIÓN DE PRECISIÓN:
{df_resultados['precision_general'].describe()}
        """
        
        return reporte

    def guardar_resultados_excel(self, resultados: List[Dict], output_path: str = None) -> str:
        """
        Guarda los resultados comparativos en Excel
        """
        if not output_path:
            output_dir = os.path.join('data', 'output', 'classification')
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f'resultado_comparacion_{timestamp}.xlsx')
        
        df_resultados = pd.DataFrame(resultados)
        
        # Crear Excel con múltiples hojas
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Hoja principal con todos los resultados
            df_resultados.to_excel(writer, sheet_name='Resultados Completos', index=False)
            
            # Hoja de resumen estadístico
            resumen_data = {
                'Métrica': ['Total Tickets', 'Precisión Promedio', 'Producto Correctos', 
                           'Segmento Correctos', 'Fabricante Correctos', 'Motivo Correctos',
                           'Bibliotecas Actualizadas'],
                'Valor': [
                    len(resultados),
                    f"{df_resultados['precision_general'].mean():.2f}%",
                    f"{df_resultados['producto_coincide'].sum()} ({df_resultados['producto_coincide'].sum()/len(resultados)*100:.2f}%)",
                    f"{df_resultados['segmento_coincide'].sum()} ({df_resultados['segmento_coincide'].sum()/len(resultados)*100:.2f}%)",
                    f"{df_resultados['fabricante_coincide'].sum()} ({df_resultados['fabricante_coincide'].sum()/len(resultados)*100:.2f}%)",
                    f"{df_resultados['motivo_coincide'].sum()} ({df_resultados['motivo_coincide'].sum()/len(resultados)*100:.2f}%)",
                    f"{df_resultados['biblioteca_actualizada'].sum()}"
                ]
            }
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja con solo los incorrectos para análisis
            incorrectos = df_resultados[df_resultados['precision_general'] < 100]
            if not incorrectos.empty:
                incorrectos.to_excel(writer, sheet_name='Necesitan Revisión', index=False)
        
        display.show_message(f"Resultados guardados en: {output_path}", "success")
        return output_path
    
    def diagnosticar_precision_cero(self, resultados: List[Dict], df_original: pd.DataFrame):
        """Diagnostica por qué la precisión es 0% - MEJORADA"""
        display.show_header("🔍 DIAGNÓSTICO DETALLADO PRECISIÓN 0%")
        
        # Mostrar estructura del DataFrame original
        display.show_section("ESTRUCTURA DEL EXCEL ORIGINAL:")
        for columna in df_original.columns:
            display.show_key_value("Columna", columna)
        
        # Verificar los primeros 3 resultados en detalle
        for i, resultado in enumerate(resultados[:3]):
            display.show_section(f"ANÁLISIS TICKET #{resultado['id']}")
            
            # Mostrar qué encontró en las filas originales
            fila_original = df_original[df_original['Ticket ID'] == resultado['id']]
            if not fila_original.empty:
                fila = fila_original.iloc[0]
                display.show_subsection("VALORES ENCONTRADOS EN EXCEL:")
                for columna in ['Seleccione el producto', 'Producto', 'Segmento', 'Fabricante', 'Tipo de Ticket']:
                    if columna in fila:
                        valor = fila[columna]
                        display.show_key_value(f"Excel - {columna}", f"'{valor}' (tipo: {type(valor).__name__})")
            
            display.show_subsection("COMPARACIÓN:")
            campos = ['producto', 'segmento', 'fabricante', 'motivo']
            for campo in campos:
                recomendado = resultado.get(f'{campo}_recomendado', 'N/A')
                original = resultado.get(f'{campo}_original', 'N/A')
                coincide = resultado.get(f'{campo}_coincide', False)
                
                status = "✅" if coincide else "❌"
                display.show_message(f"{status} {campo.upper()}:", "info")
                display.show_key_value("  Recomendado", f"'{recomendado}'")
                display.show_key_value("  Original", f"'{original}'")
                display.show_key_value("  Coincide", "SÍ" if coincide else "NO")

# 📁 Tests y ejemplos de uso
if __name__ == "__main__":
    # Ejemplo de uso
    engine = initialize_classification_system()
    
    # Tickets de prueba
    test_tickets = [
        {
            "subject": "REQUERIMIENTO CMPC: Eliminación de equipos de la CMDB",
            "description": "Necesito eliminar 3 equipos Kyocera Taskalfa de la CMDB para CMPC"
        },
        {
            "subject": "Problema upgrade TSSR 24.4 - iconos faltantes", 
            "description": "Luego del upgrade del TSSR a versión 24.4, se observan iconos faltantes en la interfaz"
        },
        {
            "subject": "INC - DX UIM: No se reciben alarmas en DXO2",
            "description": "El sistema UIM no está enviando alarmas a la plataforma DX O2"
        }
    ]
    
    display.show_header("PROBANDO SISTEMA DE CLASIFICACIÓN")
    
    for i, ticket in enumerate(test_tickets, 1):
        display.show_section(f"Ticket {i}")
        report = engine.generate_detailed_report(
            ticket["subject"], 
            ticket["description"]
        )
        print(report)
    
    # Procesamiento por lote
    display.show_section("CLASIFICACIÓN POR LOTE")
    batch_results = engine.batch_classify(test_tickets)
    display.show_message(f"Tickets procesados: {batch_results['classified_tickets']}/{batch_results['total_tickets']}", "success")
    
    # Resumen
    display.show_section("RESUMEN DE CLASIFICACIÓN")
    for field, categories in batch_results['summary'].items():
        display.show_subsection(field)
        for category, count in categories.items():
            display.show_key_value(category, str(count))