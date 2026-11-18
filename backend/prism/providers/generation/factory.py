from __future__ import annotations

from prism.config import Settings
from prism.providers.generation.base import Generator
from prism.providers.registry import load_provider

# Register new providers here; select one with PRISM_GENERATION_PROVIDER.
PROVIDERS: dict[str, str] = {
    "fake": "prism.providers.generation.fake:FakeGenerator",
    # M3: "azure-openai": "prism.providers.generation.azure_openai:AzureOpenAIGenerator",
}


def get_generator(settings: Settings) -> Generator:
    return load_provider("generation", settings.generation_provider, PROVIDERS, settings)
