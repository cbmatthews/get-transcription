"""The one interface every transcription provider implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from prism.config import Settings
from prism.models import Segment


@dataclass(frozen=True)
class TranscriptionOptions:
    # None = auto-detect (spec: any language, auto-detected)
    language: str | None = None
    # Optional per-video speaker labels (diarization)
    speaker_labels: bool = False


@dataclass
class TranscriptionResult:
    segments: list[Segment]
    language: str | None
    audio_seconds: float
    # Goes into transcript.method on the job record, e.g. "azure-speech-fast"
    method: str
    model: str | None = None
    extra: dict = field(default_factory=dict)


class Transcriber(ABC):
    """Turns an audio file into timestamped segments.

    Input is a local audio file (the pipeline extracts/downloads audio first), so
    providers don't need to know whether it came from an upload or YouTube.
    """

    name: str

    def __init__(self, settings: Settings):
        self.settings = settings

    @abstractmethod
    def transcribe(
        self, audio_path: Path, options: TranscriptionOptions
    ) -> TranscriptionResult: ...
