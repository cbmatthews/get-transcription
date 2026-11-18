from prism.ids import is_ulid, new_ulid


def test_ulid_format():
    value = new_ulid()
    assert len(value) == 26
    assert is_ulid(value)


def test_ulid_known_vector():
    assert new_ulid(0, bytes(10)) == "0" * 26
    assert new_ulid(2**48 - 1, b"\xff" * 10) == "7" + "Z" * 25


def test_ulids_sort_by_time():
    earlier = new_ulid(1_700_000_000_000)
    later = new_ulid(1_700_000_000_001)
    assert earlier < later
