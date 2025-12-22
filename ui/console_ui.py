# /ui/console_ui.py

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.tree import Tree

from .base_ui import BaseUI
from core.models.event import Event, Severity
from core.models.question import Question
from core.models.answer import Answer

class ConsoleUI(BaseUI):
    def __init__(self):
        self.console = Console()

    def handle_event(self, event: Event):
        style = "green" if event.severity == Severity.INFO else "yellow" if event.severity == Severity.WARNING else "red"
        self.console.print(Panel(f"{event.event_type}: {event.payload or event.entity}", style=style))

    def ask_question(self, question: Question) -> Answer:
        val_str = Prompt.ask(question.prompt, default=question.default or "", choices=question.choices)
        # Parse based on expected_type (ex. bool/int)
        if question.expected_type == "bool":
            val = val_str.lower() in ("oui", "o", "true")
        else:
            val = val_str
        return Answer(question.question_id, val, question.expected_type)

    def show_panel(self, text, style="blue"):
        self.console.print(Panel(text, style=style))

    # Migre show_table, select_list, show_tree from console.py
    def show_table(self, title, columns, rows):
        table = Table(title=title)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*row)
        self.console.print(table)

    # ... (select_list with jaune for temp WM)