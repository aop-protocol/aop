"""PII redaction pipeline.

Apply regex- and rule-based redaction to AOP events before they leave the
client process or are written into storage. Defense-in-depth: also
recommended on the collector side.

Default ruleset masks:
  • emails, phone numbers, SSN-like patterns
  • credit-card numbers (Luhn-validated)
  • JWT-like bearer tokens
  • OpenAI / Anthropic / AWS access keys
  • generic "api_key" / "password" / "secret" fields
"""

from __future__ import annotations

from .rules import (
    DEFAULT_RULES,
    RedactionRule,
    add_rule,
    redact_event,
    redact_value,
)

__all__ = [
    "DEFAULT_RULES",
    "RedactionRule",
    "add_rule",
    "redact_event",
    "redact_value",
]
