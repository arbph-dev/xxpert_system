# /main.py

from core.database import KnowledgeBase
from ui.console_ui import ConsoleUI
from controller.app_controller import AppController

def main():
    kb = KnowledgeBase()
    ui = ConsoleUI()
    controller = AppController(kb, ui)
    controller.run()

if __name__ == "__main__":
    main()