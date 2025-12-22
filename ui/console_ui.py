# ui/console_ui.py
#  updated with select_list and other missing methods
# ui/console_ui.py (implement show_menu with Rich grid/table as in original main.py)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.layout import Layout  # For grid if needed

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

    def show_table(self, title, columns, rows):
        table = Table(title=title)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*row)
        self.console.print(table)

    def select_list(self, items, title, wm=None, temp_items=None, official_color="green", temp_color="yellow"):
        if wm:
            items = wm.get_temp_classes() if temp_items is None else temp_items

        if not items:
            self.console.print(Panel("Liste vide", style="yellow"))
            return None

        table = Table(title=title)
        table.add_column("N°", style="cyan")
        table.add_column("Item", style="green")

        for i, item in enumerate(items, 1):
            # Différencier couleur si temp
            color = temp_color if wm and item in wm.changes else official_color
            table.add_row(str(i), f"[{color}]{item}[/]")

        self.console.print(table)
        while True:
            ch = Prompt.ask("Numéro (0 annuler)", default="0")
            if ch == "0":
                return None
            if ch.isdigit() and 1 <= int(ch) <= len(items):
                return items[int(ch)-1]
            self.console.print("[red]Invalide[/]")

    def show_tree(self, kb):
        data = kb.get_hierarchy()
        if not data:
            self.console.print(Panel("Aucune classe", style="yellow"))
            return
        tree = Tree("[bold blue]=== CLASSES ===[/]")
        nodes = {}
        for cid, name, pid, level in data:
            props = len(kb.get_all_props_for_class(name))
            insts = len(kb.get_all_instances(name))
            label = f"[green]{name}[/] — {props} props — {insts} inst."
            if pid is None:
                node = tree.add(label)
            else:
                parent_node = nodes[pid]
                node = parent_node.add(label)
            nodes[cid] = node
        self.console.print(tree)

    def prompt_choice(self, prompt, choices, default=None):
        return Prompt.ask(prompt, choices=choices, default=default)

    def confirm(self, prompt, default=True):
        return Confirm.ask(prompt, default=default)

    def show_menu(self, choices, role):
        # Replicate original menu grid from main.py
        menu_grid = Table.grid(padding=(0, 2), expand=True)
        menu_grid.add_column(justify="right", style="cyan", width=4)
        menu_grid.add_column(style="green")

        # Colonne 1
        col1 = Table.grid(padding=0)
        col1.add_column()
        col1.add_row("1. Jouer au jeu Akinator")
        col1.add_row("2. Lister les classes (arbre)")
        col1.add_row("3. Ajouter une classe")
        col1.add_row("4. Ajouter une propriété")
        col1.add_row("5. Ajouter une instance (+ props)")
        col1.add_row("6. Lister toutes les propriétés")
        col1.add_row("7. Lister instances + propriétés")            
        # Colonne 2
        col2 = Table.grid(padding=0)
        col2.add_column()
        col2.add_row("8. Propriétés héritées d'une classe")
        col2.add_row("9. Lier propriété à classe")
        col2.add_row("10. Modifier valeur propriété")
        col2.add_row("11. Voir seuils LL/L/M/H/HH")
        col2.add_row("12. Définir seuils manuels")
        col2.add_row("13. Inférence Forward")
        col2.add_row("14. Inférence Backward")
        
        col2.add_row("")
        col2.add_row("15. Soumettre changements")            
        col2.add_row("0. Quitter")
        col2.add_row("")
        if role == 'admin':
            col2.add_row("20. Lister soumissions pending")
            col2.add_row("21. Valider/rejeter soumission")

        menu_grid.add_row(col1, col2)
        self.console.print(Panel(menu_grid, title="[bold magenta]MENU PRINCIPAL[/bold magenta]", border_style="bright_blue"))