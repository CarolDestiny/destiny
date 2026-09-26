from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
from typing import Any, Iterable

from tool.build_support.errors import BuildError


@dataclass(frozen=True)
class Candidate:
    c: Path
    cxx: Path


@dataclass(frozen=True)
class Toolchain:
    c: str
    cxx: str
    family: str
    version: str
    architecture: str
    host: str
    target: str
    flags: tuple[str, ...]
    status: str
    phase: str = ""
    reason: str = ""
    compiler_fingerprint: str = ""

    @property
    def identity(self) -> str:
        text = "|".join(
            (
                self.host,
                self.c,
                self.cxx,
                self.family,
                self.version,
                self.architecture,
                self.target,
                self.compiler_fingerprint,
                *self.flags,
            )
        )
        return hashlib.sha256(text.encode()).hexdigest()[:10]

    def to_data(self) -> dict:
        return asdict(self)

    @classmethod
    def from_data(cls, data: Any) -> Toolchain:
        if isinstance(data, dict):
            data = dict(data)
            data.setdefault("compiler_fingerprint", "")
        if not isinstance(data, dict) or set(data) != set(cls.__dataclass_fields__):
            raise BuildError("Invalid saved compiler result")
        if data["family"] not in ("gcc", "clang", "unknown") or data["architecture"] not in (
            "x86",
            "x64",
        ):
            raise BuildError("Invalid compiler family or target architecture")
        if (
            data["status"] not in ("available", "unavailable")
            or not isinstance(data["flags"], list)
            or not all(isinstance(x, str) for x in data["flags"])
        ):
            raise BuildError("Invalid compiler result status or flags")
        if not all(isinstance(v, str) for k, v in data.items() if k != "flags"):
            raise BuildError("Compiler result members must be strings")
        return cls(**dict(data, flags=tuple(data["flags"])))


def combination_summary(
    results: Iterable[Toolchain], *, scan_complete: bool = False
) -> list[dict[str, str]]:
    """Distinguish an untested combination from an unsuccessful observation."""
    results = tuple(results)
    summary = []
    for family in ("gcc", "clang"):
        for architecture in ("x86", "x64"):
            candidates = [
                item
                for item in results
                if item.family == family and item.architecture == architecture
            ]
            if any(item.status == "available" for item in candidates):
                status = "available"
            elif candidates:
                status = "unavailable"
            else:
                status = "not-found" if scan_complete else "unchecked"
            summary.append({"family": family, "architecture": architecture, "status": status})
    return summary
