"""Read the module registry evaluated by CMake, without a second parser."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import threading
import tempfile
from typing import Any

from .errors import ConfigError
from tool.build_support.storage import read_json
from tool.build_support.process import run_command, check_cancelled

ENGINE_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = re.compile(r"[A-Za-z][A-Za-z0-9_-]*(/[A-Za-z][A-Za-z0-9_-]*)*\Z")
STANDARDS = (98, 11, 14, 17, 20, 23, 26)


@dataclass(frozen=True)
class Module:
    path: str
    kind: str
    cxx_standard: int
    public_cxx_standard: int
    effective_cxx_standard: int
    effective_public_cxx_standard: int

    @property
    def is_define(self) -> bool:
        return PurePosixPath(self.path).parts[0] == "define"

    @property
    def probe_relative(self) -> str:
        parts = PurePosixPath(self.path).parts[1:]
        return PurePosixPath(*parts).as_posix() if parts else "."


@dataclass(frozen=True)
class Inventory:
    root: Path
    modules: tuple[Module, ...]
    layers: tuple[str, ...]

    @classmethod
    def from_data(cls, data: Any, *, root: Path) -> Inventory:
        if (
            not isinstance(data, dict)
            or type(data.get("schema_version")) is not int
            or data["schema_version"] != 1
        ):
            raise ConfigError("Inventory requires schema_version 1")
        if not isinstance(data.get("root"), str) or Path(data["root"]).resolve() != root.resolve():
            raise ConfigError("Inventory belongs to a different project root")
        layers = data.get("layers")
        if not isinstance(layers, list) or not all(isinstance(x, str) for x in layers):
            raise ConfigError("Inventory layers must be a string array")
        entries = data.get("modules")
        if not isinstance(entries, list):
            raise ConfigError("Inventory modules must be an array")
        modules = []
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ConfigError("Inventory module must be an object")
            path = entry.get("path")
            if not isinstance(path, str) or not MODULE_PATH.fullmatch(path) or path in seen:
                raise ConfigError(f"Invalid or duplicate module path: {path}")
            if path.split("/")[0] not in layers:
                raise ConfigError(f"Module uses an unregistered layer: {path}")
            seen.add(path)
            kind = entry.get("kind")
            if kind not in ("AUTO", "STATIC", "INTERFACE"):
                raise ConfigError(f"Invalid module kind for {path}: {kind}")
            numbers = []
            for name in (
                "cxx_standard",
                "public_cxx_standard",
                "effective_cxx_standard",
                "effective_public_cxx_standard",
            ):
                value = entry.get(name)
                if str(value) not in {str(s) for s in STANDARDS}:
                    raise ConfigError(f"Invalid {name} in module {path}")
                numbers.append(int(value))
            modules.append(Module(path, kind, *numbers))
        return cls(root.resolve(), tuple(modules), tuple(layers))


def load_inventory(
    root: Path,
    *,
    manifest: Path | None = None,
    cmake: str = "cmake",
    cancel: threading.Event | None = None,
) -> Inventory:
    check_cancelled(cancel)
    root = root.resolve()
    if not root.is_dir():
        raise ConfigError(f"Project root does not exist: {root}")
    if manifest is not None:
        return Inventory.from_data(read_json(manifest), root=root)
    with tempfile.TemporaryDirectory(prefix="destiny-inventory-") as directory:
        output = Path(directory) / "modules.json"
        command = [
            cmake,
            f"-DDESTINY_ROOT={root.as_posix()}",
            f"-DDESTINY_OUTPUT={output.as_posix()}",
            "-P",
            str(ENGINE_ROOT / "cmake" / "scripts" / "Inventory.cmake"),
        ]
        result = run_command(command, cwd=root, timeout=30, cancel=cancel)
        if result.returncode:
            raise ConfigError(f"CMake module registration failed:\n{result.stdout}{result.stderr}")
        return Inventory.from_data(read_json(output), root=root)
