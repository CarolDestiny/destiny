from __future__ import annotations

import argparse
from pathlib import Path
import sys

from tool.build_support.errors import BuildError
from tool.build_support.storage import fingerprint, json_text, read_json, replace_checked
from .discovery import discover
from .model import Candidate, Toolchain, combination_summary
from .presets import write_presets
from .validation import validate


def _report(results: list[Toolchain], *, scan_complete: bool = False) -> dict:
    return {
        "schema_version": 1,
        "combinations": combination_summary(results, scan_complete=scan_complete),
        "candidates": [dict(t.to_data(), identity=t.identity) for t in results],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="find_compiler")
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser(
        "scan", help="Discover and compile-link-run validate local compiler pairs"
    )
    scan.add_argument("--root", type=Path, action="append", default=[])
    scan.add_argument("--no-defaults", action="store_true")
    scan.add_argument("--output", type=Path)
    inspect = commands.add_parser("validate", help="Validate a manually specified compiler pair")
    inspect.add_argument("--c", type=Path, required=True)
    inspect.add_argument("--cxx", type=Path, required=True)
    inspect.add_argument("--arch", choices=("x86", "x64"), required=True)
    inspect.add_argument("--output", type=Path)
    presets = commands.add_parser(
        "write-presets", help="Revalidate selected results and merge local user presets"
    )
    presets.add_argument("--input", type=Path, required=True)
    presets.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    presets.add_argument(
        "--select",
        action="append",
        default=[],
        help="Candidate identity; omit to export all available candidates",
    )
    gui = commands.add_parser("gui", help="Open the compiler discovery interface")
    gui.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        if args.command == "gui":
            from .gui import launch

            launch(args.project)
            return 0
        if args.command == "write-presets":
            data = read_json(args.input)
            if (
                not isinstance(data, dict)
                or data.get("schema_version") != 1
                or not isinstance(data.get("candidates"), list)
            ):
                raise BuildError("Expected compiler scan report schema_version 1")
            chosen = []
            seen = set()
            for entry in data["candidates"]:
                original = dict(entry)
                identity = original.pop("identity", None)
                item = Toolchain.from_data(original)
                if identity != item.identity:
                    raise BuildError(
                        "Saved compiler identity is inconsistent; scan or validate again"
                    )
                if args.select and identity not in args.select:
                    continue
                seen.add(identity)
                if item.status == "available":
                    if not item.compiler_fingerprint:
                        raise BuildError(
                            "Saved compiler report has no executable fingerprint; scan or validate again"
                        )
                    current = validate(Candidate(Path(item.c), Path(item.cxx)), item.architecture)
                    if current.status != "available" or current.identity != item.identity:
                        raise BuildError(
                            f"Compiler changed or is no longer available: {item.cxx}: {current.reason}"
                        )
                    chosen.append(current)
            if set(args.select) - seen or not chosen:
                raise BuildError(
                    "No valid selected compiler results, or an unknown selection was requested"
                )
            destination = write_presets(args.project, chosen)
            print(f"Wrote {destination}")
            return 0
        before = fingerprint(args.output) if args.output else None
        if args.command == "validate":
            results = [validate(Candidate(args.c, args.cxx), args.arch)]
        else:
            results = []
            for candidate in discover(args.root, include_defaults=not args.no_defaults):
                for architecture in ("x86", "x64"):
                    item = validate(candidate, architecture)
                    print(
                        f"{item.family} {architecture}: {item.status} ({candidate.cxx})",
                        file=sys.stderr,
                    )
                    results.append(item)
        text = json_text(_report(results, scan_complete=args.command == "scan"))
        if args.output:
            replace_checked(args.output, text, expected=before)
        else:
            print(text, end="")
        return 0 if any(item.status == "available" for item in results) else 1
    except (BuildError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
