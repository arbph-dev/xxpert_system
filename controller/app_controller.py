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
        self.ui.handle_event(Event("app_start", "controller"))

        while True:
            # Menu: ui.show_menu(choices)
            choice = self.ui.prompt_choice(...)  # Add method to BaseUI
            if choice == "3":
                # Ex. name_q = Question("input", "class_name", "[cyan]Nom de la classe[/cyan]")
                # answer = self.ui.ask_question(name_q)
                # success, event = self.wm.add_class(answer.value, parent)
                # self.ui.handle_event(event)
            # Migre tous elif: Replace console/Prompt by questions/answers/events
            elif choice == "0":
                break