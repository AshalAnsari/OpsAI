from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def error_response(code: str, message: str, status_code: int = 400, details: dict[str, Any] | None = None) -> JSONResponse:
    body: dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.code, exc.message, exc.status_code, exc.details)
