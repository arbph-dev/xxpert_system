# core/inference.py
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

class Rule:
    def __init__(self, conditions, conclusion, calculation, unit=None):
        self.conditions = conditions          # liste de propriétés
        self.conclusion = conclusion          # propriété déduite
        self.calculation = calculation        # lambda ou fonction
        self.unit = unit

# core/database.py (corrected execute method in ForwardEngine)

class ForwardEngine:
    def __init__(self, kb):
        self.kb = kb
        self.rules = []

    def add_rule(self, conditions, conclusion, calculation, unit=None):
        self.rules.append(Rule(conditions, conclusion, calculation, unit))

    def execute(self, inst_name, class_name):
        # ... (rest of the method body as before)
        facts = {}
        props = self.kb.get_all_props_for_class(class_name)
        for prop in props:
            val = self.kb.get_instance_value(inst_name, class_name, prop)
            if val is not None:
                facts[prop] = val

        changed = True
        iterations = 0
        while changed and iterations < 20:
            changed = False
            iterations += 1
            for rule in self.rules:
                if all(cond in facts for cond in rule.conditions):
                    if rule.conclusion not in facts or facts[rule.conclusion] is None:
                        try:
                            vals = [facts[c] for c in rule.conditions]
                            new_val = rule.calculation(*vals)
                            if new_val is not None:
                                facts[rule.conclusion] = round(new_val, 6) if isinstance(new_val, float) else new_val
                                self.kb.set_instance_value(inst_name, class_name, rule.conclusion, new_val)
                                # Replace console.print with return Event or handle via service
                                # For now, keep as is or comment
                        except Exception as e:
                            pass  # Handle error

        # Return events instead of print
        return Event("forward_done", "inference", payload={"iterations": iterations})

class BackwardEngine:
    def __init__(self, kb):
        self.kb = kb
        self.rules = []

    def add_rule(self, conclusion, conditions, calculation, unit=None):
        self.rules.append(Rule(conditions, conclusion, calculation, unit))

    def ask_value(self, prop, unit=None):
        val_str = Prompt.ask(f"[cyan]? Valeur de {prop}[/] ({unit or 'unité'}) (X pour inconnu)")
        if val_str.upper() == "X":
            return None
        try:
            return float(val_str)
        except:
            console.print("[red]Valeur numérique requise[/]")
            return self.ask_value(prop, unit)

    def prove(self, objective, inst_name, class_name):
        console.print(f"[magenta]→ Objectif : déduire {objective}[/]")

        val = self.kb.get_instance_value(inst_name, class_name, objective)
        if val is not None:
            console.print(f"[green]✓ Déjà connu : {objective} = {val}[/]")
            return val

        for rule in self.rules:
            if rule.conclusion == objective:
                console.print(f"[yellow]Règle applicable : {rule.conditions} → {objective}[/]")
                vals = []
                for cond in rule.conditions:
                    v = self.prove(cond, inst_name, class_name)
                    if v is None:
                        vals = None
                        break
                    vals.append(v)
                if vals is not None:
                    try:
                        result = rule.calculation(*vals)
                        result = round(result, 6) if isinstance(result, float) else result
                        self.kb.set_instance_value(inst_name, class_name, objective, result)
                        console.print(f"[bold green]✓ Déduit : {objective} = {result} {rule.unit or ''}[/]")
                        return result
                    except Exception as e:
                        console.print(f"[red]Erreur calcul : {e}[/]")

        # Demander à l'utilisateur
        unit = next((r.unit for r in self.rules if r.conclusion == objective), None)
        val = self.ask_value(objective, unit)
        if val is not None:
            self.kb.set_instance_value(inst_name, class_name, objective, val)
        return val
