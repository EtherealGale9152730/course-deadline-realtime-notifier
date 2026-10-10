from datetime import datetime
from typing import Literal

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError as exc:
    if exc.name != "pydantic":
        raise
    from dataclasses import asdict, dataclass

    @dataclass
    class DeadlineRequest:
        course_id: str
        course_title: str
        learner_id: str
        account_id: str
        due_at: datetime
        observed_at: datetime
        completed: bool = False

        @classmethod
        def model_validate(cls, values: dict) -> "DeadlineRequest":
            values = values.copy()
            for name in ("course_id", "course_title", "learner_id", "account_id"):
                if not isinstance(values[name], str) or not values[name]:
                    raise ValueError(f"{name} must be a nonempty string")
            for name in ("due_at", "observed_at"):
                if isinstance(values[name], str):
                    values[name] = datetime.fromisoformat(values[name].replace("Z", "+00:00"))
                if not isinstance(values[name], datetime):
                    raise ValueError(f"{name} must be a datetime")
            return cls(**values)

    @dataclass
    class NotificationResult:
        decision: Literal["published", "skipped"]
        reason: Literal["overdue", "due_soon", "outside_window", "completed"]
        channel: str
        event: str | None = None

        def model_dump(self) -> dict:
            return asdict(self)

else:
    class DeadlineRequest(BaseModel):
        course_id: str = Field(min_length=1)
        course_title: str = Field(min_length=1)
        learner_id: str = Field(min_length=1)
        account_id: str = Field(min_length=1)
        due_at: datetime
        observed_at: datetime
        completed: bool = False


    class NotificationResult(BaseModel):
        decision: Literal["published", "skipped"]
        reason: Literal["overdue", "due_soon", "outside_window", "completed"]
        channel: str
        event: str | None = None
