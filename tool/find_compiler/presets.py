"""Generate only tool-owned CMake user presets; preserve all unrelated content."""

from __future__ import annotations

import copy
from pathlib import Path
import shutil
import sys
import threading
from typing import Any, Iterable

from tool.build_support.errors import BuildError
from tool.build_support.compiler import compiler_fingerprint
from tool.build_support.process import compiler_environment, check_cancelled
from tool.build_support.storage import fingerprint, json_text, read_json, replace_checked
from .model import Toolchain

OWNER = "destiny-compat/find_compiler"


def _ownership(preset: dict) -> dict | None:
    vendor = preset.get("vendor", {})
    return vendor.get(OWNER) if isinstance(vendor, dict) else None


def merge_presets(
    existing: Any, toolchains: Iterable[Toolchain], *, python: Path, ninja: Path
) -> dict:
    if (
        not isinstance(existing, dict)
        or type(existing.get("version")) is not int
        or not 6 <= existing["version"] <= 6
    ):
        raise BuildError(
            "User presets must use supported schema version 6; incompatible files are not rewritten"
        )
    result = copy.deepcopy(existing)
    additions = {key: [] for key in ("configurePresets", "buildPresets", "testPresets")}
    for toolchain in toolchains:
        if toolchain.status != "available" or toolchain.family not in ("gcc", "clang"):
            raise BuildError(
                "Only successfully validated GCC/Clang combinations can produce presets"
            )
        host = {"windows": "Windows", "linux": "Linux", "darwin": "Darwin"}.get(toolchain.host)
        if not host:
            raise BuildError(f"Unsupported preset host: {toolchain.host}")
        base = f'local-{toolchain.host}-{toolchain.family}{toolchain.version.split(".")[0]}-{toolchain.architecture}-{toolchain.identity}'
        environment = compiler_environment(Path(toolchain.cxx))
        env = {"PATH": environment["PATH"], "LC_ALL": "C"}
        for key in (
            "CC",
            "CXX",
            "CFLAGS",
            "CXXFLAGS",
            "CPPFLAGS",
            "LDFLAGS",
            "CPATH",
            "C_INCLUDE_PATH",
            "CPLUS_INCLUDE_PATH",
            "LIBRARY_PATH",
            "GCC_EXEC_PREFIX",
            "COMPILER_PATH",
        ):
            env[key] = None
        metadata = {
            OWNER: {"schema_version": 1, "identity": toolchain.identity, "host": toolchain.host}
        }
        for configuration in ("Debug", "Release"):
            name = f"{base}-{configuration.lower()}"
            cache = {
                "CMAKE_C_COMPILER": Path(toolchain.c).as_posix(),
                "CMAKE_CXX_COMPILER": Path(toolchain.cxx).as_posix(),
                "CMAKE_BUILD_TYPE": configuration,
                "CMAKE_MAKE_PROGRAM": ninja.as_posix(),
                "Python3_EXECUTABLE": python.as_posix(),
                "CMAKE_C_FLAGS_INIT": " ".join(toolchain.flags),
                "CMAKE_CXX_FLAGS_INIT": " ".join(toolchain.flags),
            }
            additions["configurePresets"].append(
                {
                    "name": name,
                    "displayName": f"{toolchain.family.upper()} {toolchain.version} {toolchain.architecture} {configuration}",
                    "inherits": "destiny-base",
                    "binaryDir": f"${{sourceDir}}/build/{base}/{configuration.lower()}",
                    "cacheVariables": cache,
                    "environment": env,
                    "condition": {"type": "equals", "lhs": "${hostSystemName}", "rhs": host},
                    "vendor": metadata,
                }
            )
            additions["buildPresets"].append(
                {"name": name, "configurePreset": name, "vendor": metadata}
            )
            additions["testPresets"].append(
                {
                    "name": name,
                    "configurePreset": name,
                    "output": {"outputOnFailure": True},
                    "vendor": metadata,
                }
            )
    for key, new_entries in additions.items():
        entries = result.setdefault(key, [])
        if not isinstance(entries, list) or not all(
            isinstance(e, dict) and isinstance(e.get("name"), str) for e in entries
        ):
            raise BuildError(f"{key} must be an array of named presets")
        names = [entry["name"] for entry in entries]
        if len(names) != len(set(names)):
            raise BuildError(f"Duplicate preset name in {key}")
        index = {entry["name"]: i for i, entry in enumerate(entries)}
        for entry in new_entries:
            position = index.get(entry["name"])
            if position is None:
                index[entry["name"]] = len(entries)
                entries.append(entry)
            else:
                if _ownership(entries[position]) != _ownership(entry):
                    raise BuildError(
                        f'Preset name is not owned by this tool/identity: {entry["name"]}'
                    )
                entries[position] = entry
    return result


def write_presets(
    project: Path,
    toolchains: Iterable[Toolchain],
    *,
    python: Path | None = None,
    ninja: Path | None = None,
    cancel: threading.Event | None = None,
) -> Path:
    toolchains = tuple(toolchains)
    for toolchain in toolchains:
        if toolchain.status != "available":
            raise BuildError("Only successfully validated combinations can produce presets")
        if not toolchain.compiler_fingerprint:
            raise BuildError(
                "Saved compiler result has no executable fingerprint; validate it again"
            )
        current = compiler_fingerprint((Path(toolchain.c), Path(toolchain.cxx)), cancel)
        if current != toolchain.compiler_fingerprint:
            raise BuildError(
                f"Compiler executables changed since validation: {toolchain.cxx}; validate again"
            )
    project = project.resolve()
    shared = project / "CMakePresets.json"
    if not shared.is_file():
        raise BuildError(f"Missing shared CMake presets: {shared}")
    shared_data = read_json(shared)
    if not any(
        item.get("name") == "destiny-base" for item in shared_data.get("configurePresets", [])
    ):
        raise BuildError("Shared presets do not declare destiny-base")
    executable = ninja or (Path(found) if (found := shutil.which("ninja")) else None)
    if executable is None or not executable.is_file():
        raise BuildError("Ninja must be installed or supplied explicitly")
    destination = project / "CMakeUserPresets.json"
    before = fingerprint(destination)
    existing = read_json(destination) if destination.exists() else {"version": 6}
    merged = merge_presets(
        existing,
        toolchains,
        python=(python or Path(sys.executable)).resolve(),
        ninja=executable.resolve(),
    )
    check_cancelled(cancel)
    replace_checked(destination, json_text(merged), expected=before)
    return destination
