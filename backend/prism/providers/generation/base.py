"""The one interface every text-generation provider implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from prism.config import Settings


@dataclass(frozen=True)
class GenerationRequest:
    system: str
    prompt: str
    max_output_tokens: int = 2000
    temperature: float = 0.2


@dataclass
class GenerationResult:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class Generator(ABC):
    """Turns a system + user prompt into text. Prompts live outside providers
    (versioned as summary-v1, plan-v1, ...), so swapping models doesn't touch them."""

    name: str

    def __init__(self, settings: Settings):
        self.settings = settings

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult: ...
