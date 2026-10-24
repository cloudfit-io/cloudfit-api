"""Request-size limit, so one oversized request cannot exhaust memory or CPU."""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BodySizeLimitMiddleware:
    """Reject request bodies larger than ``max_bytes`` with HTTP 413.

    Rejects an oversized declared ``Content-Length`` up front. Otherwise it
    reads the body itself, stopping as soon as it passes the limit, and hands
    the app a replay of what it read. That covers bodies streamed without a
    length (chunked transfer) too, and keeps memory bounded by the limit. It
    reads the body here rather than inside the app because the framework turns
    errors raised while it reads the body into a generic 400.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", []):
            if name == b"content-length" and value.isdigit() and int(value) > self.max_bytes:
                await self._reject(send)
                return

        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break  # client disconnected; let the app see that as usual
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.max_bytes:
                await self._reject(send)
                return
            chunks.append(chunk)
            if not message.get("more_body", False):
                break

        body = b"".join(chunks)
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

    async def _reject(self, send: Send) -> None:
        payload = json.dumps(
            {"detail": f"Request body exceeds the {self.max_bytes}-byte limit."}
        ).encode()
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json"),
                        (b"content-length", str(len(payload)).encode())],
        })
        await send({"type": "http.response.body", "body": payload})
