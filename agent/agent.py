from manifest_loader import ManifestLoader
from dispatcher import Dispatcher
from reasoner import Reasoner
from state_manager import StateManager


class OynaAIAgent:
    """Øyna AI Agent – sentral orkestrator."""

    def __init__(self, manifest_path="../models/v2/ai_master_manifest_v2.json"):
        self.manifest = ManifestLoader(manifest_path).load()
        self.dispatcher = Dispatcher(self.manifest)
        self.reasoner = Reasoner(self.manifest)
        self.state = StateManager()

    def ask(self, query: str):
        plan = self.reasoner.plan(query)
        return self.dispatcher.execute_plan(plan)


if __name__ == "__main__":
    agent = OynaAIAgent()
    print(agent.ask("Hva er dagens forventede vannforbruk?"))