import time

from sqlalchemy.orm import Session

from app.application.agent.nodes.answer_node import AnswerNode
from app.application.agent.nodes.finalizer_node import FinalizerNode
from app.application.agent.nodes.input_guard import InputGuardNode
from app.application.agent.nodes.intent_node import IntentClassificationNode
from app.application.agent.nodes.planner_node import PlannerNode
from app.application.agent.nodes.policy_authorization_node import PolicyAuthorizationNode
from app.application.agent.nodes.result_formatter_node import ResultFormatterNode
from app.application.agent.nodes.retriever_node import RetrieverNode
from app.application.agent.nodes.sql_execution_node import SQLExecutionNode
from app.application.agent.nodes.sql_generation_node import SQLGenerationNode
from app.application.agent.nodes.sql_validation_node import SQLValidationNode
from app.application.agent.state import AgentState
from app.domain.services.authorization_domain_service import AuthorizationDomainService
from app.infrastructure.ai.openai_warmup import start_warmup_background

import os

# Path to trained intent artifacts (override via env var)
_ARTIFACTS_DIR = os.getenv(
    "INTENT_ARTIFACTS_DIR",
    str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent
        / "infrastructure" / "intent_recognition" / "artifacts")
)


class AgenticRagGraph:
    """
    Main agent graph.

    db session is injected per-request so each HTTP request
    gets its own isolated DB session.
    """

    # Stateless nodes (no DB) — shared across requests
    _guard = None
    _intent = None
    _policy = None
    _planner = None
    _answer = None
    _sql_gen = None
    _sql_validate = None
    _formatter = None
    _finalizer = None

    @classmethod
    def _init_shared_nodes(cls):
        """Initialize stateless nodes once (singleton pattern)."""
        if cls._guard is not None:
            return
        start_warmup_background()
        cls._guard = InputGuardNode()
        cls._intent = IntentClassificationNode(artifacts_dir=_ARTIFACTS_DIR)
        cls._policy = PolicyAuthorizationNode(AuthorizationDomainService())
        cls._planner = PlannerNode()
        cls._answer = AnswerNode()
        cls._sql_gen = SQLGenerationNode()
        cls._sql_validate = SQLValidationNode()
        cls._formatter = ResultFormatterNode()
        cls._finalizer = FinalizerNode()

    def __init__(self, db: Session):
        self._init_shared_nodes()
        # Stateful (DB-dependent) nodes — new instance per request
        self.retrieve = RetrieverNode(db=db)
        self.sql_exec = SQLExecutionNode(db=db)

    # -------------------------------------------------------
    # Timing wrapper
    # -------------------------------------------------------
    def _run_node(self, name: str, node, state: AgentState) -> AgentState:
        t0 = time.perf_counter()
        new_state = node.run(state)
        ms = (time.perf_counter() - t0) * 1000.0

        if new_state.debug_timings is None:
            new_state.debug_timings = {}
        new_state.debug_timings[name] = round(ms, 2)

        print(f"[TIMING] {name}: {ms:.2f} ms")
        return new_state

    def _finalize_and_log(self, total_start: float, state: AgentState) -> AgentState:
        state = self._run_node("Finalizer", self._finalizer, state)
        total_ms = (time.perf_counter() - total_start) * 1000.0
        print(f"[TIMING] TOTAL: {total_ms:.2f} ms")
        timings = state.debug_timings or {}
        if timings:
            print(f"[TIMING] BREAKDOWN: {' | '.join(f'{k}={v}ms' for k, v in timings.items())}")
        return state

    # -------------------------------------------------------
    # Main run
    # -------------------------------------------------------
    def run(self, state: AgentState) -> AgentState:
        total_start = time.perf_counter()

        # 1) Guard
        state = self._run_node("InputGuard", self._guard, state)
        if not state.is_valid:
            return self._finalize_and_log(total_start, state)

        # 2) Intent
        state = self._run_node("IntentClassification", self._intent, state)
        if state.is_blocked:
            return self._finalize_and_log(total_start, state)

        # 3) Policy
        state = self._run_node("PolicyAuthorization", self._policy, state)
        if state.is_blocked:
            return self._finalize_and_log(total_start, state)

        # 4) Planner
        state = self._run_node("Planner", self._planner, state)
        plan = state.execution_plan or []

        # STATIC
        if "STATIC" in plan and "RAG" not in plan and "SQL" not in plan:
            return self._finalize_and_log(total_start, state)

        # RAG
        if "RAG" in plan:
            state = self._run_node("Retriever", self.retrieve, state)
            if state.is_blocked:
                return self._finalize_and_log(total_start, state)
            state = self._run_node("AnswerNode", self._answer, state)
            return self._finalize_and_log(total_start, state)

        # SQL
        if "SQL" in plan:
            if not state.domain:
                state.is_blocked = True
                state.block_reason = "Analytics query missing domain."
                return self._finalize_and_log(total_start, state)

            state = self._run_node("SQLGeneration", self._sql_gen, state)
            if state.is_blocked:
                return self._finalize_and_log(total_start, state)
            state = self._run_node("SQLValidation", self._sql_validate, state)
            if state.is_blocked:
                return self._finalize_and_log(total_start, state)

            state = self._run_node("SQLExecution", self.sql_exec, state)
            if state.is_blocked:
                return self._finalize_and_log(total_start, state)

            state = self._run_node("ResultFormatter", self._formatter, state)
            return self._finalize_and_log(total_start, state)

        # Fallback
        state.is_blocked = True
        state.block_reason = "Unhandled execution plan."
        return self._finalize_and_log(total_start, state)
