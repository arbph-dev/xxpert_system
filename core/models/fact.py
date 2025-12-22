# /core/models/fact.py
"""
# dependance

    
# classes
	FactStatus
	FactSource
	Fact



class Facts:
    def __init__(self, fact_store, repository):
        self.fact_store = fact_store
        self.repo = repository
        self.changes = []

    def add_instance(self, name, class_name):
        self.changes.append({"action": "add_instance", "data": {"name": name, "class_name": class_name}})

    def submit(self, user_id, description):
        # ... (soumission des changements)

| Champ          | Type logique | Obligatoire | Description                         |
| -------------- | ------------ | ----------- | ----------------------------------- |
| `fact_id`      | UUID         | ✔           | Identifiant unique                  |
| `entity_type`  | enum         | ✔           | `class`, `instance`, `job`, `event` |
| `entity_id`    | string / int | ✔           | Identifiant de l’entité             |
| `property`     | string       | ✔           | Nom canonique de la propriété       |
| `value`        | any          | ✔           | Valeur portée par le Fact           |
| `value_type`   | enum         | ✔           | Type logique de la valeur           |
| `unit`         | string       | ⛔           | Unité SI                            |
| `confidence`   | float (0–1)  | ✔           | Niveau de certitude                 |
| `source`       | enum         | ✔           | Origine du Fact                     |
| `status`       | enum         | ✔           | État du Fact                        |
| `timestamp`    | datetime     | ✔           | Date de création                    |
| `valid_from`   | datetime     | ⛔           | Début de validité                   |
| `valid_to`     | datetime     | ⛔           | Fin de validité                     |
| `derived_from` | list[UUID]   | ⛔           | Facts parents                       |
| `rule_id`      | string       | ⛔           | Règle / modèle à l’origine          |
| `comment`      | string       | ⛔           | Justification libre                 |


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