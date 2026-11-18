from __future__ import annotations

import base64
import json

import azure.functions as func
import pytest
from azure.core.exceptions import ResourceNotFoundError

from prism.config import Settings


def principal_header(roles=("authenticated", "owner"), user_id="user-123") -> str:
    body = {
        "identityProvider": "aad",
        "userId": user_id,
        "userDetails": "me@example.com",
        "userRoles": list(roles),
    }
    return base64.b64encode(json.dumps(body).encode()).decode()


def make_request(url="/api/me", method="GET", headers=None, route_params=None):
    return func.HttpRequest(
        method=method, url=url, headers=headers or {}, body=b"", route_params=route_params or {}
    )


@pytest.fixture
def settings() -> Settings:
    return Settings(
        env="test",
        storage_account_name=None,
        storage_connection_string="UseDevelopmentStorage=true",
        key_vault_uri=None,
        transcription_provider="fake",
        generation_provider="fake",
    )


class _Download:
    def __init__(self, data: bytes):
        self._data = data

    def readall(self) -> bytes:
        return self._data


class FakeBlob:
    def __init__(self, store: dict, name: str):
        self._store, self._name = store, name

    def upload_blob(self, data, overwrite=False, **_):
        if self._name in self._store and not overwrite:
            raise ValueError("exists")
        self._store[self._name] = data if isinstance(data, bytes) else data.encode()

    def download_blob(self):
        if self._name not in self._store:
            raise ResourceNotFoundError("missing")
        return _Download(self._store[self._name])

    def delete_blob(self):
        self._store.pop(self._name, None)


class FakeContainer:
    """Just enough of azure.storage.blob.ContainerClient for unit tests."""

    def __init__(self):
        self.blobs: dict[str, bytes] = {}

    def exists(self) -> bool:
        return True

    def upload_blob(self, name, data, overwrite=False, **kwargs):
        FakeBlob(self.blobs, name).upload_blob(data, overwrite=overwrite, **kwargs)

    def get_blob_client(self, name):
        return FakeBlob(self.blobs, name)


class FakeBlobService:
    def __init__(self, containers=("uploads", "audio", "jobs")):
        self.containers = {c: FakeContainer() for c in containers}

    def get_container_client(self, name):
        return self.containers.get(name) or _MissingContainer(self, name)

    def get_blob_client(self, container, blob):
        return self.containers[container].get_blob_client(blob)


class _MissingContainer:
    def __init__(self, service: FakeBlobService, name: str):
        self._service, self._name = service, name

    def exists(self) -> bool:
        return False

    def create_container(self):
        self._service.containers[self._name] = FakeContainer()
