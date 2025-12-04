class HomeAssistantTool:
    def execute(self, action, args):
        if action == "get_entity_state":
            entity = args["entity_id"]
            return f"[MOCK] HA state for {entity}"

        if action == "call_service":
            return f"[MOCK] Called service {args}"

        return f"Unknown HA action: {action}"