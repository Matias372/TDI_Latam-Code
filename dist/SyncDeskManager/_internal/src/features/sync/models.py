from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class TicketDifference:
    ticket_id: str
    freshdesk_estado: str
    clarity_estado_actual: str
    clarity_estado_propuesto: str
    investment_id: Optional[str] = None
    clarity_internal_id: Optional[str] = None

@dataclass
class SyncResult:
    exitos: int
    fallos: int
    detalles: List[Dict]
    total_cambios: int

@dataclass
class FileValidationResult:
    es_valido: bool
    mensaje: str
    df_freshdesk: Optional = None
    df_clarity: Optional = None