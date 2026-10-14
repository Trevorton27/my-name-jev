from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class JevOpsHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code: str | None = None) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


async def jevops_exception_handler(request: Request, exc: JevOpsHTTPException) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "message": exc.detail,
            "status": exc.status_code,
        }
    }
    if exc.error_code:
        body["error"]["code"] = exc.error_code
    return JSONResponse(status_code=exc.status_code, content=body)
