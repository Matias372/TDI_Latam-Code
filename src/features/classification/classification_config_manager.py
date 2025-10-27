# 📁 src/features/classification/classification_config_manager.py (NUEVO)

import json
import os
from utils.logging import logger
from .classification_config import CLASSIFICATION_CONFIG

class ClassificationConfigManager:
    """
    Gestor de configuración específico para el sistema de clasificación
    No maneja credenciales, solo configuración de clasificación
    """
    
    def __init__(self):
        self.config_file = "data/classification/classification_config.json"
        self.default_config = CLASSIFICATION_CONFIG
        self.config = self.default_config.copy()
        self.load_config()
        
        logger.log_info("ClassificationConfigManager inicializado")

    def load_config(self):
        """Cargar configuración desde archivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Actualizar recursivamente la configuración
                    self._update_dict(self.config, loaded_config)
                logger.log_info(f"Configuración de clasificación cargada desde: {self.config_file}")
            else:
                # Si no existe, crear con valores por defecto
                self.save_config()
                logger.log_info("Configuración de clasificación creada con valores por defecto")
        except Exception as e:
            logger.log_error(f"Error cargando configuración de clasificación: {e}")

    def save_config(self):
        """Guardar configuración en archivo JSON"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.log_info(f"Configuración de clasificación guardada en: {self.config_file}")
        except Exception as e:
            logger.log_error(f"Error guardando configuración de clasificación: {e}")

    def _update_dict(self, d, u):
        """Actualizar recursivamente un diccionario"""
        for key, value in u.items():
            if isinstance(value, dict) and key in d and isinstance(d[key], dict):
                self._update_dict(d[key], value)
            else:
                d[key] = value

    def get(self, key, default=None):
        """Obtener valor de configuración usando dot notation"""
        keys = key.split('.')
        current = self.config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def set(self, key, value):
        """Establecer valor de configuración usando dot notation"""
        keys = key.split('.')
        current = self.config
        
        # Navegar hasta el penúltimo nivel
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Establecer el valor final
        current[keys[-1]] = value
        self.save_config()

    def reset_to_defaults(self):
        """Restablecer configuración a valores por defecto"""
        self.config = self.default_config.copy()
        self.save_config()
        logger.log_info("Configuración de clasificación restablecida a valores por defecto")

    def get_config_status(self):
        """Obtener estado de la configuración"""
        return {
            'library_configured': os.path.exists(self.get('library_path')),
            'variable_patterns_enabled': self.get('variable_patterns.enabled', False),
            'custom_patterns_count': len(self.get('variable_patterns.custom_patterns', {})),
            'siglas_count': len(self.get('siglas_additional', {}))
        }