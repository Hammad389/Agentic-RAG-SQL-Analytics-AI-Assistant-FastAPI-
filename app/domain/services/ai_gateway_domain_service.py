from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class IntentResult:
    intents: List[str]
    domain: Optional[List[str]]
    usage: Optional[Dict[str, int]]


class AIGatewayDomainService:
    """
    Domain abstraction for AI operations.
    Application layer depends on THIS.
    Infrastructure layer implements it.
    """

    @abstractmethod
    def classify_intent(self, *, user_message: str, context: str) -> IntentResult:
        raise NotImplementedError

    @abstractmethod
    def generate_response(
        self,
        *,
        user_message: str,
        intent: str,
        domain: Optional[List[str]] = None,
        context: Optional[dict] = None,
    ) -> Tuple[dict | str, Optional[Dict[str, int]]]:
        raise NotImplementedError
