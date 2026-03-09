import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
from sentence_transformers import SentenceTransformer


@dataclass
class LocalIntentResult:
    intents: List[str]
    domain: Optional[List[str]] = None
    usage: Optional[Dict[str, int]] = None


class LocalIntentService:
    """
    Loads saved artifacts and predicts intents locally.
    Train once, load once, reuse forever.
    """

    _encoder: Optional[SentenceTransformer] = None
    _encoder_name: Optional[str] = None

    def __init__(
        self,
        artifacts_dir: str,
        intent_threshold: float = 0.50,
        greeting_threshold: float = 0.60,
        illegal_threshold: float = 0.70,
        other_threshold: float = 0.70,
    ):
        self.artifacts_dir = Path(artifacts_dir)

        self.mlb = joblib.load(self.artifacts_dir / "intent_mlb.joblib")
        self.clf = joblib.load(self.artifacts_dir / "intent_clf.joblib")
        self.meta: Dict[str, Any] = joblib.load(self.artifacts_dir / "intent_meta.joblib")

        enc_name = self.meta["encoder_name"]

        if LocalIntentService._encoder is None or LocalIntentService._encoder_name != enc_name:
            LocalIntentService._encoder = SentenceTransformer(enc_name)
            LocalIntentService._encoder_name = enc_name

        self.encoder = LocalIntentService._encoder
        self.allowed_intents = set(self.meta["labels"])

        self.intent_threshold = intent_threshold
        self.greeting_threshold = greeting_threshold
        self.illegal_threshold = illegal_threshold
        self.other_threshold = other_threshold

    def _normalize(self, s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"\s+", " ", s)
        return s

    def classify(self, user_message: str) -> LocalIntentResult:
        text = self._normalize(user_message)
        emb = self.encoder.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
        emb = emb.reshape(1, -1)

        probs = self.clf.predict_proba(emb)[0]
        prob_map = {lbl: float(p) for lbl, p in zip(self.mlb.classes_, probs)}

        if prob_map.get("illegal_request", 0.0) >= self.illegal_threshold:
            return LocalIntentResult(intents=["illegal_request"])

        if prob_map.get("other", 0.0) >= self.other_threshold:
            return LocalIntentResult(intents=["other"])

        intents: List[str] = []
        for lbl, p in prob_map.items():
            if lbl not in self.allowed_intents:
                continue
            if lbl == "greeting":
                if p >= self.greeting_threshold:
                    intents.append(lbl)
            elif lbl not in {"illegal_request", "other"}:
                if p >= self.intent_threshold:
                    intents.append(lbl)

        if not intents:
            intents = ["other"]

        print("Probabilities:", prob_map)
        return LocalIntentResult(intents=sorted(set(intents)))
