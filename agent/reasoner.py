class Reasoner:
    """Planlegger arbeidssteg basert på spørsmål."""

    def __init__(self, manifest):
        self.manifest = manifest

    def plan(self, query: str):
        q = query.lower()

        if "pumpe" in q:
            return [
                {"tool": "home_assistant", "action": "get_entity_state",
                 "args": {"entity_id": "switch.pressure_pump_contactor"}}
            ]

        if "vannforbruk" in q:
            return [
                {"tool": "influxdb", "action": "query_latest",
                 "args": {"bucket": "haos-oyna-waterflow"}}
            ]

        return [
            {"tool": "nodered", "action": "invoke_flow", "args": {"query": query}}
        ]