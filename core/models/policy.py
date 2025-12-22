#core/models/policy.py

class Policy:
    STRICT = "strict"  # Ex. expert first

class FactPolicy:
    def select_active_fact(self, facts, policy=Policy.STRICT):
        # MVP: Return highest confidence
        if not facts:
            return None
        return max(facts, key=lambda f: f.confidence)