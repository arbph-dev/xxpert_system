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

    # Add show_tree, etc.