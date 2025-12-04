import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ----------------------------
# FILE DEFINITIONS
# ----------------------------

files = {
    "agent/__init__.py": "",
    "agent/agent.py": """from manifest_loader import ManifestLoader
from dispatcher import Dispatcher
from reasoner import Reasoner
from state_manager import StateManager


class OynaAIAgent:
    \"\"\"Øyna AI Agent – sentral orkestrator.\"\"\"

    def __init__(self, manifest_path=\"../models/v2/ai_master_manifest_v2.json\"):
        self.manifest = ManifestLoader(manifest_path).load()
        self.dispatcher = Dispatcher(self.manifest)
        self.reasoner = Reasoner(self.manifest)
        self.state = StateManager()

    def ask(self, query: str):
        plan = self.reasoner.plan(query)
        return self.dispatcher.execute_plan(plan)


if __name__ == \"__main__\":
    agent = OynaAIAgent()
    print(agent.ask(\"Hva er dagens forventede vannforbruk?\"))""",

    "agent/manifest_loader.py": """import json
from pathlib import Path

class ManifestLoader:
    def __init__(self, manifest_path: str):
        self.path = Path(manifest_path)

    def load(self):
        with self.path.open(\"r\", encoding=\"utf-8\") as f:
            return json.load(f)""",

    "agent/dispatcher.py": """from tools.ha import HomeAssistantTool
from tools.nodered import NodeRedTool
from tools.influx import InfluxTool

class Dispatcher:
    \"\"\"Knytter reasoning-plan til riktige verktøy.\"\"\"

    def __init__(self, manifest):
        self.manifest = manifest
        self.tools = {
            \"home_assistant\": HomeAssistantTool(),
            \"nodered\": NodeRedTool(),
            \"influxdb\": InfluxTool(),
        }

    def execute_plan(self, plan):
        results = []
        for step in plan:
            tool = self.tools.get(step[\"tool\"])
            if not tool:
                results.append(f\"Unknown tool: {step['tool']}\")
                continue
            result = tool.execute(step[\"action\"], step.get(\"args\", {}))
            results.append(result)

        return results[-1] if len(results) == 1 else results""",

    "agent/reasoner.py": """class Reasoner:
    \"\"\"Planlegger arbeidssteg basert på spørsmål.\"\"\"

    def __init__(self, manifest):
        self.manifest = manifest

    def plan(self, query: str):
        q = query.lower()

        if \"pumpe\" in q:
            return [
                {\"tool\": \"home_assistant\", \"action\": \"get_entity_state\",
                 \"args\": {\"entity_id\": \"switch.pressure_pump_contactor\"}}
            ]

        if \"vannforbruk\" in q:
            return [
                {\"tool\": \"influxdb\", \"action\": \"query_latest\",
                 \"args\": {\"bucket\": \"haos-oyna-waterflow\"}}
            ]

        return [
            {\"tool\": \"nodered\", \"action\": \"invoke_flow\", \"args\": {\"query\": query}}
        ]""",

    "agent/state_manager.py": """class StateManager:
    \"\"\"Enkel arbeids- og kontekstminne for agenten.\"\"\"

    def __init__(self):
        self.memory = {}

    def set(self, key, value):
        self.memory[key] = value

    def get(self, key, default=None):
        return self.memory.get(key, default)""",

    # ----------------------------
    # Tools
    # ----------------------------
    "agent/tools/__init__.py": "",
    "agent/tools/ha.py": """class HomeAssistantTool:
    def execute(self, action, args):
        if action == \"get_entity_state\":
            entity = args[\"entity_id\"]
            return f\"[MOCK] HA state for {entity}\"

        if action == \"call_service\":
            return f\"[MOCK] Called service {args}\"

        return f\"Unknown HA action: {action}\"""",

    "agent/tools/nodered.py": """class NodeRedTool:
    def execute(self, action, args):
        if action == \"invoke_flow\":
            return f\"[MOCK] Node-RED flow invoked: {args}\"
        return f\"Unknown Node-RED action: {action}\"""",

    "agent/tools/influx.py": """class InfluxTool:
    def execute(self, action, args):
        if action == \"query_latest\":
            bucket = args[\"bucket\"]
            return f\"[MOCK] Latest data from bucket {bucket}\"
        return f\"Unknown InfluxDB action: {action}\"""",

    # ----------------------------
    # Memory modules
    # ----------------------------
    "agent/memory/__init__.py": "",
    "agent/memory/episodic_memory.py": "class EpisodicMemory:\n    pass",
    "agent/memory/vector_memory.py": "class VectorMemory:\n    pass",
    "agent/memory/working_memory.py": "class WorkingMemory:\n    pass",

    # ----------------------------
    # Utils
    # ----------------------------
    "agent/utils/__init__.py": "",
    "agent/utils/logging_utils.py": "def log(msg):\n    print(f\"[AI] {msg}\")",
    "agent/utils/schema_utils.py": "# Placeholder for schema utilities\n"
}


# ----------------------------
# GENERATION LOGIC
# ----------------------------
def create_structure():
    print("Generating AI Agent skeleton...\n")

    for path, content in files.items():
        file_path = ROOT / path

        # Ensure directories exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Created: {file_path}")

    print("\nDONE! 🎉  AI-agent skeleton generated successfully.")


if __name__ == "__main__":
    create_structure()
