"""The Functions app indexes, and every HTTP handler enforces the owner role."""

import json

import function_app
from prism.api.health import health
from prism.api.me import me
from prism.auth import PRINCIPAL_HEADER
from tests.conftest import make_request, principal_header


def _user_fn(f):
    # Blueprint decorators may wrap the function in a builder; get the original callable.
    builder_fn = getattr(f, "_function", None)
    return builder_fn.get_user_function() if builder_fn else f


def test_app_registers_expected_functions():
    names = {fn.get_function_name() for fn in function_app.app.get_functions()}
    assert {
        "me",
        "health",
        "health_durable_start",
        "health_durable_status",
        "health_ping_orchestrator",
        "health_ping_activity",
    } <= names


def test_me_returns_principal():
    resp = _user_fn(me)(make_request(headers={PRINCIPAL_HEADER: principal_header()}))
    assert resp.status_code == 200
    assert json.loads(resp.get_body())["ownerId"] == "user-123"


def test_me_and_health_reject_signed_out():
    assert _user_fn(me)(make_request()).status_code == 401
    assert _user_fn(health)(make_request(url="/api/health")).status_code == 401


def test_me_rejects_non_owner():
    headers = {PRINCIPAL_HEADER: principal_header(roles=("authenticated",))}
    resp = _user_fn(me)(make_request(headers=headers))
    assert resp.status_code == 403
    assert json.loads(resp.get_body())["error"]["code"] == "forbidden"
