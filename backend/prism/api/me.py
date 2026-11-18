"""GET /api/me — confirms the signed-in identity reaches the backend."""

import azure.functions as func

from prism.auth import require_owner
from prism.http import error_response, json_response

bp = func.Blueprint()


@bp.route(route="me", methods=["GET"])
def me(req: func.HttpRequest) -> func.HttpResponse:
    try:
        principal = require_owner(req)
    except Exception as e:  # noqa: BLE001 — mapped to a friendly response
        return error_response(e)
    return json_response({"principal": principal.to_dict(), "ownerId": principal.user_id})
