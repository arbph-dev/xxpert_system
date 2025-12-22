# core/services/class_service.py

from core.models.event import Event

class ClassService:
    def __init__(self, repo):  # repo = KB
        self.repo = repo

    def add_class(self, name, parent=None):
        success = self.repo.add_class(name, parent)
        if success:
            event = Event("class_added", "class_service", entity=name)
            self.repo.store_event(event)
            return success, event
        return False, None