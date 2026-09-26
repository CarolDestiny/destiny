"""Resolve and stage only the selected executable's MinGW runtime dependencies."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

from .errors import BuildError
from .pe import read_pe


@dataclass(frozen=True)
class DependencySet:
    architecture: str
    files: dict[str, Path]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_roots(
    compiler: Path, architecture: str, additional: tuple[Path, ...] = ()
) -> tuple[tuple[Path, ...], ...]:
    compiler = compiler.resolve()
    target = {"x86": "i686", "x64": "x86_64"}.get(architecture)
    if target is None:
        raise BuildError(f"Runtime staging does not support target architecture {architecture}")
    # Target runtimes are authoritative; driver-bin copies are only a fallback.
    # Explicit extra roots are an equal-priority pool, not arbitrary first-match wins.
    tiers = [
        (compiler.parent.parent / f"{target}-w64-mingw32" / "bin",),
        (compiler.parent,),
        additional,
    ]
    return tuple(
        tuple(dict.fromkeys(path.resolve() for path in tier if path.is_dir())) for tier in tiers
    )


def windows_system_roots(architecture: str) -> tuple[Path, ...]:
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    if architecture == "x86" and (windows / "SysWOW64").is_dir():
        return (windows / "SysWOW64",)
    # Sysnative avoids WOW64 filesystem redirection when this helper is 32-bit.
    native = windows / "Sysnative"
    return (native if native.is_dir() else windows / "System32",)


def resolve_dependencies(
    executable: Path, tiers: tuple[tuple[Path, ...], ...], *, system_roots: tuple[Path, ...]
) -> DependencySet:
    image = read_pe(executable)
    catalogs = []
    for tier in tiers:
        catalog: dict[str, list[Path]] = {}
        for root in tier:
            for path in root.iterdir():
                if path.is_file() and path.suffix.lower() == ".dll":
                    catalog.setdefault(path.name.lower(), []).append(path.resolve())
        catalogs.append(catalog)
    system = {
        p.name.lower()
        for folder in system_roots
        if folder.is_dir()
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() == ".dll"
    }
    queue = list(image.imports)
    selected: dict[str, Path] = {}
    visited = set()
    while queue:
        name = queue.pop(0)
        if name in visited:
            continue
        visited.add(name)
        if name.startswith(("api-ms-win-", "ext-ms-win-")) or name in system:
            continue
        compatible = []
        incompatible = []
        for catalog in catalogs:
            for candidate in dict.fromkeys(catalog.get(name, [])):
                dependency = read_pe(candidate)
                if dependency.architecture == image.architecture:
                    compatible.append((candidate, dependency))
                else:
                    incompatible.append(str(candidate))
            if compatible:
                break
        if not compatible:
            detail = f"; incompatible candidates: {', '.join(incompatible)}" if incompatible else ""
            raise BuildError(
                f"Missing {image.architecture} runtime dependency {name} for {executable}{detail}"
            )
        hashes = {_hash(path) for path, _ in compatible}
        if len(hashes) != 1:
            raise BuildError(
                f"Conflicting equal-priority runtime candidates for {name}: "
                + ", ".join(str(path) for path, _ in compatible)
            )
        path, dependency = compatible[0]
        selected[name] = path
        queue.extend(dependency.imports)
    return DependencySet(image.architecture, selected)


@contextmanager
def _directory_lock(directory: Path):
    lock = directory / ".destiny-runtime.lock"
    deadline = time.monotonic() + 30
    while True:
        try:
            handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise BuildError(f"Runtime staging lock is busy or stale: {lock}")
            time.sleep(0.05)
    try:
        with os.fdopen(handle, "w") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def _publish(path: Path, data: bytes) -> None:
    handle, temporary = tempfile.mkstemp(prefix=".destiny-runtime-", dir=path.parent)
    staged = Path(temporary)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def _receipts(directory: Path) -> dict[Path, dict]:
    result = {}
    for path in directory.glob(".destiny-runtime-*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["schema_version"] != 1 or not isinstance(data["files"], dict):
                raise ValueError("invalid receipt")
            for name, digest in data["files"].items():
                if (
                    Path(name).name != name
                    or not name.endswith(".dll")
                    or not isinstance(digest, str)
                ):
                    raise ValueError("invalid receipt file")
            result[path] = data
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise BuildError(f"Invalid runtime staging receipt {path}: {exc}") from exc
    return result


def stage_runtime(
    executable: Path,
    compiler: Path,
    build_root: Path,
    *,
    additional: tuple[Path, ...] = (),
    system_roots: tuple[Path, ...] | None = None,
) -> DependencySet:
    executable, build_root = executable.resolve(), build_root.resolve()
    if not executable.is_file() or not executable.is_relative_to(build_root):
        raise BuildError(f"Executable must exist inside the managed build root: {executable}")
    architecture = read_pe(executable).architecture
    roots = runtime_roots(compiler, architecture, additional)
    dependencies = resolve_dependencies(
        executable,
        roots,
        system_roots=(windows_system_roots(architecture) if system_roots is None else system_roots),
    )
    directory = executable.parent
    receipt = directory / f".destiny-runtime-{executable.name}.json"
    with _directory_lock(directory):
        existing = _receipts(directory)
        previous = existing.get(receipt, {"files": {}})["files"]
        others = {
            name: digest
            for owner, data in existing.items()
            if owner != receipt
            for name, digest in data["files"].items()
        }
        desired = {name: _hash(source) for name, source in dependencies.files.items()}
        for name, digest in desired.items():
            destination = directory / name
            if destination.is_symlink():
                raise BuildError(f"Refusing to overwrite a runtime symlink: {destination}")
            if name in others and others[name] != digest:
                raise BuildError(
                    f"Programs in this directory require conflicting runtime versions: {name}"
                )
            if destination.exists() and _hash(destination) != digest:
                if previous.get(name) != _hash(destination):
                    raise BuildError(
                        f"Runtime destination was not created by this tool or was modified: {destination}"
                    )
        for name, source in dependencies.files.items():
            destination = directory / name
            if not destination.exists() or _hash(destination) != desired[name]:
                _publish(destination, source.read_bytes())
        for name, digest in previous.items():
            old = directory / name
            if (
                name not in desired
                and name not in others
                and old.is_file()
                and not old.is_symlink()
                and _hash(old) == digest
            ):
                old.unlink()
        metadata = {
            "schema_version": 1,
            "executable": executable.name,
            "architecture": architecture,
            "files": desired,
        }
        content = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
        if not receipt.exists() or receipt.read_bytes() != content:
            _publish(receipt, content)
    return dependencies


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage verified MinGW runtime DLLs beside a built executable"
    )
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--build-root", type=Path, required=True)
    parser.add_argument("--runtime-dir", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        result = stage_runtime(
            args.executable, args.compiler, args.build_root, additional=tuple(args.runtime_dir)
        )
        print(
            f"Runtime dependencies [{args.executable.name}]: {len(result.files)} verified {result.architecture} DLLs"
        )
        return 0
    except (BuildError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
