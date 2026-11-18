import dataclasses
from pathlib import Path

import pytest

from prism.errors import ConfigError
from prism.providers.generation import GenerationRequest, Generator, get_generator
from prism.providers.transcription import Transcriber, TranscriptionOptions, get_transcriber


def test_fake_transcriber_selected_by_config(settings):
    t = get_transcriber(settings)
    assert isinstance(t, Transcriber)
    result = t.transcribe(Path("unused.wav"), TranscriptionOptions(speaker_labels=True))
    assert result.method == "fake"
    assert result.segments[0].start == 0.0
    assert result.segments[0].speaker == "Speaker 1"


def test_fake_generator_selected_by_config(settings):
    g = get_generator(settings)
    assert isinstance(g, Generator)
    result = g.generate(GenerationRequest(system="s", prompt="Summarize this"))
    assert result.model == "fake"
    assert "Summarize this" in result.text


def test_unknown_provider_is_a_clear_config_error(settings):
    bad = dataclasses.replace(settings, transcription_provider="nope")
    with pytest.raises(ConfigError, match="Unknown transcription provider 'nope'"):
        get_transcriber(bad)
    bad = dataclasses.replace(settings, generation_provider="nope")
    with pytest.raises(ConfigError, match="Known providers: fake"):
        get_generator(bad)
