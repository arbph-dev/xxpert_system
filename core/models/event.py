# /core/models/event.py
"""
# dependance
    datetime
    
# classes
    Severity
    Event

| Champ        | Description                                          |
| ------------ | ---------------------------------------------------- |
| `event_type` | Type sémantique (ex: `value_deduced`, `job_created`) |
| `source`     | Module émetteur (`inference`, `workflow`, `stats`)   |
| `entity`     | Classe / Instance / Job concerné                     |
| `payload`    | Données métier (valeur, règle, seuil, etc.)          |
| `severity`   | info / warning / error                               |
| `timestamp`  | Horodatage                                           |



"""
from datetime import datetime


class Severity:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class Event:
    def __init__(self, event_type, source, entity=None, payload=None, severity=Severity.INFO):
        self.event_type = event_type
        self.source = source
        self.entity = entity
        self.payload = payload
        self.severity = severity
        self.timestamp = datetime.utcnow()