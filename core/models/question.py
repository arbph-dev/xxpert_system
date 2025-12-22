# /core/question.py
"""
# dependance
    uuid
    
# classes
    Question


| Champ           | Description                          |
| --------------- | ------------------------------------ |
| `question_id`   | Identifiant unique                   |
| `question_type` | valeur / choix / validation          |
| `target`        | Propriété / Classe / Instance        |
| `prompt`        | Texte explicatif                     |
| `expected_type` | bool / number / enum / text          |
| `unit`          | Unité SI si applicable               |
| `choices`       | Liste possible (si enum)             |
| `default`       | Valeur par défaut                    |
| `mandatory`     | bool                                 |
| `context`       | Contexte métier (job, règle, source) |



"""

import uuid

class Question:
    def __init__(
        self,
        question_type,
        target,
        prompt,
        *,
        expected_type="string",
        unit=None,
        choices=None,
        default=None,
        mandatory=True,
        constraints=None,
        context=None,
        status="open",
    ):
        self.question_id = str(uuid.uuid4())
        self.question_type = question_type
        self.target = target
        self.prompt = prompt
        self.expected_type = expected_type
        self.unit = unit
        self.choices = choices
        self.default = default
        self.mandatory = mandatory
        self.constraints = constraints  # dict: min, max, regex, enum, etc.
        self.context = context
        self.status = status             # open | answered | cancelled | expired
