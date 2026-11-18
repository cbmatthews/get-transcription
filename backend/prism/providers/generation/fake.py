"""Deterministic stand-in used in M0, local dev and tests. Costs nothing."""

from __future__ import annotations

from prism.providers.generation.base import GenerationRequest, GenerationResult, Generator


class FakeGenerator(Generator):
    name = "fake"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        preview = request.prompt.strip().splitlines()[0][:80] if request.prompt.strip() else ""
        text = (
            f"## Fake output\n\n- Generated without calling a model.\n- Prompt began: {preview}\n"
        )
        return GenerationResult(
            text=text,
            model="fake",
            input_tokens=len(request.system.split()) + len(request.prompt.split()),
            output_tokens=len(text.split()),
        )
