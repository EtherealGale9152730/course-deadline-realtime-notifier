from datetime import datetime, timedelta, timezone

from deadline_notifier.deadline_dispatch import dispatch_deadline
from deadline_notifier.models import DeadlineRequest


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish(self, **request: object) -> dict:
        self.events.append(request)
        return {}


def deadline_request(**changes: object) -> DeadlineRequest:
    observed_at = datetime(2026, 9, 4, 8, tzinfo=timezone.utc)
    values = {
        "course_id": "course-42",
        "course_title": "Distributed Systems",
        "learner_id": "learner-7",
        "account_id": "school-3",
        "due_at": observed_at + timedelta(hours=6),
        "observed_at": observed_at,
    }
    values.update(changes)
    return DeadlineRequest.model_validate(values)


def test_publishes_due_soon_deadline_to_learner_channel() -> None:
    publisher = RecordingPublisher()

    result = dispatch_deadline(deadline_request(), publisher)

    assert result.model_dump() == {
        "decision": "published",
        "reason": "due_soon",
        "channel": "learner:learner-7",
        "event": "course.deadline",
    }
    assert publisher.events[0]["data"]["course_title"] == "Distributed Systems"
    assert publisher.events[0]["account_id"] == "school-3"
    assert publisher.events[0]["idempotency_key"].endswith(":publish:due_soon")


def test_skips_completed_course_without_publishing() -> None:
    publisher = RecordingPublisher()

    result = dispatch_deadline(deadline_request(completed=True), publisher)

    assert result.decision == "skipped"
    assert result.reason == "completed"
    assert publisher.events == []
