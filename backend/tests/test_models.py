import json

from prism.ids import is_ulid
from prism.models import JobRecord, Output, Segment, Source, Transcript


def _sample() -> JobRecord:
    job = JobRecord.new(
        "carlton",
        Source(type="youtube", url="https://youtube.com/watch?v=abc", title="T", duration_sec=2700),
    )
    job.status = "done"
    job.transcript = Transcript(
        method="captions", language="en", segments=[Segment(start=0.0, end=6.2, text="hi")]
    )
    job.outputs.append(
        Output(
            type="summary",
            options={"length": "standard"},
            prompt_version="summary-v1",
            model="m",
            markdown="# S",
        )
    )
    return job


def test_serializes_to_spec_shape():
    data = json.loads(_sample().to_json())
    # Top-level fields from the Data model section of docs/spec.md
    for key in [
        "jobId",
        "ownerId",
        "createdAt",
        "status",
        "source",
        "transcript",
        "outputs",
        "tags",
        "usage",
    ]:
        assert key in data, key
    assert is_ulid(data["jobId"])
    assert data["createdAt"].endswith("Z")
    assert data["source"]["durationSec"] == 2700
    assert data["transcript"]["segments"][0] == {
        "start": 0.0,
        "end": 6.2,
        "text": "hi",
        "speaker": None,
    }
    assert data["outputs"][0]["promptVersion"] == "summary-v1"
    assert data["usage"] == {"audioMinutes": 0, "inputTokens": 0, "outputTokens": 0}
    assert data["tags"] == []


def test_round_trip():
    job = _sample()
    assert JobRecord.from_json(job.to_json()) == job


def test_reads_spec_example_and_keeps_unknown_fields():
    raw = {
        "jobId": "01JD0000000000000000000000",
        "ownerId": "carlton",
        "createdAt": "2026-11-18T15:30:00Z",
        "status": "done",
        "source": {
            "type": "youtube",
            "url": "https://youtube.com/watch?v=x",
            "title": "...",
            "durationSec": 2700,
        },
        "transcript": {
            "method": "captions",
            "language": "en",
            "segments": [{"start": 0.0, "end": 6.2, "text": "..."}],
        },
        "outputs": [
            {
                "type": "actionPlan",
                "options": {"goal": "g", "days": 30},
                "promptVersion": "plan-v1",
                "markdown": "...",
            }
        ],
        "tags": [],
        "usage": {"audioMinutes": 0, "inputTokens": 0, "outputTokens": 0},
        "futureField": {"keep": True},
    }
    job = JobRecord.model_validate(raw)
    assert job.outputs[0].type == "actionPlan"
    assert json.loads(job.to_json())["futureField"] == {"keep": True}
