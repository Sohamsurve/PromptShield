"""ONNX text classifier with gating (README §5.6)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

# Repo models/ — walk up from this file
_DEFAULT_MODEL = Path(__file__).resolve().parents[5] / "models" / "classifier.onnx"
_DEFAULT_CAL = Path(__file__).resolve().parents[5] / "models" / "calibration.json"


def classifier_available(path: Path | None = None) -> bool:
    model = Path(path or os.getenv("CLASSIFIER_PATH", _DEFAULT_MODEL))
    cal = model.with_name("calibration.json")
    if not cal.exists():
        cal = _DEFAULT_CAL
    return cal.exists() or model.exists()


def should_run_classifier(
    *,
    pre_score: float,
    gate: float,
    hidden: bool,
    decoded: bool,
    trust_t1: bool,
) -> bool:
    if trust_t1 or hidden or decoded:
        return True
    return pre_score >= gate


def _temperature_scale(prob: float, temperature: float) -> float:
    # Convert prob→logit, scale, sigmoid
    import math

    p = min(max(prob, 1e-6), 1 - 1e-6)
    logit = math.log(p / (1 - p))
    z = logit / max(temperature, 1e-3)
    return 1 / (1 + math.exp(-z))


@dataclass
class Classifier:
    session: Any
    temperature: float = 1.0
    vocabulary: dict[str, int] | None = None
    idf: list[float] | None = None
    coef: list[float] | None = None
    intercept: float = 0.0
    backend: str = "onnx"

    @classmethod
    def load(cls, model_path: Path | None = None) -> "Classifier":
        path = Path(model_path or os.getenv("CLASSIFIER_PATH", _DEFAULT_MODEL))
        cal_path = path.with_name("calibration.json")
        if not cal_path.exists():
            cal_path = _DEFAULT_CAL
        temperature = 1.0
        meta: dict[str, Any] = {}
        if cal_path.exists():
            meta = json.loads(cal_path.read_text(encoding="utf-8"))
            temperature = float(meta.get("temperature", 1.0))

        # Prefer pure-python fallback weights bundled in calibration for demos without onnxruntime
        if meta.get("coef") is not None and meta.get("vocabulary") is not None:
            return cls(
                session=None,
                temperature=temperature,
                vocabulary={str(k): int(v) for k, v in meta["vocabulary"].items()},
                idf=[float(x) for x in meta.get("idf", [])],
                coef=[float(x) for x in meta["coef"]],
                intercept=float(meta.get("intercept", 0.0)),
                backend="numpy",
            )

        import onnxruntime as ort

        sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        return cls(session=sess, temperature=temperature, backend="onnx")

    def predict_proba(self, text: str) -> float:
        if self.backend == "numpy":
            return self._predict_numpy(text)
        # ONNX path expects a single string input named "text" or float features — use numpy path if present
        return self._predict_numpy(text)

    def _predict_numpy(self, text: str) -> float:
        import math
        import re

        assert self.vocabulary is not None and self.coef is not None
        tokens = re.findall(r"[a-z0-9_]+", text.lower())
        tf: dict[int, float] = {}
        for tok in tokens:
            idx = self.vocabulary.get(tok)
            if idx is None:
                continue
            tf[idx] = tf.get(idx, 0.0) + 1.0
        if tokens:
            for k in list(tf):
                tf[k] /= len(tokens)
        # tf-idf
        score = self.intercept
        for idx, val in tf.items():
            idf = self.idf[idx] if self.idf and idx < len(self.idf) else 1.0
            if idx < len(self.coef):
                score += self.coef[idx] * val * idf
        prob = 1 / (1 + math.exp(-score))
        return _temperature_scale(prob, self.temperature)


_UNSET = object()
_CLF: Any = _UNSET


def get_classifier() -> Classifier | None:
    global _CLF
    if _CLF is not _UNSET:
        return _CLF  # type: ignore[return-value]
    if not classifier_available():
        _CLF = None
        return None
    try:
        _CLF = Classifier.load()
    except Exception:
        _CLF = None
    return _CLF  # type: ignore[return-value]


def reset_classifier_cache() -> None:
    global _CLF
    _CLF = _UNSET
