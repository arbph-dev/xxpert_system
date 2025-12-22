# /core/models/fact.py
"""
# dependance

    
# classes
	FactStatus
	FactSource
	Fact
"""

class FactStatus:
    ASSERTED = "asserted"
    UNKNOWN = "unknown"
    # ... (ajoute autres plus tard)

class FactSource:
    USER = "user"
    # ... 

class Fact:
    def __init__(self, entity_type, entity_id, property_name, value, value_type, unit=None, confidence=1.0, source=FactSource.USER, status=FactStatus.ASSERTED):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.property = property_name
        self.value = value
        self.value_type = value_type
        self.unit = unit
        self.confidence = confidence
        self.source = source
        self.status = status