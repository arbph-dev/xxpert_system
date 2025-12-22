# core/workflow/working_memory.py
import json
from rich.console import Console
from rich.panel import Panel
from core.models.event import Event

console = Console()

class WorkingMemory:
    def __init__(self, kb):
        self.kb = kb
        self.changes = []  # Liste de deltas
        self.temporary = {}  # Tampon pour instances/classes locales (pour simulation)

    def add_change(self, action, data):
        self.changes.append({"action": action, "data": data})

    # Méthodes mirror (exemples - étendre au besoin)
    def add_class(self, name, parent=None):
        console.print(f"[yellow]WM: Simulation ajout classe '{name}'[/]")
        self.add_change('add_class', {'name': name, 'parent': parent})
        self.temporary.setdefault('classes', []).append(name)
        event = Event("class_added", "workingMemory", entity=name)
        # return True
        #self.kb.self.store_event(event)
        return True, event  # return True, Event("class_added", "database", entity=name)  # Return tuple (success, event)
        self.kb.self.store_event(event)


    def add_instance(self, name, class_name):
        console.print(f"[yellow]WM: Simulation ajout instance '{name}' dans '{class_name}'[/]")
        self.add_change('add_instance', {'name': name, 'class_name': class_name})
        return True

    def add_property(self, name, ptype='string'):
        console.print(f"[yellow]WM: Simulation ajout propriété '{name}' ({ptype})[/]")
        self.add_change('add_property', {'name': name, 'ptype': ptype})
        return True

    def set_instance_value(self, inst_name, class_name, prop_name, value):
        console.print(f"[yellow]WM: Simulation saisie {prop_name} = {value} pour {inst_name}[/]")
        self.add_change('set_value', {'inst_name': inst_name, 'class_name': class_name, 'prop_name': prop_name, 'value': value})
        return True

    # ... Ajoute mirror pour autres actions (link_prop, etc.)

    def submit(self, user_id, description):
        changes_json = json.dumps(self.changes)
        self.kb.cursor.execute("""
            INSERT INTO se_submissions (user_id, description, changes_json)
            VALUES (?, ?, ?)
        """, (user_id, description, changes_json))
        self.kb.commit()
        console.print(Panel("[bold green]Soumission enregistrée pour validation[/bold green]", style="green"))
        self.changes = []  # Reset après soumission
        return True


    def get_temp_classes(self):
        official = self.kb.get_all_class_names()
        temp = [c['data']['name'] for c in self.changes if c['action'] == 'add_class']
        return list(set(official + temp))

    def get_temp_instances(self, class_name):
        official = self.kb.get_all_instances(class_name)
        temp = [c['data']['name'] for c in self.changes if c['action'] == 'add_instance' and c['data']['class_name'] == class_name]
        return list(set(official + temp))

    def get_temp_properties(self):
        official = self.kb.get_all_property_names()
        temp = [c['data']['name'] for c in self.changes if c['action'] == 'add_property']
        return list(set(official + temp))

    def get_temp_value(self, inst_name, class_name, prop_name):
        # Valeur officielle si existe, sinon temp
        official = self.kb.get_instance_value(inst_name, class_name, prop_name)
        for c in reversed(self.changes):  # Dernier changement gagne
            if c['action'] == 'set_value' and c['data']['inst_name'] == inst_name and c['data']['class_name'] == class_name and c['data']['prop_name'] == prop_name:
                return c['data']['value']
        return official       