# /core/question.py
"""
# dependance
    uuid
    
# classes
    Question
"""

import uuid

class Question:
    def __init__(self, question_type, target, prompt, expected_type="string", unit=None, choices=None, default=None, mandatory=True, context=None):
        self.question_id = str(uuid.uuid4())
        self.question_type = question_type
        self.target = target
        self.prompt = prompt
        self.expected_type = expected_type
        self.unit = unit
        self.choices = choices
        self.default = default
        self.mandatory = mandatory
        self.context = context
