class FactService:
    def __init__(self, fact_store, repository):
        self.fact_store = fact_store
        self.repo = repository

    def infer_forward(self, instance, class_name):
        pass
        # ... (logique d'inférence)

    def apply_selection_policy(self, facts, policy="priority"):
        pass
        # ... (sélection selon politique)