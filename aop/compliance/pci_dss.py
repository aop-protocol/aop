"""PCI-DSS helpers: cardholder-data masking and access logging."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict

from ..redaction.rules import RedactionRule, add_rule


_PAN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def mask_pan(text: str) -> str:
    """Mask everything but the last 4 digits of a Primary Account Number."""
    def _mask(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) < 13:
            return m.group(0)
        last4 = digits[-4:]
        return "*" * (len(digits) - 4) + last4
    return _PAN.sub(_mask, text)


def install_pan_masking() -> None:
    add_rule(RedactionRule(
        name="pan",
        pattern=_PAN,
        replacement="<masked-pan>",
    ))


def tag_pci_event(event: Dict[str, Any], *, requirement: str,
                  control: str) -> Dict[str, Any]:
    metadata = dict(event.get("metadata") or {})
    metadata["pci_dss"] = {
        "requirement": requirement,
        "control": control,
        "tagged_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**event, "metadata": metadata}
