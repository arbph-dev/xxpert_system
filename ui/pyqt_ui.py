# ui/pyqt_ui.py
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QInputDialog, QTreeWidget, QTableWidget, QMenuBar
from PyQt6.QtGui import QAction  # Moved here in PyQt6
from PyQt6.QtCore import Qt
from .base_ui import BaseUI
from core.models.event import Event, Severity
from core.models.question import Question
from core.models.answer import Answer

class PyQtUI(BaseUI):
    def __init__(self):
        self.app = QApplication([])
        self.window = QMainWindow()
        self.window.setWindowTitle("XXpert System V0.9")
        self.controller = None  # Set from main.py for bidirectional callbacks

    def handle_event(self, event: Event):
        icon = QMessageBox.Icon.Information if event.severity == Severity.INFO else QMessageBox.Icon.Warning if event.severity == Severity.WARNING else QMessageBox.Icon.Critical
        QMessageBox(icon, event.event_type, str(event.payload or event.entity), parent=self.window).exec()

    def ask_question(self, question: Question) -> Answer:
        if question.expected_type == "bool":
            reply = QMessageBox.question(self.window, "Confirmation", question.prompt, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            val = reply == QMessageBox.StandardButton.Yes
        elif question.expected_type == "int":
            val, ok = QInputDialog.getInt(self.window, question.prompt, question.prompt, value=0)
            if not ok: val = None
        elif question.expected_type == "float":
            val, ok = QInputDialog.getDouble(self.window, question.prompt, question.prompt, value=0.0)
            if not ok: val = None
        else:  # string/choice
            if question.choices:
                val, ok = QInputDialog.getItem(self.window, question.prompt, question.prompt, question.choices)
            else:
                val, ok = QInputDialog.getText(self.window, question.prompt, question.prompt)
            if not ok: val = None
        return Answer(question.question_id, val, question.expected_type)

    def show_menu(self, choices, role):
        menu_bar = self.window.menuBar()
        main_menu = menu_bar.addMenu("Menu Principal")
        for choice in choices:
            action = QAction(choice, self.window)
            action.triggered.connect(lambda checked, c=choice: self.controller.handle_choice(c) if self.controller else None)
            main_menu.addAction(action)




    def show_panel(self, text, style="blue"):
        # Simple text display (ex. QLabel or QMessageBox for panel-like)
        QMessageBox.information(self.window, "Panel", text)

    def select_list(self, items, title, wm=None, temp_items=None, official_color="green", temp_color="yellow"):
        # Use QInputDialog.getItem for choice
        if wm:
            items = wm.get_temp_classes() if temp_items is None else temp_items
        if not items:
            self.show_panel("Liste vide", style="yellow")
            return None

        # Diff colors not easy in QDialog ; stub as list str (add [temp] prefix)
        display_items = []
        for item in items:
            prefix = "[temp] " if wm and item in wm.changes else ""
            display_items.append(prefix + item)

        val, ok = QInputDialog.getItem(self.window, title, title, display_items, 0, False)
        if ok:
            return val.replace("[temp] ", "")  # Clean
        return None

    # If other abstracts missing (ex. show_table, show_tree), impl similarly
    def show_table(self, title, columns, rows):
        table = QTableWidget(len(rows), len(columns), self.window)
        table.setWindowTitle(title)
        table.setHorizontalHeaderLabels(columns)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val)))
        table.show()  # Separate window or set central
        # self.window.setCentralWidget(table)

    def show_tree(self, kb):
        tree = QTreeWidget(self.window)
        tree.setHeaderLabel("Classes")
        data = kb.get_hierarchy()
        if not data:
            self.show_panel("Aucune classe", style="yellow")
            return
        root = tree.invisibleRootItem()
        nodes = {}
        for cid, name, pid, level in data:
            props = len(kb.get_all_props_for_class(name))
            insts = len(kb.get_all_instances(name))
            label = f"{name} — {props} props — {insts} inst."
            item = QTreeWidgetItem([label])
            if pid is None:
                root.addChild(item)
            else:
                parent = nodes[pid]
                parent.addChild(item)
            nodes[cid] = item
        tree.show()  # Separate or central
        # self.window.setCentralWidget(tree)

    def show_treeOLD(self, kb):
        tree = QTreeWidget(self.window)
        tree.setHeaderLabel("Classes")
        # Build tree from kb.get_hierarchy() data
        root = tree.invisibleRootItem()
        nodes = {}
        data = kb.get_hierarchy()
        for cid, name, pid, level in data:
            label = f"{name} — props: {len(kb.get_all_props_for_class(name))} — inst: {len(kb.get_all_instances(name))}"
            item = QTreeWidgetItem([label])
            if pid is None:
                root.addChild(item)
            else:
                parent = nodes[pid]
                parent.addChild(item)
            nodes[cid] = item
        self.window.setCentralWidget(tree)

    def prompt_choice(self, prompt, choices, default=None):
        val, ok = QInputDialog.getItem(self.window, prompt, prompt, choices, 0, False)
        return val if ok else None

    def confirm(self, prompt, default=True):
        reply = QMessageBox.question(self.window, "Confirmation", prompt, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def run(self):
        self.window.show()
        self.app.exec()