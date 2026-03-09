from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentState:
    # -------- Input --------
    message: str | dict | None = None

    # NOTE: user_id removed — no auth required. Kept optional for
    # future use (e.g., scoped SQL queries) but never enforced.
    user_id: Optional[int] = None

    # -------- Guard --------
    is_valid: bool = True
    fallback_reason: Optional[str] = None
    is_blocked: bool = False
    block_reason: Optional[str] = None

    # -------- Intent --------
    intents: Optional[List[str]] = None
    domain: Optional[List[str]] = None

    # -------- Execution Plan --------
    execution_plan: Optional[List[str]] = None
    required_tools: List[str] = field(default_factory=list)

    # -------- SQL --------
    generated_sql: Optional[dict] = None
    sql_rows: Optional[List[Dict[str, Any]]] = None
    debug_sql: Optional[Dict[str, Any]] = None

    # -------- RAG --------
    rag_chunks: Optional[List[str]] = None

    # -------- Output --------
    response: Optional[Dict[str, Any]] = None

    # -------- Usage --------
    usage: Dict[str, int] = field(
        default_factory=lambda: {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
    )

    # -------- Debug --------
    debug_timings: Optional[Dict[str, float]] = None
