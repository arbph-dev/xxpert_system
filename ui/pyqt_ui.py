# ui/pyqt_ui.py (version fonctionnelle : fenêtre principale active, menu cliquable, questions non-bloquantes)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QInputDialog, QTreeWidget, QTableWidget, QMenuBar, QWidget, QVBoxLayout, QLabel, QTabWidget, QStatusBar , QDialog, QFormLayout, QLineEdit, QPushButton)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from .base_ui import BaseUI
from core.models.event import Event, Severity
from core.models.question import Question
from core.models.answer import Answer



class LoginDialog(QDialog):
    def __init__(self, parent=None, ui=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.ui = ui
        layout = QFormLayout(self)
        self.username_edit = QLineEdit()
        layout.addRow("Username:", self.username_edit)
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)

    def login(self):
        username = self.username_edit.text().strip().lower()
        if not username:
            QMessageBox.warning(self, "Error", "Username requis")
            return
        # Call controller.um.login but since no controller yet, stub or pass to ui
        # For now, accept and close (real logic in controller)
        self.accept()  # Close modal on success


class PyQtUI(BaseUI):
    def __init__(self):
        self.app = QApplication([])
        self.window = QMainWindow()
        self.window.setWindowTitle("XXpert System V0.9 - Dashboard")
        self.window.resize(800, 600)
        self.controller = None

        # Modal login before show
        login_dialog = LoginDialog(self.window, self)
        if login_dialog.exec() == QDialog.DialogCode.Rejected:
            QApplication.quit()  # Exit if login cancel
            return  # Stop init

        # Proceed after login success
        self.status_bar = QStatusBar()
        self.window.setStatusBar(self.status_bar)

        self.dashboard = QTabWidget()
        self.window.setCentralWidget(self.dashboard)

        # Tabs
        self.home_tab = QWidget()
        home_layout = QVBoxLayout(self.home_tab)
        home_label = QLabel("Bienvenue dans XXpert System\nUtilisez le menu principal pour naviguer")
        home_layout.addWidget(home_label)
        self.dashboard.addTab(self.home_tab, "Accueil")

        self.tree_tab = QTreeWidget()
        self.dashboard.addTab(self.tree_tab, "Arbre Classes")

        self.table_tab = QTableWidget()
        self.dashboard.addTab(self.table_tab, "Tables")

        self.log_tab = QLabel("Log events :\n")
        log_scroll = QWidget()
        log_layout = QVBoxLayout(log_scroll)
        log_layout.addWidget(self.log_tab)
        self.dashboard.addTab(log_scroll, "Log Events")

    def handle_event(self, event: Event):
        if event.event_type == "menu_requested":
            self.show_menu(event.payload.get("choices", []), event.payload.get("role", "user"))
        else:
            self.status_bar.showMessage(f"{event.event_type}: {event.payload}", 5000)
            current_log = self.log_tab.text()
            self.log_tab.setText(current_log + f"\n{event.timestamp} - {event.event_type}: {event.payload}")

        if event.severity == Severity.ERROR:
            QMessageBox.critical(self.window, "Erreur", str(event.payload))
    
    
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

    # show_table / show_tree : Update tabs
    def show_table(self, title, columns, rows):
        self.table_tab.setRowCount(len(rows))
        self.table_tab.setColumnCount(len(columns))
        self.table_tab.setHorizontalHeaderLabels(columns)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table_tab.setItem(i, j, QTableWidgetItem(str(val)))
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
        self.window.show()
        self.app.exec()  # Boucle principale PyQt