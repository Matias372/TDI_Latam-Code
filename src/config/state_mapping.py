"""
SISTEMA UNIFICADO DE MAPEO DE ESTADOS

Este archivo centraliza todos los mapeos de estados entre Freshdesk y Clarity.

EXPLICACIÓN:
- Freshdesk usa dos representaciones de estados:
  1. NUMÉRICA: Cuando se consulta por API (usado en processes.py)
  2. TEXTUAL:  Cuando se exporta a Excel/CSV (usado en sync_processes.py)

- Clarity siempre usa representación textual.
"""

# =============================================================================
# MAPEO PARA ESTADOS NUMÉRICOS (API Freshdesk)
# Usado en: processes.py (envío de notas internas)
# =============================================================================
MAPEO_ESTADOS_FD_API_A_CLARITY = {
    2: "Abierta",                    # Open
    3: "En evaluación",              # Pending -> En evaluación
    4: "Resuelto",                   # Resolved
    5: "Cerrada",                    # Closed
    6: "Esperando al cliente",       # Waiting on Customer
    7: "Derivado al fabricante",     # Forwarded to Manufacturer
    9: "En progreso",                # In Progress
    13: "En evaluación"              # Specific state -> En evaluación
}

# =============================================================================
# MAPEO PARA ESTADOS TEXTUALES (Archivos Excel/CSV)
# Usado en: sync_processes.py (sincronización desde archivos)
# =============================================================================
MAPEO_ESTADOS_FD_TEXTO_A_CLARITY = {
    "Open": "Abierta",
    "Closed": "Cerrada", 
    "Resolved": "Resuelto",
    "Derivado al Fabricante": "Derivado al Fabricante",
    "En evaluación": "En evaluación",
    "En progreso": "En progreso",
    "Esperando al cliente": "Esperando al cliente"
}

# =============================================================================
# ESTADOS VÁLIDOS EN CLARITY (para referencia y validación)
# =============================================================================
ESTADOS_CLARITY_VALIDOS = [
    "Abierta", 
    "En evaluación",
    "En progreso", 
    "Esperando al cliente",
    "Derivado al fabricante",
    "Resuelto",
    "Cerrada"
]

# =============================================================================
# FUNCIONES HELPER PARA FACILITAR EL USO
# =============================================================================

def mapear_estado_desde_api(estado_numerico: int) -> str:
    """Mapear estado numérico de API Freshdesk a Clarity"""
    return MAPEO_ESTADOS_FD_API_A_CLARITY.get(estado_numerico, "Ninguno")

def mapear_estado_desde_texto(estado_texto: str) -> str:
    """Mapear estado textual de archivo Freshdesk a Clarity"""
    # Limpieza básica del texto para mayor robustez
    if estado_texto:
        estado_limpio = estado_texto.strip()
        return MAPEO_ESTADOS_FD_TEXTO_A_CLARITY.get(estado_limpio, "Ninguno")
    return "Ninguno"

def es_estado_clarity_valido(estado: str) -> bool:
    """Validar si un estado es aceptado por Clarity"""
    return estado in ESTADOS_CLARITY_VALIDOS

def obtener_estados_api_disponibles() -> list:
    """Obtener lista de estados numéricos válidos para la API"""
    return list(MAPEO_ESTADOS_FD_API_A_CLARITY.keys())

def obtener_estados_texto_disponibles() -> list:
    """Obtener lista de estados textuales válidos para archivos"""
    return list(MAPEO_ESTADOS_FD_TEXTO_A_CLARITY.keys())