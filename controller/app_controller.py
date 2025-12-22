# controller/app_controller.py (updated with proper prompt_choice call)

from core.database import KnowledgeBase
from core.workflow.working_memory import WorkingMemory
from core.auth.user import UserManager
from ui.base_ui import BaseUI
from core.models.event import Event
from core.models.question import Question

class AppController:
    def __init__(self, kb: KnowledgeBase, ui: BaseUI):
        self.kb = kb
        self.ui = ui
        self.um = UserManager(kb)
        self.wm = None

    def run(self):
        # Login: Use questions if needed, mais pour l'instant as before
        user_id, username, role = self.um.login()  # Update um pour use questions/ui
        self.wm = WorkingMemory(self.kb)
        self.ui.handle_event(Event("app_start", "AppController"))

        while True:
            # Define choices
            choices = ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15"]
            if role == 'admin':
                choices += ["20", "21"]
            
            
            self.ui.show_menu(choices, role)  # Display the menu grid

            choice = self.ui.prompt_choice("[bold cyan]Votre choix[/bold cyan]", choices, default="1")
            if choice == "3":
                # Ex. name_q = Question("input", "class_name", "[cyan]Nom de la classe[/cyan]")
                # answer = self.ui.ask_question(name_q)
                # success, event = self.wm.add_class(answer.value, parent)
                # self.ui.handle_event(event)
                pass  # Placeholder pour éviter l'erreur d'indentation (remplace par le code réel plus tard)
            # Migre tous elif: Replace console/Prompt by questions/answers/events
            elif choice == "0":
                break