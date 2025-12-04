class NodeRedTool:
    def execute(self, action, args):
        if action == "invoke_flow":
            return f"[MOCK] Node-RED flow invoked: {args}"
        return f"Unknown Node-RED action: {action}"