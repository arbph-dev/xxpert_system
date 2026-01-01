# core/workflow/working_memory.py (pure buffer, no UI/print/store; return Events via service)
class WorkingMemory:
    def __init__(self, repo):
        self.repo = repo
        self.changes = []

    def add_change(self, action, data):
        self.changes.append({"action": action, "data": data})

    def add_class(self, name, parent=None):
        if self.repo.get_class_id(name):  # Rule: if exists, no add
            return False
        self.add_change('add_class', {'name': name, 'parent': parent})
        return True

    def add_property(self, name, ptype):
        if self.kb.get_property_id(name):
            return False
        # Stage the add in self.changes (e.g., self.changes['properties'].append((name, ptype)))
        return True

    def attach_property_to_class(self, class_name, prop_name):
        # Stage the attachment in changes
        return True

    def add_instance(self, name, class_name):
        if self.kb.instance_exists(name, class_name):
            return False
        # Stage in changes
        return True

    def submit(self, user_id, description):
        changes_json = json.dumps(self.changes)
        self.repo.cursor.execute("INSERT INTO se_submissions (user_id, description, changes_json) VALUES (?, ?, ?)", (user_id, description, changes_json))
        self.repo.commit()
        self.changes = []
        return True