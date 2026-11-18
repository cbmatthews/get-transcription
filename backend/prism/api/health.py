"""Foundation health endpoints.

GET  /api/health                      Storage, Key Vault and provider checks
POST /api/health/durable              Start a tiny Durable orchestration
GET  /api/health/durable/{instanceId} Poll it (expects output "pong")

The Durable round trip proves the task hub works on identity-based storage,
which every M1+ job depends on.
"""

import azure.durable_functions as df
import azure.functions as func

from prism.auth import require_owner
from prism.config import get_settings
from prism.health import run_health
from prism.http import error_response, json_response

bp = df.Blueprint()


@bp.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    try:
        require_owner(req)
        result = run_health(get_settings())
    except Exception as e:  # noqa: BLE001
        return error_response(e)
    return json_response(result, 200 if result["status"] == "ok" else 503)


@bp.route(route="health/durable", methods=["POST"])
@bp.durable_client_input(client_name="client")
async def health_durable_start(req: func.HttpRequest, client) -> func.HttpResponse:
    try:
        require_owner(req)
        instance_id = await client.start_new("health_ping_orchestrator", None, "ping")
    except Exception as e:  # noqa: BLE001
        return error_response(e)
    return json_response({"instanceId": instance_id}, 202)


@bp.route(route="health/durable/{instanceId}", methods=["GET"])
@bp.durable_client_input(client_name="client")
async def health_durable_status(req: func.HttpRequest, client) -> func.HttpResponse:
    try:
        require_owner(req)
        status = await client.get_status(req.route_params["instanceId"])
    except Exception as e:  # noqa: BLE001
        return error_response(e)
    if status is None or status.runtime_status is None:
        return json_response({"error": {"code": "not_found", "message": "No such run."}}, 404)
    return json_response(
        {
            "instanceId": status.instance_id,
            "runtimeStatus": status.runtime_status.name,
            "output": status.output,
        }
    )


@bp.orchestration_trigger(context_name="context")
def health_ping_orchestrator(context: df.DurableOrchestrationContext):
    message = context.get_input()
    result = yield context.call_activity("health_ping_activity", message)
    return result


@bp.activity_trigger(input_name="message")
def health_ping_activity(message: str) -> str:
    return "pong" if message == "ping" else f"unexpected: {message}"
