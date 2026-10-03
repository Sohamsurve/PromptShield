"""TF-IDF logistic classifier with explicit fallback (README §5.6)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_CAL = Path(__file__).resolve().parents[5] / "models" / "calibration.json"
_PLACEHOLDER_MARKERS = (b"ONNX_PLACEHOLDER", b"PLACEHOLDER")


class ClassifierConfigError(RuntimeError):
    """Raised when CLASSIFIER_PATH points at a missing or fake ONNX file."""


def _is_fake_onnx(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return True
    raw = path.read_bytes()
    if len(raw) < 64:
        return True
    if any(m in raw for m in _PLACEHOLDER_MARKERS):
        return True
    # Real ONNX files typically start with a protobuf encoding; reject empty/marker files.
    return False


def classifier_available(path: Path | None = None) -> bool:
    """True if TF-IDF calibration weights are loadable."""
    cal = Path(os.getenv("CLASSIFIER_CALIBRATION", _DEFAULT_CAL))
    if path is not None:
        cal = Path(path).with_name("calibration.json") if Path(path).suffix == ".onnx" else Path(path)
    return cal.exists()


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
    import math

    p = min(max(prob, 1e-6), 1 - 1e-6)
    logit = math.log(p / (1 - p))
    z = logit / max(temperature, 1e-3)
    return 1 / (1 + math.exp(-z))


@dataclass
class Classifier:
    temperature: float = 1.0
    vocabulary: dict[str, int] | None = None
    idf: list[float] | None = None
    coef: list[float] | None = None
    intercept: float = 0.0
    backend: str = "tfidf_logreg"

    @classmethod
    def load(cls, model_path: Path | None = None) -> "Classifier":
        """Load TF-IDF+logreg from calibration.json.

        If CLASSIFIER_PATH / model_path points at an .onnx file that is missing or a
        placeholder, raise ClassifierConfigError (fail loudly). Otherwise use the
        explicit tfidf_logreg fallback from calibration.json.
        """
        env_path = os.getenv("CLASSIFIER_PATH")
        path = Path(model_path or env_path) if (model_path or env_path) else None

        if path is not None and str(path).endswith(".onnx"):
            if _is_fake_onnx(path):
                raise ClassifierConfigError(
                    f"Configured ONNX classifier missing or fake: {path}. "
                    "Remove CLASSIFIER_PATH or provide a real ONNX model; "
                    "default backend is tfidf_logreg via models/calibration.json."
                )
            # Real ONNX not implemented in this release — fail loudly rather than silent fake.
            raise ClassifierConfigError(
                f"ONNX runtime path requested ({path}) but this build only ships "
                "tfidf_logreg. Unset CLASSIFIER_PATH to use models/calibration.json."
            )

        cal_path = Path(os.getenv("CLASSIFIER_CALIBRATION", _DEFAULT_CAL))
        if not cal_path.exists():
            raise ClassifierConfigError(
                f"TF-IDF calibration not found at {cal_path}. Run `make train`."
            )
        meta: dict[str, Any] = json.loads(cal_path.read_text(encoding="utf-8"))
        backend = str(meta.get("backend", "tfidf_logreg"))
        if backend not in {"tfidf_logreg", "numpy_tfidf_logreg", "numpy"}:
            raise ClassifierConfigError(f"Unsupported classifier backend in calibration: {backend}")
        if meta.get("coef") is None or meta.get("vocabulary") is None:
            raise ClassifierConfigError(f"calibration.json missing coef/vocabulary: {cal_path}")

        logger.info("classifier_backend=tfidf_logreg calibration=%s", cal_path)
        return cls(
            temperature=float(meta.get("temperature", 1.0)),
            vocabulary={str(k): int(v) for k, v in meta["vocabulary"].items()},
            idf=[float(x) for x in meta.get("idf", [])],
            coef=[float(x) for x in meta["coef"]],
            intercept=float(meta.get("intercept", 0.0)),
            backend="tfidf_logreg",
        )

    def predict_proba(self, text: str) -> float:
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
        score = self.intercept
        for idx, val in tf.items():
            idf = self.idf[idx] if self.idf and idx < len(self.idf) else 1.0
            if idx < len(self.coef):
                score += self.coef[idx] * val * idf
        prob = 1 / (1 + math.exp(-max(-50, min(50, score))))
        return _temperature_scale(prob, self.temperature)


_UNSET = object()
_CLF: Any = _UNSET


def get_classifier() -> Classifier | None:
    global _CLF
    if _CLF is not _UNSET:
        return _CLF  # type: ignore[return-value]
    try:
        _CLF = Classifier.load()
    except ClassifierConfigError as exc:
        logger.error("classifier_config_error: %s", exc)
        # Missing calibration → degrade; misconfigured ONNX → re-raise so ops notice
        if "ONNX" in str(exc) or "onnx" in str(exc):
            raise
        _CLF = None
    except Exception as exc:
        logger.error("classifier_load_failed: %s", exc)
        _CLF = None
    return _CLF  # type: ignore[return-value]


def reset_classifier_cache() -> None:
    global _CLF
    _CLF = _UNSET
