"""Headless operations and a lazily imported Tk configuration interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .errors import ConfigError
from .inventory import ENGINE_ROOT, load_inventory
from tool.build_support.storage import fingerprint, json_text, read_json, replace_checked
from .sync import Synchronizer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="auto_define_config")
    parser.add_argument("--root", type=Path, default=ENGINE_ROOT)
    parser.add_argument("--inventory", type=Path, help="Use an existing CMake module inventory")
    parser.add_argument("--cmake", default="cmake")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inventory", help="List modules from their CMake declarations")
    commands.add_parser("check", help="Validate counterpart files without writing")
    sync = commands.add_parser("sync", help="Create missing counterpart skeletons only")
    sync.add_argument("--dry-run", action="store_true")
    probe = commands.add_parser("probe", help="Collect validated module observations")
    probe.add_argument("--context", type=Path)
    probe.add_argument("--options", type=Path)
    probe.add_argument("--output", type=Path)
    probe.add_argument("--module")
    preview = commands.add_parser(
        "preview", help="Preview sources through the native CMake selector"
    )
    preview.add_argument("--module", required=True)
    preview.add_argument("--facts", type=Path, required=True)
    rename = commands.add_parser(
        "rename", help="Explicitly migrate one orphaned define counterpart"
    )
    rename.add_argument("old")
    rename.add_argument("new")
    rename.add_argument("--dry-run", action="store_true")
    commands.add_parser("gui", help="Open the project rule/probe configuration interface")
    args = parser.parse_args(argv)
    try:
        if args.command == "gui":
            from .gui import launch

            launch(args.root, cmake=args.cmake)
            return 0
        inventory = load_inventory(args.root, manifest=args.inventory, cmake=args.cmake)
        if args.command == "inventory":
            from dataclasses import asdict

            print(
                json_text(
                    {
                        "root": str(inventory.root),
                        "layers": inventory.layers,
                        "modules": [asdict(item) for item in inventory.modules],
                    }
                ),
                end="",
            )
            return 0
        if args.command == "preview":
            from .preview import preview_selection

            result = preview_selection(inventory, args.module, args.facts, cmake=args.cmake)
            print(
                json_text(
                    {
                        "mode": "preview",
                        "module": args.module,
                        "facts": str(args.facts.resolve()),
                        "selection": result,
                    }
                ),
                end="",
            )
            return 0
        if args.command == "probe":
            from .probes import collect_facts

            context = read_json(args.context) if args.context else {}
            options = read_json(args.options) if args.options else {}
            if not isinstance(context, dict) or not isinstance(options, dict):
                raise ConfigError("Context and options must be JSON objects")
            expected_output = fingerprint(args.output) if args.output else None
            result = collect_facts(inventory, target=context, options=options, module=args.module)
            content = json_text(result)
            if args.output:
                replace_checked(args.output, content, expected=expected_output)
            else:
                print(content, end="")
            return 0
        service = Synchronizer(inventory)
        if args.command == "rename":
            print(json_text(service.rename(args.old, args.new, dry_run=args.dry_run)), end="")
            return 0
        if args.command == "check":
            entries = service.check()
        elif args.dry_run:
            entries = service.inspect()
        else:
            entries = service.apply()
        print(json_text({"entries": [entry.to_data() for entry in entries]}), end="")
        return 0
    except (ConfigError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
