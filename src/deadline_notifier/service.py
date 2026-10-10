from fastapi import FastAPI, HTTPException

from .deadline_dispatch import dispatch_deadline
from .infrai_realtime import InfraiError, InfraiTransportError, RealtimePublisher
from .models import DeadlineRequest, NotificationResult

app = FastAPI(title="Course deadline notifier")


@app.post("/deadlines/notify", response_model=NotificationResult)
def notify_deadline(request: DeadlineRequest) -> NotificationResult:
    try:
        return dispatch_deadline(request, RealtimePublisher())
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
    except InfraiTransportError as exc:
        raise HTTPException(status_code=502, detail="upstream transport response unavailable") from exc


def run() -> None:
    import uvicorn

    uvicorn.run("deadline_notifier.service:app", host="127.0.0.1", port=8000)
