from app.application.agent.state import AgentState


class PlannerNode:
    """
    Decides execution path based on classified intents.
    Supports multi-intent. Pure routing logic.
    """

    def run(self, state: AgentState) -> AgentState:
        if state.is_blocked:
            return state

        intents = state.intents or []
        execution_plan = []
        required_tools = set()

        for intent in intents:
            if intent in {"greeting", "other", "illegal_request"}:
                execution_plan.append("STATIC")
            elif intent in {"help", "navigation"}:
                execution_plan.append("RAG")
                required_tools.add("knowledge_search")
            elif intent == "analytics":
                execution_plan.append("SQL")
                required_tools.update({"sql_generator", "sql_executor"})
            else:
                execution_plan.append("STATIC")

        # Dedupe while preserving order
        state.execution_plan = list(dict.fromkeys(execution_plan))
        state.required_tools = list(required_tools)
        return state
