from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import joblib

from src.common.models import PHIRedactionResult


class PHIGuard:
    """
    Privacy guard for report/dashboard evidence.

    The model detects whether free-text evidence contains PHI. Regex rules then
    redact common identifiers so stored/demo evidence remains safe to display.
    """

    def __init__(self, model):
        self.model = model
        self.patterns = [
            (re.compile(r"(?<=Patient )([A-Z][a-z]+ [A-Z][a-z]+)"), "[REDACTED_NAME]"),
            (re.compile(r"\b[Pp]-\d{3,5}\b"), "[REDACTED_ID]"),
            (re.compile(r"\bID #?\d+\b"), "ID [REDACTED]"),
            (re.compile(r"(?<=Condition: )[^.;,\n]+"), "[REDACTED_MEDICAL]"),
            (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_ID]"),
        ]

    @classmethod
    def load(cls, models_dir: Path):
        pipeline_path = models_dir / "ARS PHI.pkl"
        dict_path = models_dir / "ars_phi_model.pkl"
        if pipeline_path.exists():
            return cls(joblib.load(pipeline_path))
        bundle = joblib.load(dict_path)
        return cls(bundle)

    def _predict(self, text: str) -> bool:
        if isinstance(self.model, dict):
            model = self.model.get("model")
            vectorizer = self.model.get("vectorizer")
            if model is not None and vectorizer is not None:
                return bool(model.predict(vectorizer.transform([text]))[0])
            if model is not None and hasattr(model, "predict"):
                return bool(model.predict([text])[0])
        return bool(self.model.predict([text])[0])

    def _regex_detect(self, text: str) -> bool:
        return any(pattern.search(text) for pattern, _ in self.patterns)

    def redact(self, text: str) -> PHIRedactionResult:
        model_detected = False
        try:
            model_detected = self._predict(text)
        except Exception:
            model_detected = False

        regex_detected = self._regex_detect(text)
        phi_detected = model_detected or regex_detected

        redacted = text
        count = 0
        if phi_detected:
            for pattern, replacement in self.patterns:
                redacted, replacements = pattern.subn(replacement, redacted)
                count += replacements

        return PHIRedactionResult(
            phi_detected=phi_detected,
            original_text=text,
            redacted_text=redacted,
            redaction_count=count,
            reason="PHI model and regex privacy guard evaluated report evidence.",
            metadata={"model_detected": model_detected, "regex_detected": regex_detected, "model": "ARS PHI.pkl"},
        )


def build_evidence_text(document: Dict[str, Any], analysis: Dict[str, Any] | None = None) -> str:
    device_id = document.get("device_id", "unknown")
    device_type = document.get("device_type", "unknown")
    ward = document.get("ward", "unknown")
    attack_type = document.get("attack_type", "normal")
    patient_ref = document.get("patient_name") or document.get("patient") or ""
    patient_id = document.get("patient_id") or document.get("patientId") or ""
    clinical_condition = document.get("condition") or document.get("diagnosis") or ""
    action = ""
    if analysis:
        action = str(analysis.get("decision", {}).get("action", ""))

    patient_clause = f" Patient {patient_ref}" if patient_ref else ""
    id_clause = f" ID {patient_id}" if patient_id else ""
    condition_clause = f" Condition: {clinical_condition}" if clinical_condition else ""
    return (
        f"Device {device_id} ({device_type}) in ward {ward} reported attack_type={attack_type}. "
        f"Recommended action={action}.{patient_clause}{id_clause}{condition_clause}"
    )
