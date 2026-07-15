"""Deterministic hashing utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 digest for a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    """Hash a JSON-serialisable object using sorted keys."""

    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_directory_files(directory: str | Path, pattern: str = "*") -> dict[str, str]:
    """Hash regular files in deterministic name order."""

    base = Path(directory)
    return {
        str(path.relative_to(base)): sha256_file(path)
        for path in sorted(base.glob(pattern))
        if path.is_file()
    }
