"""Job record: one JSON document per run, stored at jobs/{ownerId}/{jobId}.json.

Shape follows the Data model section of docs/spec.md. Additions beyond the spec
(all optional, so records stay forward compatible):
  - schemaVersion: lets V2 code recognise older records without migrations
  - updatedAt, error: needed to report progress and failures
  - source.fileName / source.blobPath: where an uploaded file lives
  - segment.speaker: for the optional speaker-label toggle

Unknown fields are preserved on read/write (extra="allow"), so a newer record
read by older code doesn't lose data.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from prism.ids import new_ulid

SCHEMA_VERSION = 1

JobStatus = Literal["queued", "running", "done", "failed"]
SourceType = Literal["youtube", "upload"]


def utcnow() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")


class Source(CamelModel):
    type: SourceType
    url: str | None = None
    title: str | None = None
    duration_sec: float | None = None
    file_name: str | None = None
    blob_path: str | None = None


class Segment(CamelModel):
    start: float
    end: float
    text: str
    speaker: str | None = None


class Transcript(CamelModel):
    # "captions" for YouTube captions; otherwise the transcription provider name
    method: str
    language: str | None = None
    segments: list[Segment] = Field(default_factory=list)


class Output(CamelModel):
    # "summary" | "actionPlan" in V1; "retool", "repurpose", ... later
    type: str
    options: dict[str, Any] = Field(default_factory=dict)
    prompt_version: str
    model: str | None = None
    markdown: str
    created_at: datetime = Field(default_factory=utcnow)


class Usage(CamelModel):
    audio_minutes: float = 0
    input_tokens: int = 0
    output_tokens: int = 0


class JobError(CamelModel):
    code: str
    message: str


class JobRecord(CamelModel):
    schema_version: int = SCHEMA_VERSION
    job_id: str
    owner_id: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime | None = None
    status: JobStatus = "queued"
    source: Source
    transcript: Transcript | None = None
    outputs: list[Output] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    error: JobError | None = None

    @classmethod
    def new(cls, owner_id: str, source: Source) -> JobRecord:
        now = utcnow()
        return cls(
            job_id=new_ulid(), owner_id=owner_id, created_at=now, updated_at=now, source=source
        )

    def to_json(self) -> str:
        return self.model_dump_json(by_alias=True, indent=2)

    @classmethod
    def from_json(cls, data: str | bytes) -> JobRecord:
        return cls.model_validate_json(data)
