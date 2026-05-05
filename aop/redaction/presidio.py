"""Optional Presidio integration for richer NER-based PII detection.

Wraps Microsoft Presidio if installed, falling back to no-op.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class PresidioRedactor:
    def __init__(self, *, language: str = "en") -> None:
        try:
            from presidio_analyzer import AnalyzerEngine  # type: ignore
            from presidio_anonymizer import AnonymizerEngine  # type: ignore
        except ImportError as e:
            raise ImportError(
                "Presidio integration requires presidio-analyzer and "
                "presidio-anonymizer. Install with: pip install presidio-analyzer "
                "presidio-anonymizer"
            ) from e
        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()
        self.language = language

    def redact(self, text: str, *, entities: Optional[List[str]] = None) -> str:
        results = self._analyzer.analyze(text=text, entities=entities, language=self.language)
        return self._anonymizer.anonymize(text=text, analyzer_results=results).text

    def redact_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.redact(value)
        if isinstance(value, dict):
            return {k: self.redact_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.redact_value(v) for v in value]
        return value
