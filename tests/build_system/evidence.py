"""Associate validation outcomes with the exact implementation and test inputs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .support import ROOT


def source_fingerprint(root: Path = ROOT) -> dict:
    files = [
        root / name
        for name in (
            "CMakeLists.txt",
            "CMakePresets.json",
            "pyproject.toml",
            "agent/build/EXTENDING.md",
            "thirdLib/googletest.provenance.json",
        )
    ]
    for directory in ("cmake", "tool", "tests/build_system", "source", "thirdLib/googletest"):
        files.extend(
            path
            for path in (root / directory).rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        )
    digest = hashlib.sha256()
    count = 0
    for path in sorted(set(files), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        count += 1
    return {"algorithm": "sha256-path-and-content", "files": count, "digest": digest.hexdigest()}
