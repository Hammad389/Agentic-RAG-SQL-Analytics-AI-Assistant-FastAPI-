import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

DEFAULT_ENCODER = "sentence-transformers/all-MiniLM-L6-v2"

DEFAULT_INTENTS = [
    "greeting",
    "help",
    "navigation",
    "analytics",
    "illegal_request",
    "other",
]


@dataclass(frozen=True)
class TrainResult:
    artifacts_dir: Path
    encoder_name: str
    labels: List[str]
    report: str
    n_samples: int


def _normalize(s: str) -> str:
    s = s.lower().strip()
    return re.sub(r"\s+", " ", s)


def _load_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    with dataset_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("Dataset must be a non-empty JSON list.")
    return data


def train_intent_model(
    *,
    dataset_path: Path,
    artifacts_dir: Path,
    encoder_name: str = DEFAULT_ENCODER,
    allowed_intents: Optional[List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> TrainResult:
    allowed_intents = allowed_intents or DEFAULT_INTENTS
    data = _load_dataset(dataset_path)

    texts: List[str] = []
    y_raw: List[List[str]] = []

    for idx, row in enumerate(data):
        q = row.get("query")
        intents = (row.get("target") or {}).get("intent")
        if not q or not isinstance(intents, list) or not intents:
            raise ValueError(f"Row #{idx} invalid. Need 'query' and target.intent (non-empty list).")
        for it in intents:
            if it not in allowed_intents:
                raise ValueError(f"Unknown intent '{it}'. Allowed: {allowed_intents}")
        texts.append(_normalize(q))
        y_raw.append(intents)

    encoder = SentenceTransformer(encoder_name)
    X = encoder.encode(texts, normalize_embeddings=True, convert_to_numpy=True)

    mlb = MultiLabelBinarizer(classes=allowed_intents)
    Y = mlb.fit_transform(y_raw)

    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=test_size, random_state=random_state)

    clf = OneVsRestClassifier(LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs"))
    clf.fit(X_train, y_train)

    pred = clf.predict(X_test)
    report = classification_report(y_test, pred, target_names=mlb.classes_, zero_division=0)

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(mlb, artifacts_dir / "intent_mlb.joblib")
    joblib.dump(clf, artifacts_dir / "intent_clf.joblib")
    joblib.dump(
        {"encoder_name": encoder_name, "labels": allowed_intents, "n_samples": len(texts)},
        artifacts_dir / "intent_meta.joblib",
    )

    return TrainResult(
        artifacts_dir=artifacts_dir,
        encoder_name=encoder_name,
        labels=allowed_intents,
        report=report,
        n_samples=len(texts),
    )
