"""Reads and writes job records in the `jobs` container at {ownerId}/{jobId}.json."""

from __future__ import annotations

import re

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import ContainerClient, ContentSettings

from prism.errors import ValidationError
from prism.models import JobRecord, utcnow

_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_JSON = ContentSettings(content_type="application/json; charset=utf-8")


def _check_segment(value: str, label: str) -> str:
    if not _SAFE_SEGMENT.match(value):
        raise ValidationError(f"Invalid {label}.")
    return value


def job_blob_name(owner_id: str, job_id: str) -> str:
    return f"{_check_segment(owner_id, 'owner id')}/{_check_segment(job_id, 'job id')}.json"


class JobStore:
    def __init__(self, container: ContainerClient):
        self._container = container

    def save(self, job: JobRecord) -> JobRecord:
        job.updated_at = utcnow()
        self._container.upload_blob(
            job_blob_name(job.owner_id, job.job_id),
            job.to_json().encode("utf-8"),
            overwrite=True,
            content_settings=_JSON,
        )
        return job

    def get(self, owner_id: str, job_id: str) -> JobRecord | None:
        blob = self._container.get_blob_client(job_blob_name(owner_id, job_id))
        try:
            data = blob.download_blob().readall()
        except ResourceNotFoundError:
            return None
        return JobRecord.from_json(data)
