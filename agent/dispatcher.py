from tools.ha import HomeAssistantTool
from tools.nodered import NodeRedTool
from tools.influx import InfluxTool

class Dispatcher:
    """Knytter reasoning-plan til riktige verktøy."""

    def __init__(self, manifest):
        self.manifest = manifest
        self.tools = {
            "home_assistant": HomeAssistantTool(),
            "nodered": NodeRedTool(),
            "influxdb": InfluxTool(),
        }

    def execute_plan(self, plan):
        results = []
        for step in plan:
            tool = self.tools.get(step["tool"])
            if not tool:
                results.append(f"Unknown tool: {step['tool']}")
                continue
            result = tool.execute(step["action"], step.get("args", {}))
            results.append(result)

        return results[-1] if len(results) == 1 else results