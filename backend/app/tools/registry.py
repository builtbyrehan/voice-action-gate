"""Simulated tools (SR-7: everything is fake). Only the conversation engine
can reach this module — there is no route from the LLM to here (SR-1)."""


class ToolRegistry:
    def execute(self, action_name: str, evidence: list) -> dict:
        vals = {e.name: e.effective_value for e in evidence}
        if action_name == "DELETE_DATABASE":
            result = {"tool": "delete_database",
                      "deleted": f"{vals['database']}@{vals['environment']}",
                      "simulated": True}
        elif action_name == "DEPLOY_APPLICATION":
            result = {"tool": "deploy_application",
                      "deployed": f"{vals['application']} v{vals['version']} -> {vals['environment']}",
                      "simulated": True}
        elif action_name == "TRANSFER_FUNDS":
            result = {"tool": "transfer_funds",
                      "transferred": f"{vals['amount']} {vals['currency']} to {vals['recipient']}",
                      "simulated": True}
        else:
            result = {"tool": action_name.lower(), "simulated": True}
        return {"status": "COMPLETED", "result": result}