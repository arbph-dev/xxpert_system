# core/services/property_service.py
#  - Service pour propriétés avec gestion d'erreurs via Events
#  - Adapt to staged mode with WM

from core.models.command import Command
from core.models.event import Event, Severity
from core.workflow.working_memory import WorkingMemory

class PropertyService:
    def __init__(self, kb, wm: WorkingMemory):
        self.kb = kb  # Keep for queries, but writes go to WM
        self.wm = wm

    def handle_command(self, cmd: Command):
        # add_property
        if cmd.command_type == "add_property":
            name = cmd.parameters.get("name")
            ptype = cmd.parameters.get("type", "string")
            class_name = cmd.parameters.get("class_name")

            if not name or not isinstance(name, str):
                return Event("error", "property_service", payload="Nom de propriété invalide ou manquant", severity=Severity.ERROR)

            success = self.wm.add_property(name, ptype)  # Stage in WM
            if not success:
                return Event("add_property_failed", "property_service", entity=name, severity=Severity.ERROR, payload="Propriété existe déjà ou type invalide")

            if class_name:
                success = self.wm.attach_property_to_class(class_name, name)
                if not success:
                    return Event("error", "property_service", payload=f"Impossible d'attacher '{name}' à '{class_name}'", severity=Severity.ERROR)

            return Event("property_proposed", "property_service", entity=name)  # Changed to "proposed" for staged mode
        # delete_property
        elif cmd.command_type == "delete_property":
            name = cmd.parameters.get("name")

            if not name or not isinstance(name, str):
                return Event("error", "property_service", payload="Nom de propriété invalide ou manquant", severity=Severity.ERROR)

            success = self.wm.delete_property(name)  # Stage deletion in WM
            if not success:
                return Event("delete_property_failed", "property_service", entity=name, severity=Severity.ERROR, payload="Propriété inconnue ou erreur")

            return Event("property_deletion_proposed", "property_service", entity=name)
        # modify_property
        elif cmd.command_type == "modify_property":
            name = cmd.parameters.get("name")
            new_name = cmd.parameters.get("new_name")
            new_type = cmd.parameters.get("new_type")

            if not name or not isinstance(name, str):
                return Event("error", "property_service", payload="Nom de propriété invalide ou manquant", severity=Severity.ERROR)
            success = self.wm.modify_property(name, new_name, new_type)  # Stage modification in WM

            if not success:
                return Event("modify_property_failed", "property_service", entity=name, severity=Severity.ERROR, payload="Modification impossible")
            return Event("property_modification_proposed", "property_service", entity=name)
        else:
            return Event("error", "property_service", payload="Commande non supportée", severity=Severity.ERROR)