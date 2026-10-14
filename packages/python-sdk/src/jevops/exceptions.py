from __future__ import annotations


class JevOpsError(Exception):
    """Base exception for JevOps SDK."""


class JevOpsAPIError(JevOpsError):
    """API returned an error response."""

    def __init__(self, status_code: int, message: str, error_code: str | None = None) -> None:
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        super().__init__(f"[{status_code}] {message}")


class ReviewTimeoutError(JevOpsError):
    """Timed out waiting for a human review decision."""

    def __init__(self, decision_id: str, timeout_seconds: float) -> None:
        self.decision_id = decision_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Review timeout after {timeout_seconds}s for decision {decision_id}")
