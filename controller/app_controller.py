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

        self.current_class_name = None
        self.current_class_id = -1



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
            "15: Exécuter inférence backward",
            "16: Modifier valeur propriété instance",
            "17: Supprimer valeur propriété instance",
            "18: Afficher valeurs instance"
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
            # For add_class (already using WM)
            event = self.class_service.handle_command(cmd)
            self.kb.store_event(event) #stocke en db
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
            # Similar for property and instance
            event = self.property_service.handle_command(cmd)  # Assume self.property_service = PropertyService(self.kb, self.wm)
            self.kb.store_event(event) #stocke en db
            self.ui.handle_event(event)
        
        # Ajouter instance
        elif choice_num == "5":
            name_q = Question("input", "inst_name", "Nom de l'instance")
            answer = self.ui.ask_question(name_q)
            #if not answer.value:
            #    return

            class_q = Question("choice", "class_name", "Classe associée", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            # class_name = class_answer.value.strip() if class_answer.value else None
            #if not class_name:
            #    self.ui.handle_event(Event("info", "controller", payload="Aucune classe spécifiée"))
            #    return

            cmd = Command("add_instance", parameters={"name": answer.value, "class_name": class_answer.value}, actor=self.user_id)
            #cmd = Command("add_instance", parameters={"name": answer.value, "class_name": class_name}, actor=self.user_id)
            event = self.instance_service.handle_command(cmd)  # Assume self.instance_service = InstanceService(self.kb, self.wm)
            self.kb.store_event(event) #stocke en db
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
            # self.kb.store_event(event) #stocke en db
            self.ui.handle_event(event)

        # "8 : Modifier instance"
        elif choice_num == "8":
            class_q = Question("choice", "class_name", "Classe de l'instance", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            if not class_answer.value:
                return

            name_q = Question("choice", "inst_name", "Instance à modifier", choices=self.kb.get_all_instances(class_answer.value))
            answer = self.ui.ask_question(name_q)
            if not answer.value:
                return

            new_name_q = Question("input", "new_name", "Nouveau nom (laisser vide pour ignorer)")
            new_name_answer = self.ui.ask_question(new_name_q)
            new_name = new_name_answer.value.strip() if new_name_answer.value else None

            if not new_name:
                self.ui.handle_event(Event("info", "controller", payload="Aucune modification spécifiée"))
                return

            cmd = Command("modify_instance", parameters={"name": answer.value, "class_name": class_answer.value, "new_name": new_name}, actor=self.user_id)
            event = self.instance_service.handle_command(cmd)
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
            # self.kb.store_event(event) #stocke en db
            self.ui.handle_event(event)        

        # "11 : Supprimer instance"
        elif choice_num == "11":
            class_q = Question("choice", "class_name", "Classe de l'instance", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            if not class_answer.value:
                return

            name_q = Question("choice", "inst_name", "Instance à supprimer", choices=self.kb.get_all_instances(class_answer.value))
            answer = self.ui.ask_question(name_q)
            if not answer.value:
                return

            confirm = self.ui.confirm(f"Confirmer la suppression de '{answer.value}' dans '{class_answer.value}' ? Cela effacera les valeurs associées.")
            if not confirm:
                return

            cmd = Command("delete_instance", parameters={"name": answer.value, "class_name": class_answer.value}, actor=self.user_id)
            event = self.instance_service.handle_command(cmd)
            self.ui.handle_event(event)


        # "12: Lister propriétés d'une classe"
        elif choice_num == "12":
            class_q = Question("choice", "class_name", "Classe à lister propriétés", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            event = Event("table_requested", "controller", payload={"table_name": "props", "filter": {"class_name": class_answer.value}})
            self.ui.handle_event(event)
        
        # "16 : Modifier valeur"
        elif choice_num == "16":
            class_q = Question("choice", "class_name", "Classe de l'instance", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            if not class_answer.value:
                return

            inst_q = Question("choice", "inst_name", "Instance", choices=self.kb.get_all_instances(class_answer.value))
            inst_answer = self.ui.ask_question(inst_q)
            if not inst_answer.value:
                return

            prop_q = Question("choice", "prop_name", "Propriété à modifier", choices=self.kb.get_all_props_for_class(class_answer.value))
            prop_answer = self.ui.ask_question(prop_q)
            if not prop_answer.value:
                return

            # Fetch current value for display (optional)
            current_value = self.kb.get_instance_value(inst_answer.value, class_answer.value, prop_answer.value)
            value_q = Question("input", "new_value", f"Nouvelle valeur pour '{prop_answer.value}' (current: {current_value})")
            value_answer = self.ui.ask_question(value_q)
            if not value_answer.value:
                return

            cmd = Command("modify_value", parameters={"inst_name": inst_answer.value, "class_name": class_answer.value, "prop_name": prop_answer.value, "new_value": value_answer.value}, actor=self.user_id)
            event = self.instance_service.handle_command(cmd)
            self.ui.handle_event(event)
        
        # "17 : Supprimer valeur"
        elif choice_num == "17":  
            class_q = Question("choice", "class_name", "Classe de l'instance", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            if not class_answer.value:
                return

            inst_q = Question("choice", "inst_name", "Instance", choices=self.kb.get_all_instances(class_answer.value))
            inst_answer = self.ui.ask_question(inst_q)
            if not inst_answer.value:
                return

            prop_q = Question("choice", "prop_name", "Propriété à supprimer", choices=self.kb.get_all_props_for_class(class_answer.value))
            prop_answer = self.ui.ask_question(prop_q)
            if not prop_answer.value:
                return

            confirm = self.ui.confirm(f"Confirmer la suppression de la valeur pour '{prop_answer.value}' dans '{inst_answer.value}' ?")
            if not confirm:
                return

            cmd = Command("delete_value", parameters={"inst_name": inst_answer.value, "class_name": class_answer.value, "prop_name": prop_answer.value}, actor=self.user_id)
            event = self.instance_service.handle_command(cmd)
            self.ui.handle_event(event)

        #"18: Afficher valeurs instance"
        elif choice_num == "18":
            class_q = Question("choice", "class_name", "Classe de l'instance", choices=self.kb.get_all_class_names())
            class_answer = self.ui.ask_question(class_q)
            if not class_answer.value:
                return

            inst_q = Question("choice", "inst_name", "Instance à afficher", choices=self.kb.get_all_instances(class_answer.value))
            inst_answer = self.ui.ask_question(inst_q)
            if not inst_answer.value:
                return

            # Call UI method to load and display
            self.ui.load_instance_values(inst_answer.value, class_answer.value)

            # Optional: log event
            event = Event("instance_values_viewed", "controller", entity=inst_answer.value)
            self.kb.store_event(event)

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
                self.current_class_name = event.payload.get("class_name")
                self.current_class_id = self.kb.get_class_id(self.current_class_name)
                # Exemple : charger les propriétés de la classe dans le table tab
                columns = ["Name"]
                rows = [(prop,) for prop in self.kb.get_all_props_for_class(class_name)]
                self.ui.show_table(f"Props de {class_name}", columns, rows)
        # No run() with while; all async via events/choices