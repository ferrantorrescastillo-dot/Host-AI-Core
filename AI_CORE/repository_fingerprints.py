from __future__ import annotations

import hashlib
from pathlib import Path


def hash_file_content(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_repository(entries: list[tuple[str, str]]) -> str:
    """entries: lista de (relative_path_normalized, file_fingerprint)."""
    h = hashlib.sha256()
    for rel_path, fingerprint in sorted(entries, key=lambda x: x[0].lower()):
        h.update(rel_path.encode("utf-8", errors="replace"))
        h.update(b"|")
        h.update(fingerprint.encode("ascii", errors="replace"))
        h.update(b"\n")
    return h.hexdigest()
