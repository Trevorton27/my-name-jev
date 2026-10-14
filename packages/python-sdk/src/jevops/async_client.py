from __future__ import annotations

from typing import Any

import httpx

from jevops.exceptions import JevOpsAPIError, JevOpsError
from jevops.models import DecisionResponse, EvaluateRequest, OutcomeRequest, ReviewResponse
from jevops.retry import RetryConfig, async_retry


class AsyncJevOpsClient:
    """Asynchronous JevOps client."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "",
        timeout: float = 30.0,
        retry: RetryConfig | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.retry = retry or RetryConfig()
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"X-API-Key": api_key},
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self.retry.max_retries + 1):
            try:
                resp = await self._client.request(method, path, **kwargs)
                if resp.status_code in self.retry.retryable_status_codes and attempt < self.retry.max_retries:
                    await async_retry(self.retry, attempt)
                    continue
                if resp.status_code >= 400:
                    body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    error = body.get("error", {}) if isinstance(body, dict) else {}
                    raise JevOpsAPIError(
                        status_code=resp.status_code,
                        message=error.get("message", resp.text),
                        error_code=error.get("code"),
                    )
                return resp
            except httpx.HTTPError as e:
                last_exc = e
                if attempt < self.retry.max_retries:
                    await async_retry(self.retry, attempt)
                    continue
        raise JevOpsError(f"Request failed after {self.retry.max_retries + 1} attempts") from last_exc

    async def evaluate(self, request: EvaluateRequest | dict[str, Any]) -> DecisionResponse:
        if isinstance(request, dict):
            request = EvaluateRequest(**request)
        resp = await self._request("POST", "/v1/decisions/evaluate", json=request.model_dump())
        return DecisionResponse(**resp.json())

    async def get_decision(self, decision_id: str) -> DecisionResponse:
        resp = await self._request("GET", f"/v1/decisions/{decision_id}")
        return DecisionResponse(**resp.json())

    async def record_outcome(self, decision_id: str, request: OutcomeRequest | dict[str, Any]) -> dict[str, Any]:
        if isinstance(request, dict):
            request = OutcomeRequest(**request)
        resp = await self._request("POST", f"/v1/decisions/{decision_id}/outcome", json=request.model_dump())
        return resp.json()

    async def list_reviews(self, status: str | None = None) -> list[ReviewResponse]:
        params = {}
        if status:
            params["status"] = status
        resp = await self._request("GET", "/v1/reviews", params=params)
        return [ReviewResponse(**r) for r in resp.json()]

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncJevOpsClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
