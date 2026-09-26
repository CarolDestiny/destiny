"""Run the approved native acceptance scenario; not a replacement build launcher."""

from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time

from .scenario import prepare_scenario
from .support import ROOT, Workspace
from .evidence import source_fingerprint
from tool.build_support.compiler import executable_architecture
from tool.build_support.errors import BuildError
from tool.build_support.process import compiler_environment, run_command
from tool.build_support.storage import fingerprint, json_text, read_json, replace_checked
from tool.find_compiler.model import Candidate, Toolchain
from tool.find_compiler.validation import validate


def _candidates(report: Path | None) -> list[Toolchain]:
    if report:
        data = read_json(report)
        entries = []
        for item in data["candidates"]:
            item = dict(item)
            item.pop("identity", None)
            entries.append(Toolchain.from_data(item))
    else:
        entries = []
        for family, c, cxx in [("gcc", "gcc", "g++"), ("clang", "clang", "clang++")]:
            cc, cxx_path = shutil.which(c), shutil.which(cxx)
            if cc and cxx_path:
                entries.extend(
                    validate(Candidate(Path(cc), Path(cxx_path)), architecture)
                    for architecture in ("x86", "x64")
                )
    selected = []
    host = platform.system().lower()
    for family in ("gcc", "clang"):
        for architecture in ("x86", "x64"):
            choices = [
                item
                for item in entries
                if item.host == host
                and item.family == family
                and item.architecture == architecture
                and item.status == "available"
            ]
            choices.sort(
                key=lambda item: (
                    len(item.flags),
                    Path(item.cxx).name.lower() not in ("g++", "clang++", "g++.exe", "clang++.exe"),
                    len(item.cxx),
                    item.cxx,
                )
            )
            if not choices:
                raise BuildError(f"No validated {host} {family} {architecture} toolchain")
            current = validate(Candidate(Path(choices[0].c), Path(choices[0].cxx)), architecture)
            if current.status != "available":
                raise BuildError(current.reason)
            selected.append(current)
    return selected


def run_profile(toolchain: Toolchain, configuration: str, logs: Path) -> dict:
    label = f"{toolchain.host}-{toolchain.family}-{toolchain.architecture}-{configuration.lower()}"
    print(f"BEGIN {label}", flush=True)
    w = Workspace(framework=True)
    started = time.monotonic()
    log = []
    try:
        prepare_scenario(w)
        output = w.root / "out"
        env = compiler_environment(Path(toolchain.cxx))
        flags = " ".join(toolchain.flags)

        def command(args, *, runtime=False):
            environment = env.copy()
            if runtime and os.name == "nt":
                environment["PATH"] = str(
                    Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
                )
            result = run_command(
                args, cwd=w.root, env=environment, timeout=180, output_limit=8 * 1024 * 1024
            )
            log.append("$ " + " ".join(map(str, args)) + "\n" + result.stdout + result.stderr)
            if result.returncode:
                raise BuildError(
                    f"{label}: command returned {result.returncode}\n{result.stdout}{result.stderr}"
                )
            return result

        command(
            [
                "cmake",
                "-S",
                w.root,
                "-B",
                output,
                "-G",
                "Ninja",
                f"-DCMAKE_BUILD_TYPE={configuration}",
                f"-DCMAKE_C_COMPILER={Path(toolchain.c).as_posix()}",
                f"-DCMAKE_CXX_COMPILER={Path(toolchain.cxx).as_posix()}",
                f"-DCMAKE_C_FLAGS={flags}",
                f"-DCMAKE_CXX_FLAGS={flags}",
                f"-DPython3_EXECUTABLE={Path(sys.executable).as_posix()}",
            ]
        )
        command(["cmake", "--build", output, "--parallel", "4"])
        marker = w.root / "runtime-started.txt"
        if marker.exists():
            raise BuildError("Build executed a project test or its discovery")
        report = read_json(output / f"reports/source-selection-{configuration}.json")
        facts = read_json(output / "generated/facts.json")
        for module, fields in facts["modules"].items():
            if any(f["status"] != "available" for f in fields.values()):
                raise BuildError(f"Unexpected unavailable real provider in {module}")
        binaries = [Path(item["executable"]) for item in report["programs"]]
        for binary in binaries:
            if executable_architecture(binary) != toolchain.architecture:
                raise BuildError("Executable architecture mismatch")
        command(["ctest", "--test-dir", output, "--output-on-failure"], runtime=True)
        if not marker.exists() or not all(
            Path(line).resolve() == w.root.resolve() for line in marker.read_text().splitlines()
        ):
            raise BuildError("CTest discovery/execution did not use the project source root")
        for program in report["programs"]:
            if program["category"] in ("demo", "bench"):
                command([program["executable"]], runtime=True)
        headers = {str(p): p.stat().st_mtime_ns for p in (output / "generated").rglob("*.hpp")}
        objects = {
            str(p): p.stat().st_mtime_ns for p in output.rglob("*") if p.suffix in (".o", ".obj")
        }
        second = command(["cmake", "--build", output, "--parallel", "4"])
        if "Configuring done" in second.stdout:
            raise BuildError("Unchanged build unexpectedly reconfigured")
        if any(Path(p).stat().st_mtime_ns != t for p, t in headers.items()):
            raise BuildError("Unchanged build rewrote generated headers")
        if any(Path(p).stat().st_mtime_ns != t for p, t in objects.items()):
            raise BuildError("Unchanged build recompiled native sources")
        return {
            "profile": label,
            "status": "passed",
            "seconds": round(time.monotonic() - started, 3),
            "toolchain": toolchain.to_data(),
            "selection": report,
            "facts": facts,
            "checks": [
                "compile-link",
                "architecture",
                "ctest-root",
                "build-does-not-run",
                "demo-run",
                "bench-run",
                "no-op-build",
            ],
        }
    except Exception as exc:
        return {
            "profile": label,
            "status": "failed",
            "seconds": round(time.monotonic() - started, 3),
            "reason": str(exc),
            "toolchain": toolchain.to_data(),
        }
    finally:
        logs.mkdir(parents=True, exist_ok=True)
        (logs / f"{label}.log").write_text("\n".join(log), encoding="utf-8")
        w.close()
        print(f"END {label}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler-report", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--family", choices=("gcc", "clang"))
    parser.add_argument("--arch", choices=("x86", "x64"))
    parser.add_argument("--config", choices=("Debug", "Release"))
    args = parser.parse_args()
    try:
        before = source_fingerprint()
        chains = _candidates(args.compiler_report)
        chains = [
            c
            for c in chains
            if (not args.family or c.family == args.family)
            and (not args.arch or c.architecture == args.arch)
        ]
        data = {
            "schema_version": 1,
            "date": datetime.date.today().isoformat(),
            "host": platform.system(),
            "profiles": [],
            "source_before": before,
        }
        revision = fingerprint(args.report)
        for toolchain in chains:
            for configuration in [args.config] if args.config else ["Debug", "Release"]:
                result = run_profile(
                    toolchain, configuration, args.report.parent / (args.report.stem + "-logs")
                )
                data["profiles"].append(result)
                replace_checked(args.report, json_text(data), expected=revision)
                revision = fingerprint(args.report)
                print(result["profile"] + ": " + result["status"], flush=True)
        after = source_fingerprint()
        data["source_after"] = after
        data["source_unchanged"] = before == after
        replace_checked(args.report, json_text(data), expected=revision)
        return (
            0
            if data["source_unchanged"]
            and all(item["status"] == "passed" for item in data["profiles"])
            else 1
        )
    except (BuildError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
