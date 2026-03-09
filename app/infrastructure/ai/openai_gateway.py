import json
import logging
from typing import Dict, List, Optional, Tuple

from app.domain.services.ai_gateway_domain_service import AIGatewayDomainService, IntentResult
from app.infrastructure.ai.openai_client import OpenAIClientProvider
from app.infrastructure.prompts.intent_prompt import intent_recognition_prompt

logger = logging.getLogger("agenic_rag.ai")


class OpenAIGateway(AIGatewayDomainService):
    """OpenAI implementation of AI Gateway."""

    def __init__(self):
        self.client = OpenAIClientProvider.get_client()

    def _extract_usage(self, response) -> Optional[Dict[str, int]]:
        usage = getattr(response, "usage", None)
        if not usage:
            return None
        return {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
            "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
        }

    def parse_json(self, text: str) -> dict:
        try:
            return json.loads(text.strip())
        except Exception:
            raise ValueError("Invalid JSON returned from intent model.")

    def classify_intent(self, *, user_message: str, context: str) -> IntentResult:
        try:
            response = self.client.responses.create(
                model="gpt-4o-mini",
                temperature=0,
                max_output_tokens=200,
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": intent_recognition_prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": context + "\n" + user_message}]},
                ],
            )
            parsed = self.parse_json(response.output_text or "")
            usage = self._extract_usage(response)
            intent = parsed.get("intent", "other")
            domain = parsed.get("domain")
            if isinstance(domain, str):
                domain = [domain]
            return IntentResult(intents=intent, domain=domain, usage=usage)
        except Exception as exc:
            logger.warning("Intent classification failed: %s", exc)
            return IntentResult(intents=["other"], domain=None, usage=None)

    def generate_response(
        self,
        *,
        user_message: str,
        intent: str,
        domain: Optional[List[str]] = None,
        context: Optional[dict] = None,
    ) -> Tuple[dict | str, Optional[Dict[str, int]]]:
        try:
            system_prompt = self._resolve_prompt(intent=intent)
            response = self.client.responses.create(
                model="gpt-3.5-turbo",
                temperature=0,
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": user_message}]},
                ],
            )
            usage = self._extract_usage(response)
            text = response.output_text or ""
            try:
                parsed = json.loads(text)
                return parsed, usage
            except Exception:
                return text, usage
        except Exception as exc:
            logger.exception("AI generation failed: %s", exc)
            return {"error": "ai_failure"}, None

    def _resolve_prompt(self, *, intent: str) -> str:
        if intent == "help":
            return "You are AI assistant. Provide help responses."
        if intent == "navigation":
            return "You are AI assistant. Provide navigation guidance."
        if intent == "analytics":
            return (
                "Generate ONLY a JSON object.\n"
                "Read-only SQL (SELECT/WITH only).\n"
                "No semicolons.\n"
                'Output: {"sql":"...","template":"..."}'
            )
        return "You are AI assistant."
