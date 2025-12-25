# /main.py

from core.database import KnowledgeBase


# from ui.console_ui import ConsoleUI
## DEV 2025-12-25
from ui.pyqt_ui import PyQtUI

from controller.app_controller import AppController

def main():
    kb = KnowledgeBase()
    # ui = ConsoleUI()
    ui = PyQtUI()
    
    controller = AppController(kb, ui)
    ui.controller = controller  # Bidirectional for menu callbacks
    controller.run()

if __name__ == "__main__":
    main()