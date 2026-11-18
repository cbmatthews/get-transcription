"""Runtime configuration, read once from environment variables (app settings)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    env: str
    # Storage: account name (Azure, managed identity) or connection string (local Azurite)
    storage_account_name: str | None
    storage_connection_string: str | None
    key_vault_uri: str | None
    # Provider names; see prism/providers/*/factory.py for the registered values
    transcription_provider: str
    generation_provider: str
    uploads_container: str = "uploads"
    audio_container: str = "audio"
    jobs_container: str = "jobs"

    @property
    def blob_endpoint(self) -> str | None:
        if self.storage_account_name:
            return f"https://{self.storage_account_name}.blob.core.windows.net"
        return None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        e = os.environ if environ is None else environ

        def get(name: str, default: str | None = None) -> str | None:
            value = e.get(name, default)
            return value.strip() if value and value.strip() else default

        return cls(
            env=get("PRISM_ENV", "local") or "local",
            storage_account_name=get("PRISM_STORAGE_ACCOUNT_NAME"),
            storage_connection_string=get("PRISM_STORAGE_CONNECTION_STRING"),
            key_vault_uri=get("PRISM_KEY_VAULT_URI"),
            transcription_provider=get("PRISM_TRANSCRIPTION_PROVIDER", "fake") or "fake",
            generation_provider=get("PRISM_GENERATION_PROVIDER", "fake") or "fake",
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
