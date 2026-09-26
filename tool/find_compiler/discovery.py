"""Bounded filesystem discovery; identity is established by validation, not names."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import threading
from typing import Iterable

from .model import Candidate
from tool.build_support.process import check_cancelled

DRIVER = re.compile(
    r"(?P<prefix>.*?)(?P<driver>g\+\+|clang\+\+)(?P<version>-\d+(?:\.\d+)*)?(?P<suffix>\.exe)?$",
    re.I,
)
SKIP = {
    ".git",
    ".cache",
    "include",
    "share",
    "lib",
    "lib64",
    "libexec",
    "node_modules",
    "__pycache__",
}


def pair_for(cxx: Path) -> Candidate | None:
    match = DRIVER.fullmatch(cxx.name)
    if match is None:
        return None
    c_driver = "gcc" if match["driver"].lower() == "g++" else "clang"
    c_name = f"{match['prefix']}{c_driver}{match['version'] or ''}{match['suffix'] or ''}"
    c = cxx.with_name(c_name)
    if not c.is_file():
        return None
    # Keep driver basenames: symlink names may determine the driver's behavior.
    return Candidate(c.absolute(), cxx.absolute())


def _walk(root: Path, depth: int, cancel: threading.Event | None) -> Iterable[Path]:
    check_cancelled(cancel)
    if not root.is_dir():
        return
    pending = [(root, 0)]
    seen = set()
    while pending:
        check_cancelled(cancel)
        directory, level = pending.pop()
        resolved = directory.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            entries = []
            for item in directory.iterdir():
                check_cancelled(cancel)
                entries.append(item)
            entries.sort()
        except (OSError, PermissionError):
            continue
        for item in entries:
            check_cancelled(cancel)
            if item.is_file() and DRIVER.fullmatch(item.name):
                yield item
            elif (
                level < depth
                and item.is_dir()
                and not item.is_symlink()
                and item.name.lower() not in SKIP
            ):
                pending.append((item, level + 1))


def discover(
    roots: Iterable[Path] = (),
    *,
    include_defaults: bool = True,
    max_depth: int = 4,
    cancel: threading.Event | None = None,
) -> tuple[Candidate, ...]:
    check_cancelled(cancel)
    locations: dict[Path, int] = {Path(root).expanduser().absolute(): max_depth for root in roots}
    if include_defaults:
        for text in os.environ.get("PATH", "").split(os.pathsep):
            if text:
                locations.setdefault(Path(text), 0)
        for name in ("g++", "clang++"):
            location = shutil.which(name)
            if location and os.name == "nt":
                driver = Path(location)
                # Check sibling target installs, never elevate discovery to a drive root.
                ancestor = driver.parent.parent.parent
                if len(ancestor.parts) >= 3:
                    locations.setdefault(ancestor, 3)
        defaults = (
            (Path("C:/msys64"), Path("C:/mingw64"), Path("C:/Program Files/LLVM"))
            if os.name == "nt"
            else (Path("/usr/bin"), Path("/usr/local/bin"), Path("/opt/homebrew/bin"))
        )
        for root in defaults:
            locations.setdefault(root, 3 if os.name == "nt" else 0)
    candidates = {}
    for root, depth in locations.items():
        for cxx in _walk(root, depth, cancel):
            pair = pair_for(cxx)
            if pair is not None:
                key = (
                    (str(pair.c).casefold(), str(pair.cxx).casefold())
                    if os.name == "nt"
                    else (str(pair.c), str(pair.cxx))
                )
                candidates[key] = pair
    return tuple(candidates[key] for key in sorted(candidates))
