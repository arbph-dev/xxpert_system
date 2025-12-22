class FactStore:
    def __init__(self, repository):
        self.repo = repository

    def get_instances_by_class(self, class_name):
        return self.repo.get_all_instances(class_name)

    def get_fact_value(self, instance, class_name, property_name):
        return self.repo.get_instance_value(instance, class_name, property_name)

    def get_thresholds(self, class_name, property_name):
        return self.repo.get_thresholds(class_name, property_name)