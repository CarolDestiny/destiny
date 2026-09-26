"""JSON validation and guarded writes shared by CLI and GUI services."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .errors import BuildError


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BuildError(f"Duplicate JSON member: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda value: _invalid_constant(value),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BuildError(f"Cannot read JSON {path}: {exc}") from exc


def _invalid_constant(value: str) -> None:
    raise BuildError(f"Non-finite JSON number: {value}")


def json_text(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n"


def fingerprint(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def contained_path(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise BuildError(f"Path escapes its managed root: {path}")
    return path


def create_missing(path: Path, content: str) -> bool:
    """Publish a complete new file exclusively; never expose a partial skeleton."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    staged = Path(temporary)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(staged, path)
        except FileExistsError:
            return False
        return True
    finally:
        staged.unlink(missing_ok=True)


def replace_checked(path: Path, content: str, *, expected: str | None) -> bool:
    """Save a previously inspected text file; unchanged content keeps its mtime."""
    if fingerprint(path) != expected:
        raise BuildError(f"File changed outside this operation: {path}")
    encoded = content.encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    staged = Path(temporary)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if fingerprint(path) != expected:
            raise BuildError(f"File changed before save: {path}")
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)
    return True
