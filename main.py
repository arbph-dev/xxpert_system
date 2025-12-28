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
    
    ui.window.show()

    controller.init_logic()  # Appel manquant ? Ajoute si login/menu doit s'init
    
    ui.load_table(ui.table_combo.currentText())  # Chargement initial après controller set    
    
    ui.show_tree(controller.kb)  # Chargement initial treeview après login
    
    # ui.run()  # Lance la fenêtre et la boucle
    ui.app.exec()  # Start event loop (replaces ui.run())

if __name__ == "__main__":
    main()