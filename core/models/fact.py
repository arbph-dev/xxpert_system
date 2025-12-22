# /core/models/fact.py
"""
# dependance

    
# classes
	FactStatus
	FactSource
	Fact
"""
import uuid
from datetime import datetime

class FactStatus:
    ASSERTED = "asserted"
    UNKNOWN = "unknown"
    # ... (ajoute autres plus tard)

class FactSource:
    USER = "user"
    # ... 

class Fact:
    def __init__(
        self,
        *,
        entity_type,
        entity_id,
        property_name,
        value,
        value_type,
        unit=None,
        source="system",
        actor=None,
        confidence=1.0,
        status="active",
        origin="inference",
        related_question_id=None,
        related_answer_id=None,
        job_id=None,
        metadata=None,
    ):
        self.fact_id = str(uuid.uuid4())

        # Cible
        self.entity_type = entity_type        # class | instance | job
        self.entity_id = entity_id
        self.property_name = property_name

        # Valeur
        self.value = value
        self.value_type = value_type
        self.unit = unit

        # Qualité / gouvernance
        self.status = status                  # active | inactive | superseded | rejected
        self.confidence = confidence
        self.source = source                  # human | expert | api | ml | system
        self.actor = actor
        self.origin = origin                  # input | inference | api | correction

        # Traçabilité
        self.related_question_id = related_question_id
        self.related_answer_id = related_answer_id
        self.job_id = job_id

        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at