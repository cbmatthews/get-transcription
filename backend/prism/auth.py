"""Identity forwarded by Azure Static Web Apps.

SWA authenticates the user and passes a base64-encoded JSON principal to the
linked backend in the ``x-ms-client-principal`` header. The Function App only
accepts traffic from the SWA (configured when the backend is linked), so the
header can be trusted. We still enforce the ``owner`` role here so the API stays
locked even if a route rule in staticwebapp.config.json is loosened by mistake.
"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass

import azure.functions as func

from prism.errors import ForbiddenError, UnauthorizedError

PRINCIPAL_HEADER = "x-ms-client-principal"
OWNER_ROLE = "owner"


@dataclass(frozen=True)
class ClientPrincipal:
    identity_provider: str
    user_id: str
    user_details: str
    user_roles: tuple[str, ...]

    @property
    def is_owner(self) -> bool:
        return OWNER_ROLE in self.user_roles

    def to_dict(self) -> dict:
        return {
            "identityProvider": self.identity_provider,
            "userId": self.user_id,
            "userDetails": self.user_details,
            "userRoles": list(self.user_roles),
        }


def parse_client_principal(header_value: str | None) -> ClientPrincipal | None:
    """Decode the SWA principal header. Returns None if missing or malformed."""
    if not header_value:
        return None
    try:
        padded = header_value + "=" * (-len(header_value) % 4)
        data = json.loads(base64.b64decode(padded).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None

    user_id = data.get("userId")
    if not isinstance(user_id, str) or not user_id:
        return None
    roles = data.get("userRoles") or []
    if not isinstance(roles, list):
        roles = []

    return ClientPrincipal(
        identity_provider=str(data.get("identityProvider") or ""),
        user_id=user_id,
        user_details=str(data.get("userDetails") or ""),
        user_roles=tuple(str(r) for r in roles),
    )


def require_owner(req: func.HttpRequest) -> ClientPrincipal:
    """Return the caller's principal, or raise if they aren't signed in as owner."""
    principal = parse_client_principal(req.headers.get(PRINCIPAL_HEADER))
    if principal is None:
        raise UnauthorizedError("Sign in to use Prism.")
    if not principal.is_owner:
        raise ForbiddenError("This account isn't allowed to use Prism.")
    return principal
