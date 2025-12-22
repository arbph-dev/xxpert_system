from rich.console import Console
from rich.prompt import Prompt, Confirm  # Confirm ajouté

console = Console()

class UserManager:
    def __init__(self, kb):
        self.kb = kb

    def login(self):
        while True:
            username = Prompt.ask("[bold cyan]Username[/bold cyan]").strip().lower()
            if not username:
                console.print("[red]Username requis[/red]")
                continue

            role = self.kb.get_user_role(username)
            #console.print(f"[green]lecture, {username.capitalize()} ({role})[/]")

            if role:
                console.print(f"[green]Bienvenue, {username.capitalize()} ({role})[/]")
                user_id = self.kb.get_user_id(username)
                return user_id, username.capitalize(), role

            if Confirm.ask(f"[yellow]Utilisateur '{username}' inconnu. Créer ?[/yellow]"):
                self.kb.create_user(username, 'user')
                console.print(f"[green]Utilisateur '{username.capitalize()}' créé (rôle user)[/]")
                user_id = kb.get_user_id(username)
                return user_id, username.capitalize(), 'user'
