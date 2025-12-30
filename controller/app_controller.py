# controller/app_controller.py (updated with proper prompt_choice call)

from core.database import KnowledgeBase
#from core.repository import Repository
from core.workflow.working_memory import WorkingMemory
from core.auth.user import UserManager
from ui.base_ui import BaseUI
from ui.console_ui import ConsoleUI
from core.models.event import Event
from core.models.question import Question
from core.services.class_service import ClassService
from core.services.property_service import PropertyService
from core.services.instance_service import InstanceService
from core.models.command import Command



class AppController:
    def __init__(self, kb: KnowledgeBase, ui: BaseUI):
        self.kb = kb
        self.ui = ui
        #self.wm = None
        self.wm = WorkingMemory(self.kb)
        
        self.um = UserManager(self.kb) # self.um = UserManager(self.kb, self.wm)

        self.class_service = ClassService(self.kb, self.wm)
        self.property_service = PropertyService(self.kb, self.wm)
        self.instance_service = InstanceService(self.kb, self.wm)
        #user_id, username, role = self.um.login(self.ui)  # Pass UI


    def init_logic(self):
        user_id, username, role = self.um.login(self.ui)
        self.user_id = user_id  # Store for commands
        self.role = role
        self.wm = WorkingMemory(self.kb)
        # choices = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15"]
        # if role == 'admin':
        #    choices += ["20", "21"]

        choices = [
            "0: Quitter",
            "1: Lister classes",
            "2: Lister instances",
            "3: Ajouter classe",
            "4: Ajouter propriété",
            "5: Ajouter instance",
            "6: Modifier classe",
            "7: Modifier propriété",
            "8: Modifier instance",
            "9: Supprimer classe",
            "10: Supprimer propriété",
            "11: Supprimer instance",
            "12: Lister propriétés d'une classe",
            "13: Lister instances d'une classe",
            "14: Exécuter inférence forward",
            "15: Exécuter inférence backward"
        ]
        if role == 'admin':
            choices += [
                "20: Valider submissions",
                "21: Gérer utilisateurs"
            ]

        self.ui.handle_event(Event("app_start", "controller"))
        self.ui.handle_event(Event("menu_requested", "controller", payload={"choices": choices, "role": role}))

    def handle_choice(self, choice):
        # Extraire le numéro de la choice (ex: "2: Lister instances" → "2")
        choice_num = choice.split(":")[0].strip()
        # Lister classes
        if choice_num == "1":
            event = Event("table_requested", "controller", payload={"table_name": "classes"})
            self.ui.handle_event(event)
        
        # Lister instances
        elif choice_num == "2":  
            event = Event("table_requested", "controller", payload={"table_name": "instances"})
            self.ui.handle_event(event)
        
        # Ajouter classes
        elif choice_num == "3":  
            name_q = Question("input", "class_name", "Nom de la classe")
            answer = self.ui.ask_question(name_q)
            parent_q = Question("choice", "parent", "Parent (optional)", choices=self.kb.get_all_class_names())
            parent_answer = self.ui.ask_question(parent_q)
            cmd = Command("add_class", parameters={"name": answer.value, "parent": parent_answer.value}, actor=self.user_id)
            event = self.class_service.handle_command(cmd)
            self.ui.handle_event(event)
        
        # Ajouter propriété
        elif choice_num == "4":  
            name_q = Question("input", "prop_name", "Nom de la propriété")
            answer = self.ui.ask_question(name_q)
            type_q = Question("choice", "type", "Type de propriété", choices=["string", "int", "float", "bool"])
            type_answer = self.ui.ask_question(type_q)
            class_q = Question("choice", "class_name", "Attacher à classe (optional)", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            cmd = Command("add_property", parameters={"name": answer.value, "type": type_answer.value, "class_name": class_answer.value}, actor=self.user_id)
            event = self.property_service.handle_command(cmd)  # Assume self.property_service = PropertyService(self.kb, self.wm)
            self.ui.handle_event(event)
        
        # Ajouter instance
        elif choice_num == "5":
            name_q = Question("input", "inst_name", "Nom de l'instance")
            answer = self.ui.ask_question(name_q)
            class_q = Question("choice", "class_name", "Classe associée", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            cmd = Command("add_instance", parameters={"name": answer.value, "class_name": class_answer.value}, actor=self.user_id)
            event = self.instance_service.handle_command(cmd)  # Assume self.instance_service = InstanceService(self.kb, self.wm)
            self.ui.handle_event(event)
        # "6: Modifier classe"
        
        # "7: Modifier propriété"
        elif choice_num == "7":  
            name_q = Question("choice", "prop_name", "Propriété à modifier", choices=self.kb.get_all_property_names())
            answer = self.ui.ask_question(name_q)
            if not answer.value:
                return

            new_name_q = Question("input", "new_name", "Nouveau nom (laisser vide pour ignorer)")
            new_name_answer = self.ui.ask_question(new_name_q)
            new_name = new_name_answer.value.strip() if new_name_answer.value else None

            type_q = Question("choice", "new_type", "Nouveau type (laisser vide pour ignorer)", choices=["", "string", "int", "float", "bool"])
            type_answer = self.ui.ask_question(type_q)
            new_type = type_answer.value if type_answer.value else None

            if not new_name and not new_type:
                self.ui.handle_event(Event("info", "controller", payload="Aucune modification spécifiée"))
                return

            cmd = Command("modify_property", parameters={"name": answer.value, "new_name": new_name, "new_type": new_type}, actor=self.user_id)
            event = self.property_service.handle_command(cmd)
            self.ui.handle_event(event)
            
        # "10: Supprimer propriété"
        elif choice_num == "10":
            name_q = Question("choice", "prop_name", "Propriété à supprimer", choices=self.kb.get_all_property_names())
            answer = self.ui.ask_question(name_q)
            if not answer.value:
                return

            confirm = self.ui.confirm(f"Confirmer la suppression de '{answer.value}' ? Cela effacera les liens et valeurs associées.")
            if not confirm:
                return

            cmd = Command("delete_property", parameters={"name": answer.value}, actor=self.user_id)
            event = self.property_service.handle_command(cmd)
            self.ui.handle_event(event)        
        
        # "12: Lister propriétés d'une classe"
        elif choice_num == "12":
            class_q = Question("choice", "class_name", "Classe à lister propriétés", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            event = Event("table_requested", "controller", payload={"table_name": "props", "filter": {"class_name": class_answer.value}})
            self.ui.handle_event(event)
        
        # Pour admin: "20" lister pending submissions, etc.
        elif choice_num == "20" and self.role == 'admin':
            # Logic pour valider submissions (utiliser get_pending_submissions)
            pass
        
        elif choice_num == "0":
            QApplication.quit()
        # Add other choices

    # No run() with while; all async via events/choices


    def handle_event(self, event: Event):
        if event.event_type == "class_selected":
            class_name = event.payload.get("class_name")
            if class_name:
                # Exemple : charger les propriétés de la classe dans le table tab
                columns = ["Name"]
                rows = [(prop,) for prop in self.kb.get_all_props_for_class(class_name)]
                self.ui.show_table(f"Props de {class_name}", columns, rows)
        # No run() with while; all async via events/choices