# core/services/class_service.py (handle Commands, use repo/WM, emit Events, apply rules)
from core.models.event import Event

class ClassService:
    def __init__(self, repo, wm):
        self.repo = repo
        self.wm = wm

    def handle_command(self, cmd):
        if cmd.command_type == "add_class":
            name = cmd.parameters.get('name')
            parent = cmd.parameters.get('parent')
            success = self.wm.add_class(name, parent)  # Use WM for staging
            if success:
                return Event("class_proposed", "class_service", entity=name, payload={"parent": parent})
            return Event("add_class_failed", "class_service", entity=name, severity=Severity.WARNING, payload="Class exists")
        # Extend for other commands