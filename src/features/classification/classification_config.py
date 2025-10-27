# 📁 src/config/classification_config.py (ACTUALIZADO)

CLASSIFICATION_CONFIG = {
    "library_path": "data/classification/biblioteca_clasificacion_tickets.json",
    "confidence_thresholds": {
        "high": 100,
        "medium": 50, 
        "low": 10,
        "minimal": 2
    },
    "max_recommendations": 3,
    "supported_fields": [
        "Tipo de Ticket",
        "Segmento",
        "Fabricante", 
        "Producto",
        "Nombre del grupo"
    ],
    "siglas_additional": {
        "APM": "apm",
        "CMDB": "cmdb",
        "ITSM": "itsm"
    },
    # 🆕 NUEVA SECCIÓN PARA PATRONES VARIABLES
    "variable_patterns": {
        "enabled": True,
        "server_patterns": [
            r'pwcauimapp\d+',
            r'appserver\d+',
            r'dbserver\d+',
            r'webapp\d+',
            r'srv\d+'
        ],
        "normalized_to": {
            "pwcauimapp": "servidor aplicacion uim",
            "appserver": "servidor aplicaciones",
            "dbserver": "servidor base datos",
            "webapp": "aplicacion web",
            "srv": "servidor"
        },
        "custom_patterns": {}
    }
}