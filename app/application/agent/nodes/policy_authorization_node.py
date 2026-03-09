from app.application.agent.state import AgentState
from app.domain.enums import FallbackMessage, FallbackReason
from app.domain.services.authorization_domain_service import AuthorizationDomainService


class PolicyAuthorizationNode:
    """
    Enforces business rules before execution.

    NOTE: Authentication check removed — this agent is publicly queryable.
    Remaining checks:
      1. Illegal request blocking
      2. Greeting short-circuit
      3. Cross-domain violation for analytics
    """

    def __init__(self, auth_service: AuthorizationDomainService):
        self.auth_service = auth_service

    def run(self, state: AgentState) -> AgentState:
        intents = state.intents or []
        domain = state.domain

        # 1) Illegal request dominates all
        if "illegal_request" in intents:
            state.is_blocked = True
            state.block_reason = FallbackReason.ILLEGAL_INPUT
            state.response = {
                "intent": FallbackReason.ILLEGAL_INPUT.value,
                "message": FallbackMessage.ILLEGAL_INPUT.message,
            }
            return state

        # 2) Pure greeting short-circuit
        if intents == ["greeting"]:
            state.block_reason = FallbackReason.GREETING
            state.response = {
                "intent": FallbackReason.GREETING.value,
                "message": FallbackMessage.GREETING.message,
            }
            return state

        # 3) Cross-domain violation for analytics
        if "analytics" in intents:
            if self.auth_service.is_cross_domain_violation(domain):
                state.is_blocked = True
                state.block_reason = "cross_domain_violation"
                state.response = {
                    "intent": "other",
                    "message": "This request crosses multiple restricted domains.",
                }
                return state

        # Passed all checks
        state.is_blocked = False
        state.block_reason = None
        state.response = None
        return state
