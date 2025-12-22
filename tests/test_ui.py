# tests/test_ui.py - Unit tests for ConsoleUI using unittest (standard lib, no pytest needed)

import unittest
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

from ui.console_ui import ConsoleUI
from core.models.event import Event, Severity
from core.models.question import Question
from core.models.answer import Answer

class TestConsoleUI(unittest.TestCase):
    def setUp(self):
        self.ui = ConsoleUI()

    def test_handle_event(self):
        event = Event("test_event", "test_source", payload="test_payload", severity=Severity.INFO)
        with redirect_stdout(StringIO()) as output:
            self.ui.handle_event(event)
        self.assertIn("test_event: test_payload", output.getvalue())  # Basic check for output

    def test_ask_question_string(self):
        question = Question("input", "test_target", "Test prompt", expected_type="string", default="default")
        with patch('rich.prompt.Prompt.ask', return_value="user_input"):
            answer = self.ui.ask_question(question)
        self.assertEqual(answer.value, "user_input")
        self.assertEqual(answer.value_type, "string")

    def test_ask_question_bool(self):
        question = Question("input", "test_target", "Test prompt", expected_type="bool")
        with patch('rich.prompt.Prompt.ask', return_value="oui"):
            answer = self.ui.ask_question(question)
        self.assertTrue(answer.value)

        with patch('rich.prompt.Prompt.ask', return_value="non"):
            answer = self.ui.ask_question(question)
        self.assertFalse(answer.value)

    def test_show_panel(self):
        with redirect_stdout(StringIO()) as output:
            self.ui.show_panel("Test text", style="red")
        self.assertIn("Test text", output.getvalue())

    def test_show_table(self):
        with redirect_stdout(StringIO()) as output:
            self.ui.show_table("Test Title", ["Col1", "Col2"], [["row1col1", "row1col2"]])
        self.assertIn("Test Title", output.getvalue())
        self.assertIn("row1col1", output.getvalue())

    def test_select_list(self):
        items = ["Item1", "Item2"]
        with patch('rich.prompt.Prompt.ask', return_value="1"):
            selected = self.ui.select_list(items, "Test Title")
        self.assertEqual(selected, "Item1")

        with patch('rich.prompt.Prompt.ask', return_value="0"):
            selected = self.ui.select_list(items, "Test Title")
        self.assertIsNone(selected)

    def test_show_tree(self):
        class MockKB:
            def get_hierarchy(self):
                return [(1, "Class1", None, 0)]  # Simple mock data
            def get_all_props_for_class(self, name):
                return []
            def get_all_instances(self, name):
                return []

        with redirect_stdout(StringIO()) as output:
            self.ui.show_tree(MockKB())
        self.assertIn("Class1", output.getvalue())

    def test_prompt_choice(self):
        with patch('rich.prompt.Prompt.ask', return_value="2"):
            choice = self.ui.prompt_choice("Test prompt", ["1", "2"], default="1")
        self.assertEqual(choice, "2")

    def test_confirm(self):
        with patch('rich.prompt.Confirm.ask', return_value=True):
            confirmed = self.ui.confirm("Test confirm")
        self.assertTrue(confirmed)

    def test_show_menu(self):
        choices = ["0", "1", "2"]
        with redirect_stdout(StringIO()) as output:
            self.ui.show_menu(choices, "user")
        self.assertIn("MENU PRINCIPAL", output.getvalue())

if __name__ == '__main__':
    unittest.main()