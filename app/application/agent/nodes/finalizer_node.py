from app.application.agent.state import AgentState


class FinalizerNode:
    """
    Produces the final API-ready response with consistent structure.
    """

    def _normalize_data(self, data):
        if data is None:
            return None
        if isinstance(data, str):
            return {"message": data}
        if isinstance(data, dict):
            return data
        return {"message": str(data)}

    def run(self, state: AgentState) -> AgentState:
        normalized = self._normalize_data(state.response)

        if normalized is None:
            state.response = {
                "success": False,
                "error": "no_response_generated",
                "data": {"message": "Sorry! This is out of my scope."},
                "usage": state.usage,
                "execution_plan": state.execution_plan,
                "intent": state.intents,
            }
            return state

        state.response = {
            "success": True,
            "intent": state.intents,
            "execution_plan": state.execution_plan,
            "data": normalized,
            "usage": state.usage,
        }
        return state
