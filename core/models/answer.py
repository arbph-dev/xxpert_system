# /core/models/answer.py
"""
# dependance

    
# classes
	Answer

"""
import uuid
from datetime import datetime

class Answer:
    def __init__(
        self,
        question_id,
        value,
        value_type,
        *,
        status="provided",
        unit=None,
        source="human",
        actor=None,
        confidence=1.0,
        comment=None,
    ):
    
        self.answer_id = str(uuid.uuid4())
        self.question_id = question_id
        self.value = value
        self.value_type = value_type
        self.status = status            # provided | estimated | unknown | rejected | invalid
        self.unit = unit
        self.source = source            # human | expert | api | ml | system
        self.actor = actor              # username / agent_id / system
        self.confidence = confidence
        self.comment = comment
        self.timestamp = datetime.utcnow()
