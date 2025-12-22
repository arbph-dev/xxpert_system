# /core/models/answer.py
"""
# dependance

    
# classes
	Answer

"""
class Answer:
    def __init__(self, question_id, value, value_type, source="human", confidence=1.0):
        self.answer_id = str(uuid.uuid4())
        self.question_id = question_id
        self.value = value
        self.value_type = value_type
        self.source = source
        self.confidence = confidence
        self.timestamp = datetime.utcnow()