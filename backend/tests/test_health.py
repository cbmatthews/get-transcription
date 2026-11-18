import dataclasses

from prism import health
from tests.conftest import FakeBlobService


def test_health_ok_with_storage_and_no_vault_locally(settings, monkeypatch):
    service = FakeBlobService()
    monkeypatch.setattr(health, "get_blob_service", lambda s: service)
    local = dataclasses.replace(settings, env="local")

    result = health.run_health(local)

    assert result["status"] == "ok", result
    assert result["checks"]["storage"]["ok"]
    # Probe blob is cleaned up
    assert service.containers["jobs"].blobs == {}
    assert result["checks"]["providers"]["detail"] == "transcription=fake, generation=fake"


def test_health_degraded_when_container_missing(settings, monkeypatch):
    monkeypatch.setattr(health, "get_blob_service", lambda s: FakeBlobService(("uploads", "jobs")))
    result = health.run_health(settings)
    assert result["status"] == "degraded"
    assert "audio" in result["checks"]["storage"]["detail"]


def test_health_creates_missing_containers_locally(settings, monkeypatch):
    service = FakeBlobService(("jobs",))
    monkeypatch.setattr(health, "get_blob_service", lambda s: service)
    result = health.run_health(dataclasses.replace(settings, env="local"))
    assert result["checks"]["storage"]["ok"], result
    assert set(service.containers) == {"uploads", "audio", "jobs"}


def test_health_reports_exceptions_instead_of_raising(settings, monkeypatch):
    def boom(_):
        raise RuntimeError("no network")

    monkeypatch.setattr(health, "get_blob_service", boom)
    result = health.run_health(settings)
    assert result["checks"]["storage"] == {"ok": False, "detail": "RuntimeError: no network"}


def test_key_vault_required_outside_local(settings):
    azure = dataclasses.replace(settings, env="azure")
    assert health.check_key_vault(azure).ok is False


def test_key_vault_reads_canary(settings, monkeypatch):
    class Secret:
        value = "ok"

    class Client:
        def get_secret(self, name):
            assert name == "prism-healthcheck"
            return Secret()

    monkeypatch.setattr(health, "get_secret_client", lambda s: Client())
    assert health.check_key_vault(settings).ok
