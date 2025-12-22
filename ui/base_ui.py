# /ui/base_ui.py

from abc import ABC, abstractmethod
from core.models.event import Event
from core.models.question import Question
from core.models.answer import Answer

class BaseUI(ABC):
    @abstractmethod
    def handle_event(self, event: Event):
        pass

    @abstractmethod
    def ask_question(self, question: Question) -> Answer:
        pass

    @abstractmethod
    def show_panel(self, text, style="blue"):
        pass

    @abstractmethod
    def show_table(self, title, columns, rows):
        pass

    @abstractmethod
    def select_list(self, items, title):
        pass

    @abstractmethod
    def show_menu(self, choices, role):
        """Display the main menu grid based on choices and role."""
        pass

    @abstractmethod
    def prompt_choice(self, prompt, choices, default=None):
        pass

    @abstractmethod
    def confirm(self, prompt, default=True):
        pass

    # Add show_tree if not already
    @abstractmethod
    def show_tree(self, kb):
        pass