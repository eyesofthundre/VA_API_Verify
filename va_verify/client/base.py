"""Shared HTTP session logic for VA API clients."""

from __future__ import annotations
import requests
from requests import Response


class VAAPIError(Exception):
    """Raised when the VA API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str, body: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body or {}

    def __str__(self) -> str:
        return f"HTTP {self.status_code}: {super().__str__()}"


def _raise_for_status(resp: Response) -> None:
    """Convert non-2xx responses into VAAPIError with useful context."""
    if resp.ok:
        return
    try:
        body = resp.json()
        message = (
            body.get("message")
            or body.get("error")
            or body.get("errors", [{}])[0].get("detail", resp.text)
        )
    except Exception:
        body = {}
        message = resp.text or resp.reason

    raise VAAPIError(resp.status_code, message, body)


def build_session(extra_headers: dict | None = None) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    if extra_headers:
        session.headers.update(extra_headers)
    return session
