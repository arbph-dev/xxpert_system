# core/auth/user.py (decoupled without major changes: inject ui only for login, keep structure)
from core.models.question import Question
from core.models.event import Event, Severity
from ui.pyqt_ui import LoginDialog  # Direct import since it's PyQt-specific now
from PyQt6.QtWidgets import QDialog


class UserManager:
    def __init__(self, kb):
        self.kb = kb

    def login(self, ui):
        """
        Shows a dedicated LoginDialog.
        Returns (user_id, username, role) on success.
        Blocks until login or cancel.
        """
        dialog = LoginDialog(self.kb, ui.window)  # Pass main window as parent
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Success: user either existed or was created
            ui.handle_event(Event("login_success", "user_manager", payload=f"Bienvenue, {dialog.username} ({dialog.role})"))
            return dialog.user_id, dialog.username, dialog.role
        else:
            # User cancelled → quit app gracefully
            ui.handle_event(Event("login_cancelled", "user_manager", payload="Connexion annulée par l'utilisateur"))
            #ui.handle_event(Event("error", "login", payload="[red]Username requis[/red]", severity=Severity.ERROR))
            QApplication.quit()
            return None, None, None  # Will not be reached due to quit