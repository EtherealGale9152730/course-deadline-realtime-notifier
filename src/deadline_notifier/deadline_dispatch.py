from datetime import timedelta
from typing import Protocol

from .models import DeadlineRequest, NotificationResult


class Publisher(Protocol):
    def publish(
        self,
        *,
        channel: str,
        event: str,
        data: dict,
        account_id: str,
        idempotency_key: str,
    ) -> dict:
        """Publish one learner event."""


def dispatch_deadline(request: DeadlineRequest, publisher: Publisher) -> NotificationResult:
    channel = f"learner:{request.learner_id}"
    if request.completed:
        return NotificationResult(decision="skipped", reason="completed", channel=channel)

    remaining = request.due_at - request.observed_at
    if remaining > timedelta(hours=24):
        return NotificationResult(decision="skipped", reason="outside_window", channel=channel)

    reason = "overdue" if remaining.total_seconds() < 0 else "due_soon"
    event = "course.deadline"
    operation_id = f"deadline:{request.course_id}:{request.learner_id}:{request.due_at.isoformat()}"
    publisher.publish(
        channel=channel,
        event=event,
        data={
            "course_id": request.course_id,
            "course_title": request.course_title,
            "learner_id": request.learner_id,
            "due_at": request.due_at.isoformat(),
            "status": reason,
        },
        account_id=request.account_id,
        idempotency_key=f"{operation_id}:publish:{reason}",
    )
    return NotificationResult(decision="published", reason=reason, channel=channel, event=event)
