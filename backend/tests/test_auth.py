import base64

import pytest

from prism.auth import PRINCIPAL_HEADER, parse_client_principal, require_owner
from prism.errors import ForbiddenError, UnauthorizedError
from tests.conftest import make_request, principal_header


def test_parses_swa_principal():
    p = parse_client_principal(principal_header())
    assert p is not None
    assert p.user_id == "user-123"
    assert p.identity_provider == "aad"
    assert p.user_details == "me@example.com"
    assert p.is_owner


def test_parses_unpadded_base64():
    header = principal_header().rstrip("=")
    assert parse_client_principal(header) is not None


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "not base64!!",
        base64.b64encode(b"[1,2]").decode(),
        base64.b64encode(b'{"userRoles": ["owner"]}').decode(),
    ],
)
def test_rejects_missing_or_malformed(value):
    assert parse_client_principal(value) is None


def test_require_owner_accepts_owner():
    req = make_request(headers={PRINCIPAL_HEADER: principal_header()})
    assert require_owner(req).user_id == "user-123"


def test_require_owner_401_when_signed_out():
    with pytest.raises(UnauthorizedError):
        require_owner(make_request())


def test_require_owner_403_without_role():
    req = make_request(headers={PRINCIPAL_HEADER: principal_header(roles=("authenticated",))})
    with pytest.raises(ForbiddenError):
        require_owner(req)
