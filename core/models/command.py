# core/models/command.py (new, for CQRS Commands)
import uuid
from datetime import datetime

class Command:
    def __init__(self, command_type, parameters=None, actor=None, context=None):
        self.command_id = str(uuid.uuid4())
        self.command_type = command_type
        self.parameters = parameters or {}
        self.actor = actor  # ex. user_id
        self.context = context  # ex. role
        self.timestamp = datetime.utcnow()