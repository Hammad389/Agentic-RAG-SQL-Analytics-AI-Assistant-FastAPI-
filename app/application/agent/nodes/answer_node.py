from app.application.agent.state import AgentState
from app.infrastructure.ai.openai_client import OpenAIClientProvider
from app.infrastructure.prompts.rag_system_prompt import RAG_SYSTEM_PROMPT


class AnswerNode:
    def __init__(self):
        self.client = OpenAIClientProvider.get_client()

    def run(self, state: AgentState) -> AgentState:
        if state.is_blocked:
            return state

        if not state.rag_chunks:
            state.response = {"message": "This is not supported in the current our documentation."}
            return state

        context_text = "\n\n---\n\n".join(state.rag_chunks)
        prompt = f"""
            CONTEXT:
            {context_text}

            QUESTION:
            {state.message}
            """.strip()

        resp = self.client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_output_tokens=400,
        )

        usage = getattr(resp, "usage", None)
        if usage:
            state.usage["input_tokens"] += getattr(usage, "input_tokens", 0) or 0
            state.usage["output_tokens"] += getattr(usage, "output_tokens", 0) or 0
            state.usage["total_tokens"] += getattr(usage, "total_tokens", 0) or 0

        state.response = {"message": resp.output_text or ""}
        return state
