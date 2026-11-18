"""ULID job IDs: 26 chars, Crockford base32, sortable by creation time."""

from __future__ import annotations

import os
import re
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def new_ulid(timestamp_ms: int | None = None, randomness: bytes | None = None) -> str:
    ts = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    if not 0 <= ts < 2**48:
        raise ValueError("timestamp out of range for ULID")
    rand = os.urandom(10) if randomness is None else randomness
    if len(rand) != 10:
        raise ValueError("ULID randomness must be 10 bytes")
    value = (ts << 80) | int.from_bytes(rand, "big")
    return "".join(_CROCKFORD[(value >> (5 * i)) & 0x1F] for i in reversed(range(26)))


def is_ulid(value: str) -> bool:
    return bool(ULID_RE.match(value))
