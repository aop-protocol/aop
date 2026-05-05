"""User feedback / eval-signal adapter.

A generic protocol for capturing feedback signals on traces — used by
evaluation pipelines, RLHF data collection, customer telemetry, etc.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseAdapter, EventHandle


class FeedbackAdapter(BaseAdapter):
    PROTOCOL = "feedback"

    def log_thumb(
        self, agent_id: str, target_event_id: str, value: int,
        comment: Optional[str] = None, user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        if value not in (-1, 0, 1):
            raise ValueError("value must be -1, 0, or 1")
        et = "feedback.thumb.up" if value == 1 else (
            "feedback.thumb.down" if value == -1 else "feedback.thumb.neutral"
        )
        ev = self._build_event(
            agent_id=agent_id, event_type=et,
            data={"target_event_id": target_event_id,
                  "value": value, "comment": comment, "user_id": user_id},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_score(
        self, agent_id: str, target_event_id: str, score: float,
        scale_max: float = 1.0, label: Optional[str] = None,
        evaluator: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="feedback.score.recorded",
            data={"target_event_id": target_event_id,
                  "score": score, "scale_max": scale_max,
                  "label": label, "evaluator": evaluator},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_edit(
        self, agent_id: str, target_event_id: str,
        original_preview: str, edited_preview: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="feedback.edit.applied",
            data={"target_event_id": target_event_id,
                  "original_preview": original_preview[:300],
                  "edited_preview": edited_preview[:300],
                  "user_id": user_id},
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)

    def log_escalation(
        self, agent_id: str, target_event_id: str, reason: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> EventHandle:
        ev = self._build_event(
            agent_id=agent_id, event_type="feedback.escalation.requested",
            data={"target_event_id": target_event_id,
                  "reason": reason, "user_id": user_id},
            severity="warn",
            correlation_id=correlation_id,
        )
        return self._log_and_return_handle(ev)
