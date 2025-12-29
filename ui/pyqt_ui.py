# ui/pyqt_ui.py (version fonctionnelle : fenêtre principale active, menu cliquable, questions non-bloquantes)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QInputDialog, QTreeWidget, QTableWidget, QMenuBar, QWidget, QVBoxLayout, QLabel, QTabWidget, QStatusBar , QDialog, QFormLayout, QLineEdit, QPushButton,QComboBox,QTableWidgetItem, QTreeWidgetItem)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from .base_ui import BaseUI
from core.models.event import Event, Severity
from core.models.question import Question
from core.models.answer import Answer

DEBUG = True  # Ou False pour désactiver

class LoginDialog(QDialog):
    def __init__(self, kb, parent=None):
        super().__init__(parent)
        self.kb = kb
        self.setWindowTitle("Connexion - XXpert System")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Entrez votre nom d'utilisateur")
        layout.addRow("Username:", self.username_edit)
        
        btn_layout = QVBoxLayout()
        self.login_btn = QPushButton("Se connecter")
        self.login_btn.clicked.connect(self.attempt_login)
        btn_layout.addWidget(self.login_btn)
        
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        layout.addRow(self.message_label)
        
        layout.addRow(btn_layout)
        
        self.resize(300, 150)

    def attempt_login(self):
        username = self.username_edit.text().strip().lower()
        if not username:
            self.message_label.setText("<font color='red'>Username requis</font>")
            return
        
        role = self.kb.get_user_role(username)
        if role:
            self.username = username.capitalize()
            self.role = role
            self.user_id = self.kb.get_user_id(username)
            self.accept()  # Success → close dialog with Accepted
            return
        
        # User unknown → ask to create
        reply = QMessageBox.question(
            self, "Utilisateur inconnu",
            f"L'utilisateur '{username}' n'existe pas.\nVoulez-vous le créer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.kb.create_user(username, 'user')
            self.username = username.capitalize()
            self.role = 'user'
            self.user_id = self.kb.get_user_id(username)
            self.accept()
        else:
            self.message_label.setText("<font color='orange'>Connexion annulée</font>")
            self.username_edit.clear()

class PyQtUI(BaseUI):
    def __init__(self):
        self.app = QApplication([])
        #self._apply_styles()   # ← ICI, point d’entrée unique du style
        with open("ui/styles.qss", "r") as f:
            self.app.setStyleSheet(f.read())
        self.window = QMainWindow()
        self.window.setWindowTitle("XXpert System V0.9 - Dashboard")
        self.window.resize(1400, 900)
        self.controller = None

        # Modal login before show
#        login_dialog = LoginDialog(self.window, self)
#        if login_dialog.exec() == QDialog.DialogCode.Rejected:
#            QApplication.quit()  # Exit if login cancel
#            return  # Stop init

        # Proceed after login success
        self.status_bar = QStatusBar()
        self.window.setStatusBar(self.status_bar)

        self.dashboard = QTabWidget()
        self.window.setCentralWidget(self.dashboard)

        # Tabs
        self.home_tab = QWidget()
        home_layout = QVBoxLayout(self.home_tab)
        home_label = QLabel("Bienvenue dans XXpert System\nUtilisez le menu principal pour naviguer")
        home_label.setProperty("role", "title") # voir ui/styles.qss

        home_layout.addWidget(home_label)
        self.dashboard.addTab(self.home_tab, "Accueil")

        self.tree_tab = QTreeWidget()
        self.tree_tab.itemClicked.connect(self.handle_tree_click)  # Ajout pour gérer les clics
        # controller
        self.dashboard.addTab(self.tree_tab, "Arbre Classes")


        #self.table_tab = QTableWidget()
        self.table_tab = QWidget()  # Change de QTableWidget à QWidget pour layout
        table_layout = QVBoxLayout(self.table_tab)
        self.table_combo = QComboBox()
        self.table_combo.addItems(["Classes", "Instances", "Props", "Events"])
        self.table_combo.currentTextChanged.connect(self.load_table)
        table_layout.addWidget(self.table_combo)
        self.table_widget = QTableWidget()
        table_layout.addWidget(self.table_widget)
        self.dashboard.addTab(self.table_tab, "Tables")
        #if self.table_combo.count() > 0:
        #    self.load_table(self.table_combo.currentText())



        
        self.log_tab = QLabel("Log events :\n")
        log_scroll = QWidget()
        log_layout = QVBoxLayout(log_scroll)
        log_layout.addWidget(self.log_tab)
        self.dashboard.addTab(log_scroll, "Log Events")

    def handle_event(self, event: Event):
        if event.event_type == "menu_requested":
            self.show_menu(event.payload.get("choices", []), event.payload.get("role", "user"))

        elif event.event_type == "table_requested":
            table_name = event.payload.get("table_name")
            filter_data = event.payload.get("filter", {})
            if table_name:
                self.table_combo.setCurrentText(table_name.capitalize())
                self.load_table(table_name.capitalize(), filter_data)  # Ajouter param filter
                self.dashboard.setCurrentWidget(self.table_tab)
  
        else:
            self.status_bar.showMessage(f"{event.event_type}: {event.payload}", 5000)
            current_log = self.log_tab.text()
            self.log_tab.setText(current_log + f"\n{event.timestamp} - {event.event_type}: {event.payload}")

        if event.severity == Severity.ERROR:
            QMessageBox.critical(self.window, "Erreur", str(event.payload))
    
    def handle_tree_click(self, item, column):
        # Extrait le nom de la classe du label (avant " — ")
        class_name = item.text(column).split(" —")[0]
        # Affiche dans la status bar
        self.status_bar.showMessage(f"Classe sélectionnée : {class_name}", 5000)
        # Optionnel : déclenche un événement pour le controller
        event = Event("class_selected", "ui", payload={"class_name": class_name})
        self.controller.ui.handle_event(event)  # Ou directement self.handle_event si local

    def ask_question(self, question: Question) -> Answer:
        # Questions en dialogs (modaux OK ici, car courts)
        if question.expected_type == "bool":
            reply = QMessageBox.question(self.window, "Question", question.prompt, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            val = reply == QMessageBox.StandardButton.Yes
        elif question.expected_type == "int":
            val, ok = QInputDialog.getInt(self.window, "Question", question.prompt)
            val = val if ok else None
        elif question.expected_type == "float":
            val, ok = QInputDialog.getDouble(self.window, "Question", question.prompt)
            val = val if ok else None
        else:
            if question.choices:
                val, ok = QInputDialog.getItem(self.window, "Question", question.prompt, question.choices, 0, False)
            else:
                val, ok = QInputDialog.getText(self.window, "Question", question.prompt)
            val = val if ok else None
        return Answer(question.question_id, val, question.expected_type)

    def show_menu(self, choices, role):
        menu_bar = self.window.menuBar()
        menu_bar.clear()  # Refresh
        main_menu = menu_bar.addMenu("Menu Principal")
        for choice in choices:
            action = QAction(choice, self.window)
            action.triggered.connect(lambda checked, c=choice: self.controller.handle_choice(c))
            main_menu.addAction(action)

    # show_panel : Status bar or log
    def show_panel(self, text, style="blue"):
        self.status_bar.showMessage(text, 10000)

    # select_list : QInputDialog list
    def select_list(self, items, title, wm=None, temp_items=None, official_color="green", temp_color="yellow"):
        if not items:
            self.show_panel("Liste vide")
            return None
        display_items = [f"[temp] {i}" if wm and i in wm.changes else i for i in items]
        val, ok = QInputDialog.getItem(self.window, title, title, display_items, 0, False)
        return val.replace("[temp] ", "") if ok else None
    
    # DEV

    def load_table(self, table_name, filter_data=None):
        if filter_data is None:
            filter_data = {}

        if DEBUG:
            print(f"load_table called with {table_name}, filter: {filter_data}")

        if not self.controller or not self.controller.kb:
            if DEBUG:
                print("load_table: Controller or KB None, returning early")
            return

        kb = self.controller.kb
        columns = []
        rows = []

        if table_name == "Classes":
            columns = ["ID", "Name", "Parent Name"]
            rows = kb.get_all_classes()

        elif table_name == "Instances":
            columns = ["ID", "Name", "Class Name"]
            rows = kb.get_all_instances_global()

        elif table_name == "Props":
            # Cas filtré : on veut les propriétés d'une classe spécifique
            class_filter = filter_data.get("class_name")
            if class_filter:
                columns = ["Name", "Type"]  # Plus léger, pas besoin d'ID ici
                prop_names = kb.get_all_props_for_class(class_filter)
                rows = []
                for name in prop_names:
                    ptype = kb.get_property_type(name) or "string"
                    rows.append((name, ptype))
                title = f"Propriétés de {class_filter}"
            else:
                # Cas global : toutes les propriétés
                columns = ["ID", "Name", "Type"]
                rows = kb.get_all_properties()
                title = "Table: Props"

        elif table_name == "Events":
            columns = ["ID", "Type", "Source", "Entity", "Payload", "Severity", "Timestamp"]
            rows = kb.get_all_events(limit=100)
            title = "Table: Events"

        else:
            return  # Table inconnue

        self.show_table(title if 'title' in locals() else f"Table: {table_name}", columns, rows)

    def load_tableOLD(self, table_name):
        if DEBUG:
           print(f"load_table called with {table_name}")
           print(f"Controller: {self.controller}, KB: {self.controller.kb if self.controller else None}")        
  
        if not self.controller or not self.controller.kb:
            if DEBUG:
                print("load_table: Controller or KB None, returning early")            
            return
        kb = self.controller.kb
        columns = []
        rows = []
        
        if table_name == "Classes":
            columns = ["ID", "Name", "Parent Name"]
            if DEBUG:
                print("Fetching classes...")            
            rows = kb.get_all_classes()  
        
        elif table_name == "Instances":
            columns = ["ID", "Name", "Class Name"]
            rows = kb.get_all_instances_global()  

        elif table_name == "Props":  # Ou "Properties"
            if filter_data.get("class_name"):
                columns = ["Name", "Type"]
                rows = [(name, self.controller.kb.get_property_type(name)) for name in self.controller.kb.get_all_props_for_class(filter_data["class_name"])]            
            else:
                columns = ["ID", "Name", "Type"]
                rows = kb.get_all_properties()  
        
        elif table_name == "Events":
            columns = ["ID", "Type", "Source", "Entity", "Payload", "Severity", "Timestamp"]
            rows = kb.get_all_events(limit=100)  
        self.show_table(f"Table: {table_name}", columns, rows)
        if DEBUG:
            print(f"show_table called with {len(rows)} rows")    

    # show_table / show_tree : Update tabs
    def show_table(self, title, columns, rows):
        if DEBUG:
            print(f"Entering show_table with title '{title}', {len(columns)} columns, {len(rows)} rows")        
        self.table_widget.setRowCount(len(rows))
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels(columns)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table_widget.setItem(i, j, QTableWidgetItem(str(val)))
        self.dashboard.setCurrentWidget(self.table_tab)
        self.dashboard.setTabText(self.dashboard.indexOf(self.table_tab), title)

    def show_tree(self, kb):
        self.tree_tab.clear()
        self.tree_tab.setHeaderLabel("Classes")
        data = kb.get_hierarchy()
        root = self.tree_tab.invisibleRootItem()
        nodes = {}
        for cid, name, pid, level in data:
            label = f"{name} — props: {len(kb.get_all_props_for_class(name))} — inst: {len(kb.get_all_instances(name))}"
            item = QTreeWidgetItem([label])
            if pid is None:
                root.addChild(item)
            else:
                parent = nodes[pid]
                parent.addChild(item)
            nodes[cid] = item
        self.dashboard.setCurrentWidget(self.tree_tab)


    def confirm(self, prompt, default=True):
        reply = QMessageBox.question(self.window, "Confirmation", prompt, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def prompt_choice(self, prompt, choices, default=None):
        current = choices.index(default) if default in choices else 0
        val, ok = QInputDialog.getItem(self.window, prompt, prompt, choices, current, False)
        return val if ok else None


    def run(self):
        #self.window.show()
        self.app.exec()  # ← Comment or remove (now shown in main())
        # Boucle principale PyQt