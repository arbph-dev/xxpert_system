# core/auth/user.py (decoupled from Rich, use Questions/Events)
from core.models.question import Question
from core.models.event import Event

class UserManager:
    def __init__(self, repo, wm):
        self.repo = repo  # KB as repo
        self.wm = wm

    def login(self, ui):
        username_q = Question("input", "username", "Username")
        answer = ui.ask_question(username_q)
        username = answer.value.lower().strip()
        if not username:
            ui.handle_event(Event("error", "login", payload="[red]Username requis[/red]", severity=Severity.ERROR))
            return self.login(ui)  # Retry

        role = self.repo.get_user_role(username)
        if role:
            event = Event("login_success", "user_manager", payload=f"[green]Bienvenue, {username.capitalize()} ({role})[/]")
            ui.handle_event(event)
            user_id = self.repo.get_user_id(username)
            return user_id, username.capitalize(), role

        confirm_q = Question("confirmation", "create_user", f"[yellow]Utilisateur '{username}' inconnu. Créer ?[/yellow]", expected_type="bool", default=True)
        confirm_answer = ui.ask_question(confirm_q)
        if confirm_answer.value:
            self.wm.add_change('create_user', {'username': username, 'role': 'user'})  # Stage in WM
            event = Event("user_created", "user_manager", payload=f"[green]Utilisateur '{username.capitalize()}' créé (rôle user)[/]")
            ui.handle_event(event)
            # Submit WM later for admin validation
            user_id = self.repo.get_user_id(username)  # Temp until validated
            return user_id, username.capitalize(), 'user'
        #return self.login(ui)  # Retry
