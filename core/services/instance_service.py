# core/services/instance_service.py
# - Nouveau fichier pour gérer instances
# - Adapt to staged mode with WM

from core.models.command import Command
from core.models.event import Event, Severity
from core.workflow.working_memory import WorkingMemory

class InstanceService:
    def __init__(self, kb, wm: WorkingMemory):
        self.kb = kb  # For queries
        self.wm = wm

    def handle_command(self, cmd: Command):

        # add_instance
        if cmd.command_type == "add_instance":
            name = cmd.parameters.get("name")
            class_name = cmd.parameters.get("class_name")

            if not name or not isinstance(name, str):
                return Event("error", "instance_service", payload="Nom d'instance invalide ou manquant", severity=Severity.ERROR)
            if not class_name or not isinstance(class_name, str):
                return Event("error", "instance_service", payload="Nom de classe invalide ou manquant", severity=Severity.ERROR)

            success = self.wm.add_instance(name, class_name)  # Stage in WM
            if not success:
                return Event("add_instance_failed", "instance_service", entity=name, severity=Severity.ERROR, payload="Instance existe déjà ou classe inconnue")

            return Event("instance_proposed", "instance_service", entity=name)

        # delete_instance
        elif cmd.command_type == "delete_instance":
            name = cmd.parameters.get("name")
            class_name = cmd.parameters.get("class_name")

            if not name or not isinstance(name, str):
                return Event("error", "instance_service", payload="Nom d'instance invalide ou manquant", severity=Severity.ERROR)
            if not class_name or not isinstance(class_name, str):
                return Event("error", "instance_service", payload="Nom de classe invalide ou manquant", severity=Severity.ERROR)

            if not self.kb.delete_instance(name, class_name):
                return Event("error", "instance_service", payload=f"Impossible de supprimer l'instance '{name}' (inconnue ou erreur DB)", severity=Severity.ERROR)

            return Event("instance_deleted", "instance_service", entity=name)

        # modify_instance
        elif cmd.command_type == "modify_instance":
            name = cmd.parameters.get("name")
            class_name = cmd.parameters.get("class_name")
            new_name = cmd.parameters.get("new_name")

            if not name or not isinstance(name, str):
                return Event("error", "instance_service", payload="Nom d'instance invalide ou manquant", severity=Severity.ERROR)
            if not class_name or not isinstance(class_name, str):
                return Event("error", "instance_service", payload="Nom de classe invalide ou manquant", severity=Severity.ERROR)

            if not self.kb.modify_instance(name, class_name, new_name):
                return Event("error", "instance_service", payload=f"Impossible de modifier l'instance '{name}' (inconnue ou erreur)", severity=Severity.ERROR)

            return Event("instance_modified", "instance_service", entity=name)
        
        # delete_value
        elif cmd.command_type == "delete_value":
            name = cmd.parameters.get("inst_name")
            class_name = cmd.parameters.get("class_name")
            prop_name = cmd.parameters.get("prop_name")

            if not name or not isinstance(name, str):
                return Event("error", "instance_service", payload="Nom d'instance invalide", severity=Severity.ERROR)
            if not class_name or not isinstance(class_name, str):
                return Event("error", "instance_service", payload="Nom de classe invalide", severity=Severity.ERROR)
            if not prop_name or not isinstance(prop_name, str):
                return Event("error", "instance_service", payload="Nom de propriété invalide", severity=Severity.ERROR)

            if not self.kb.delete_instance_value(name, class_name, prop_name):
                return Event("error", "instance_service", payload=f"Impossible de supprimer la valeur de '{prop_name}' pour '{name}'", severity=Severity.ERROR)

            return Event("value_deleted", "instance_service", entity=f"{name}.{prop_name}")
        
        # modify_value
        elif cmd.command_type == "modify_value":
            name = cmd.parameters.get("inst_name")
            class_name = cmd.parameters.get("class_name")
            prop_name = cmd.parameters.get("prop_name")
            new_value = cmd.parameters.get("new_value")

            if not name or not isinstance(name, str):
                return Event("error", "instance_service", payload="Nom d'instance invalide", severity=Severity.ERROR)
            if not class_name or not isinstance(class_name, str):
                return Event("error", "instance_service", payload="Nom de classe invalide", severity=Severity.ERROR)
            if not prop_name or not isinstance(prop_name, str):
                return Event("error", "instance_service", payload="Nom de propriété invalide", severity=Severity.ERROR)
            if new_value is None:
                return Event("error", "instance_service", payload="Nouvelle valeur requise", severity=Severity.ERROR)

            if not self.kb.modify_instance_value(name, class_name, prop_name, new_value):
                return Event("error", "instance_service", payload=f"Impossible de modifier la valeur de '{prop_name}' pour '{name}'", severity=Severity.ERROR)

            return Event("value_modified", "instance_service", entity=f"{name}.{prop_name}")


        # Add for delete/modify similarly
        return Event("error", "instance_service", payload="Commande non supportée", severity=Severity.ERROR)