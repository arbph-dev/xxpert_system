# For facts/rules/inference (ex. gros chat)
# core/rules/engine.py (new stub)
class RuleEngine:
    def __init__(self, repo):
        self.repo = repo
        self.rules = []  # Add rule(is_gros_chat, deduce_gros)

    def apply(self, fact):
        for condition, action in self.rules:
            if condition(fact):
                action(fact, self.repo)
# Ex. add rule for masse >15kg → gros=True → job mail/excel/print (stub: event "send_mail")

# In set_instance_value: Create Fact → rule_engine.apply(fact)
# Formulas: Use sympy for U*I - P = 0 (add dep pip install sympy; solve eq in inference)
from sympy import symbols, Eq, solve
U, I, P = symbols('U I P')
eq = Eq(U * I - P, 0)
# Solve for missing var in backward