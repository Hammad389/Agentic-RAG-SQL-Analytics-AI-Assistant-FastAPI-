from app.application.agent.state import AgentState
from app.infrastructure.intent_recognition.domain_router import infer_domains
from app.infrastructure.intent_recognition.local_intent_service import LocalIntentService


class IntentClassificationNode:
    def __init__(self, artifacts_dir: str):
        self.intent_service = LocalIntentService(artifacts_dir=artifacts_dir)

    def run(self, state: AgentState) -> AgentState:
        result = self.intent_service.classify(state.message)
        state.intents = result.intents or []

        # Suppress greeting if stronger intent is present
        if "analytics" in state.intents or "help" in state.intents or "navigation" in state.intents:
            state.intents = [i for i in state.intents if i != "greeting"]

        # Domain inference only for analytics
        if "analytics" in state.intents:
            state.domain = infer_domains(state.message)
            if not state.domain:
                state.is_blocked = True
                state.block_reason = "Analytics request detected but domain could not be inferred."
                return state
        else:
            state.domain = None

        valid_set = {"greeting", "illegal_request", "navigation", "analytics", "help", "other"}
        state.is_valid = bool(state.intents) and all(i in valid_set for i in state.intents)

        print(f"[IntentNode] intents={state.intents}, domain={state.domain}")
        return state
