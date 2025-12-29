# core/services/instance_service.py - Nouveau fichier pour gérer instances
from core.models.command import Command
from core.models.event import Event, Severity
from core.workflow.working_memory import WorkingMemory

class InstanceService:
    def __init__(self, kb, wm: WorkingMemory):
        self.kb = kb
        self.wm = wm

    def handle_command(self, cmd: Command):
        if cmd.command_type == "add_instance":
            name = cmd.parameters.get("name")
            class_name = cmd.parameters.get("class_name")
            if self.kb.instance_exists(name, class_name):  # Assume méthode à ajouter
                return Event("error", "instance_service", payload=f"Instance '{name}' existe déjà pour '{class_name}'", severity=Severity.ERROR)
            self.kb.add_instance(name, class_name)
            return Event("instance_added", "instance_service", entity=name)
        # Ajouter pour modify/delete