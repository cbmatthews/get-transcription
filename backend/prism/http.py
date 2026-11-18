"""Small helpers for JSON HTTP responses."""

from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func

from prism.errors import PrismError

log = logging.getLogger(__name__)

_JSON_HEADERS = {"Cache-Control": "no-store"}


def json_response(body: Any, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body, default=str),
        status_code=status_code,
        mimetype="application/json",
        headers=_JSON_HEADERS,
    )


def error_response(error: Exception) -> func.HttpResponse:
    """Turn an exception into a friendly JSON error. Unknown errors are logged, not leaked."""
    if isinstance(error, PrismError):
        return json_response(
            {"error": {"code": error.code, "message": error.message}}, error.status_code
        )
    log.exception("Unhandled error", exc_info=error)
    return json_response(
        {"error": {"code": "internal_error", "message": "Something went wrong. Please try again."}},
        500,
    )
