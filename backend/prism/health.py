"""Foundation checks: can the Function App's identity reach Storage and Key Vault,
and do the configured providers resolve? Used by GET /api/health."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from prism.config import Settings
from prism.models import utcnow
from prism.providers.generation import get_generator
from prism.providers.transcription import get_transcriber
from prism.storage.clients import get_blob_service, get_secret_client

log = logging.getLogger(__name__)

HEALTH_SECRET_NAME = "prism-healthcheck"
PROBE_BLOB = "_health/probe.json"
_BUILD_INFO = Path(__file__).resolve().parent.parent / "build_info.json"


@dataclass
class Check:
    ok: bool
    detail: str


def _run(name: str, fn) -> Check:
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 — a failed check is reported, not raised
        log.warning("Health check %s failed: %s", name, e)
        return Check(False, f"{type(e).__name__}: {str(e).splitlines()[0][:200]}")


def check_storage(settings: Settings) -> Check:
    service = get_blob_service(settings)
    missing = []
    for name in (settings.uploads_container, settings.audio_container, settings.jobs_container):
        container = service.get_container_client(name)
        if container.exists():
            continue
        if settings.env == "local":
            # Azurite starts empty; in Azure the containers come from Bicep.
            container.create_container()
        else:
            missing.append(name)
    if missing:
        return Check(False, f"Missing containers: {', '.join(missing)}")

    # Round-trip a small blob in the jobs container, the same path job records use.
    blob = service.get_blob_client(settings.jobs_container, PROBE_BLOB)
    payload = json.dumps({"probe": True, "at": utcnow().isoformat()}).encode()
    blob.upload_blob(payload, overwrite=True)
    if blob.download_blob().readall() != payload:
        return Check(False, "Probe blob read back different content")
    blob.delete_blob()
    return Check(True, "uploads, audio, jobs reachable; write/read/delete OK")


def check_key_vault(settings: Settings) -> Check:
    client = get_secret_client(settings)
    if client is None:
        return Check(settings.env == "local", "Not configured (PRISM_KEY_VAULT_URI empty)")
    value = client.get_secret(HEALTH_SECRET_NAME).value
    if value != "ok":
        return Check(False, f"Secret {HEALTH_SECRET_NAME} has unexpected value")
    return Check(True, f"Read secret {HEALTH_SECRET_NAME}")


def check_providers(settings: Settings) -> Check:
    t = get_transcriber(settings)
    g = get_generator(settings)
    return Check(True, f"transcription={t.name}, generation={g.name}")


@lru_cache(maxsize=1)
def build_info() -> dict[str, Any]:
    try:
        return json.loads(_BUILD_INFO.read_text())
    except (OSError, ValueError):
        return {"version": "dev"}


def run_health(settings: Settings) -> dict[str, Any]:
    checks = {
        "storage": _run("storage", lambda: check_storage(settings)),
        "keyVault": _run("keyVault", lambda: check_key_vault(settings)),
        "providers": _run("providers", lambda: check_providers(settings)),
    }
    return {
        "status": "ok" if all(c.ok for c in checks.values()) else "degraded",
        "env": settings.env,
        "build": build_info(),
        "checks": {k: asdict(v) for k, v in checks.items()},
    }
