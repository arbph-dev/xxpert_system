# core/services/property_service.py - Nouveau fichier pour gérer propriétés
from core.models.command import Command
from core.models.event import Event, Severity
from core.workflow.working_memory import WorkingMemory

class PropertyService:
    def __init__(self, kb, wm: WorkingMemory):
        self.kb = kb
        self.wm = wm

    def handle_command(self, cmd: Command):
        if cmd.command_type == "add_property":
            name = cmd.parameters.get("name")
            ptype = cmd.parameters.get("type", "string")
            class_name = cmd.parameters.get("class_name")  # Optionnel pour attacher à classe
            if self.kb.get_property_id(name):
                return Event("error", "property_service", payload=f"Propriété '{name}' existe déjà", severity=Severity.ERROR)
            self.kb.add_property(name, ptype)  # Assume méthode existante ou à ajouter dans database.py
            if class_name:
                self.kb.attach_property_to_class(class_name, name)
            return Event("property_added", "property_service", entity=name)
        # Ajouter pour modify/delete si besoin