# /main.py

from core.database import KnowledgeBase


# from ui.console_ui import ConsoleUI
## DEV 2025-12-25
from ui.pyqt_ui import PyQtUI

from controller.app_controller import AppController

def main():
    kb = KnowledgeBase()
    ui = PyQtUI()
    controller = AppController(kb, ui)
    ui.controller = controller
    ui.run()  # Lance la fenêtre et la boucle


if __name__ == "__main__":
    main()