from __future__ import annotations

from prism.config import Settings
from prism.providers.registry import load_provider
from prism.providers.transcription.base import Transcriber

# Register new providers here; select one with PRISM_TRANSCRIPTION_PROVIDER.
PROVIDERS: dict[str, str] = {
    "fake": "prism.providers.transcription.fake:FakeTranscriber",
    # M1: "azure-speech-fast": "prism.providers.transcription.azure_speech:AzureSpeechFast",
}


def get_transcriber(settings: Settings) -> Transcriber:
    return load_provider("transcription", settings.transcription_provider, PROVIDERS, settings)
