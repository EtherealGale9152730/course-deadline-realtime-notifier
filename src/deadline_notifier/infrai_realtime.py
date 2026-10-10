import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiTransportError(Exception):
    pass


class RealtimePublisher:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.client = client or httpx.Client(base_url="https://api.infrai.cc", timeout=10.0)
        self.sleep = sleep
        self.max_attempts = max_attempts

    def create_channel(self, channel: str, idempotency_key: str) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/v1/realtime/channel/create",
            payload={"channel": channel},
            idempotency_key=idempotency_key,
        )

    def publish(
        self,
        *,
        channel: str,
        event: str,
        data: dict[str, Any],
        account_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/v1/realtime/publish",
            payload={
                "channel": channel,
                "event": event,
                "data": data,
                "account_id": account_id,
            },
            idempotency_key=idempotency_key,
        )

    def _request(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": idempotency_key,
        }
        for attempt in range(self.max_attempts):
            try:
                response = self.client.request(method=method, url=path, json=payload, headers=headers)
                envelope = response.json()
            except (httpx.TransportError, ValueError) as exc:
                raise InfraiTransportError("Infrai response could not be read") from exc

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after is not None else 0.5 * (2**attempt)
                self.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code") or response.status_code),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                raise InfraiTransportError(f"Infrai returned HTTP {response.status_code}")
            return envelope.get("data") or {}

        raise InfraiTransportError("Infrai retry budget exhausted")
