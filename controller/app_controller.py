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
from core.models.command import Command



class AppController:
    def __init__(self, kb: KnowledgeBase, ui: BaseUI):
        self.kb = kb
        self.ui = ui
        #self.wm = None
        self.wm = WorkingMemory(self.kb)
        self.um = UserManager(self.kb, self.wm)
        self.class_service = ClassService(self.kb, self.wm)
        
        #user_id, username, role = self.um.login(self.ui)  # Pass UI



    def run(self):
        # Login: Use questions if needed, mais pour l'instant as before
        user_id, username, role = self.um.login(self.ui)  # Update um pour use questions/ui
        
        self.ui.handle_event(Event("app_start", "AppController"))

        while True:
            # Define choices
            choices = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15"]
            if role == 'admin':
                choices += ["20", "21"]
            
            
            self.ui.show_menu(choices, role)  # Display the menu grid

            choice = self.ui.prompt_choice("[bold cyan]Votre choix[/bold cyan]", choices, default="1")

            if choice == "3":
                # In run, for choice == "3":
                name_q = Question("input", "class_name", "Nom de la classe")
                answer = self.ui.ask_question(name_q)
                parent_q = Question("choice", "parent", "Parent (optional)", choices=self.kb.get_all_class_names())
                parent_answer = self.ui.ask_question(parent_q)
                cmd = Command("add_class", parameters={"name": answer.value, "parent": parent_answer.value}, actor=user_id)
                event = self.class_service.handle_command(cmd)
                self.ui.handle_event(event)

            elif choice == "0":
                break