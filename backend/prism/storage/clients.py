"""Azure SDK clients, authenticated with managed identity in Azure.

Locally, PRISM_STORAGE_CONNECTION_STRING (Azurite) takes precedence, and
DefaultAzureCredential falls back to your `az login` session for Key Vault.
"""

from __future__ import annotations

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

from prism.config import Settings
from prism.errors import ConfigError


@lru_cache(maxsize=1)
def get_credential() -> DefaultAzureCredential:
    # In Azure, AZURE_CLIENT_ID selects the Function App's user-assigned identity.
    return DefaultAzureCredential()


@lru_cache(maxsize=4)
def get_blob_service(settings: Settings) -> BlobServiceClient:
    if settings.storage_connection_string:
        return BlobServiceClient.from_connection_string(settings.storage_connection_string)
    if settings.blob_endpoint:
        return BlobServiceClient(settings.blob_endpoint, credential=get_credential())
    raise ConfigError(
        "Storage isn't configured: set PRISM_STORAGE_ACCOUNT_NAME or "
        "PRISM_STORAGE_CONNECTION_STRING."
    )


@lru_cache(maxsize=4)
def get_secret_client(settings: Settings) -> SecretClient | None:
    if not settings.key_vault_uri:
        return None
    return SecretClient(vault_url=settings.key_vault_uri, credential=get_credential())
