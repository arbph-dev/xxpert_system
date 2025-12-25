# core/auth/user.py (decoupled without major changes: inject ui only for login, keep structure)
from core.models.question import Question
from core.models.event import Event, Severity

class UserManager:
    def __init__(self, kb):
        self.kb = kb

    def login(self, ui):
        while True:
            username_q = Question("input", "username", "[bold cyan]Username[/bold cyan]")
            answer = ui.ask_question(username_q)
            username = answer.value.strip().lower()
            if not username:
                ui.handle_event(Event("error", "login", payload="[red]Username requis[/red]", severity=Severity.ERROR))
                continue

            role = self.kb.get_user_role(username)
            if role:
                ui.handle_event(Event("login_success", "user_manager", payload=f"[green]Bienvenue, {username.capitalize()} ({role})[/]"))
                user_id = self.kb.get_user_id(username)
                return user_id, username.capitalize(), role

            create_q = Question("confirmation", "create_user", f"[yellow]Utilisateur '{username}' inconnu. Créer ?[/yellow]", expected_type="bool", default=True)
            create_answer = ui.ask_question(create_q)
            if create_answer.value:
                self.kb.create_user(username, 'user')  # Direct for simplicity; WM if staging needed
                ui.handle_event(Event("user_created", "user_manager", payload=f"[green]Utilisateur '{username.capitalize()}' créé (rôle user)[/]"))
                user_id = self.kb.get_user_id(username)
                return user_id, username.capitalize(), 'user'