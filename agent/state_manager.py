class StateManager:
    """Enkel arbeids- og kontekstminne for agenten."""

    def __init__(self):
        self.memory = {}

    def set(self, key, value):
        self.memory[key] = value

    def get(self, key, default=None):
        return self.memory.get(key, default)