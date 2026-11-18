import json

import pytest

from prism.errors import ValidationError
from prism.models import JobRecord, Source
from prism.storage.job_store import JobStore, job_blob_name
from tests.conftest import FakeContainer


def test_saves_at_owner_job_path():
    container = FakeContainer()
    store = JobStore(container)
    job = store.save(JobRecord.new("owner1", Source(type="upload", file_name="a.mp4")))

    name = f"owner1/{job.job_id}.json"
    assert list(container.blobs) == [name]
    assert json.loads(container.blobs[name])["source"]["fileName"] == "a.mp4"
    assert job.updated_at is not None


def test_get_round_trip_and_missing():
    store = JobStore(FakeContainer())
    job = store.save(JobRecord.new("owner1", Source(type="upload")))
    assert store.get("owner1", job.job_id) == job
    assert store.get("owner1", "01JD0000000000000000000000") is None


@pytest.mark.parametrize("owner,job", [("../x", "a"), ("a", "b/c"), ("", "a")])
def test_rejects_unsafe_path_segments(owner, job):
    with pytest.raises(ValidationError):
        job_blob_name(owner, job)
