# core/services/property_service.py - Service pour propriétés avec gestion d'erreurs via Events
from core.models.command import Command
from core.models.event import Event, Severity
from core.workflow.working_memory import WorkingMemory

class PropertyService:
    def __init__(self, kb, wm: WorkingMemory):
        self.kb = kb
        self.wm = wm

    def handle_command(self, cmd: Command):
        # add_property  
        if cmd.command_type == "add_property":
            name = cmd.parameters.get("name")
            ptype = cmd.parameters.get("type", "string")
            class_name = cmd.parameters.get("class_name")  # Optionnel

            if not name or not isinstance(name, str):
                return Event("error", "property_service", payload="Nom de propriété invalide ou manquant", severity=Severity.ERROR)

            # Appel à KB, qui gère déjà les validations internes
            if not self.kb.add_property(name, ptype):
                return Event("error", "property_service", payload=f"Impossible d'ajouter la propriété '{name}' (existe déjà ou type invalide)", severity=Severity.ERROR)

            if class_name:
                if not self.kb.attach_property_to_class(class_name, name):
                    return Event("error", "property_service", payload=f"Impossible d'attacher '{name}' à la classe '{class_name}'", severity=Severity.ERROR)

            return Event("property_added", "property_service", entity=name)
        
        # delete_property            
        elif cmd.command_type == "delete_property":
            name = cmd.parameters.get("name")

            if not name or not isinstance(name, str):
                return Event("error", "property_service", payload="Nom de propriété invalide ou manquant", severity=Severity.ERROR)

            if not self.kb.delete_property(name):
                return Event("error", "property_service", payload=f"Impossible de supprimer la propriété '{name}' (inconnue ou erreur DB)", severity=Severity.ERROR)

            return Event("property_deleted", "property_service", entity=name)
        
        # modify_property
        elif cmd.command_type == "modify_property":
            name = cmd.parameters.get("name")
            new_name = cmd.parameters.get("new_name")  # Nouveau param pour rename
            new_type = cmd.parameters.get("new_type")  # Optionnel

            if not name or not isinstance(name, str):
                return Event("error", "property_service", payload="Nom de propriété invalide ou manquant", severity=Severity.ERROR)

            if not self.kb.modify_property(name, new_name, new_type):
                return Event("error", "property_service", payload=f"Impossible de modifier la propriété '{name}' (inconnue ou erreur)", severity=Severity.ERROR)

            return Event("property_modified", "property_service", entity=name)  # Ou new_name si rename

        else :            
            # À ajouter plus tard pour modify/delete
            return Event("error", "property_service", payload="Commande non supportée", severity=Severity.ERROR)