import json
import time

from app.application.agent.state import AgentState
from app.domain.sql_schema_registry import get_schemas
from app.infrastructure.ai.openai_client import OpenAIClientProvider
from app.infrastructure.prompts.sql_system_prompt import SQL_SYSTEM_PROMPT


class SQLGenerationNode:
    def __init__(self):
        self.client = OpenAIClientProvider.get_client()

    def run(self, state: AgentState) -> AgentState:
        if state.is_blocked:
            return state

        t0 = time.perf_counter()
        schema = get_schemas(state.domain)
        schema_ms = (time.perf_counter() - t0) * 1000.0

        user_prompt = f"""
            QUESTION:
            {state.message}

            SCHEMA:
            {schema}
            """.strip()

        prompt_chars = len(user_prompt)

        t1 = time.perf_counter()
        resp = self.client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SQL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_output_tokens=400,
        )
        openai_ms = (time.perf_counter() - t1) * 1000.0

        usage = getattr(resp, "usage", None)
        if usage:
            state.usage["input_tokens"] += getattr(usage, "input_tokens", 0) or 0
            state.usage["output_tokens"] += getattr(usage, "output_tokens", 0) or 0
            state.usage["total_tokens"] += getattr(usage, "total_tokens", 0) or 0

        t2 = time.perf_counter()
        raw = (resp.output_text or "").strip()

        try:
            payload = json.loads(raw)
        except Exception:
            state.is_blocked = True
            state.block_reason = "invalid_structured_query"
            state.debug_sql = {
                "schema_ms": round(schema_ms, 2),
                "openai_ms": round(openai_ms, 2),
                "json_ms": round((time.perf_counter() - t2) * 1000.0, 2),
                "prompt_chars": prompt_chars,
                "raw_preview": raw[:250],
            }
            return state

        json_ms = (time.perf_counter() - t2) * 1000.0
        state.debug_sql = {
            "schema_ms": round(schema_ms, 2),
            "openai_ms": round(openai_ms, 2),
            "json_ms": round(json_ms, 2),
            "prompt_chars": prompt_chars,
        }

        if not isinstance(payload, dict) or payload.get("error"):
            state.is_blocked = True
            state.block_reason = payload.get("error") if isinstance(payload, dict) else "invalid_structured_query"
            return state

        state.generated_sql = payload
        return state
