"""Invoke the exact CMake selector used by native builds."""

from __future__ import annotations

from pathlib import Path
import tempfile
import threading

from .contracts import Declaration, Observation
from .errors import ConfigError
from .inventory import ENGINE_ROOT, Inventory
from .rules import load_rules, validate_rules
from tool.build_support.storage import read_json, json_text
from tool.build_support.process import run_command, check_cancelled


def preview_selection(
    inventory: Inventory,
    module: str,
    facts: Path,
    *,
    cmake: str = "cmake",
    rules_override: dict | None = None,
    validate_only: bool = False,
    cancel: threading.Event | None = None,
) -> dict:
    check_cancelled(cancel)
    if module not in {item.path for item in inventory.modules}:
        raise ConfigError(f"Unknown module for selection preview: {module}")
    module_root = inventory.root / "source" / module
    rules = module_root / "source_rules.json"
    if rules_override is None and rules.exists():
        load_rules(rules)
    data = read_json(facts)
    if (
        not isinstance(data, dict)
        or type(data.get("schema_version")) is not int
        or data["schema_version"] != 1
    ):
        raise ConfigError("Preview facts require schema_version 1")
    with tempfile.TemporaryDirectory(prefix="destiny-selection-") as directory:
        output = Path(directory) / "selection.json"
        command = [
            cmake,
            f"-DDESTINY_MODULE_ROOT={module_root.as_posix()}",
            f"-DDESTINY_FACTS={facts.resolve().as_posix()}",
            f"-DDESTINY_OUTPUT={output.as_posix()}",
            "-P",
            str(ENGINE_ROOT / "cmake/scripts/SelectSources.cmake"),
        ]
        if validate_only:
            command.insert(1, "-DDESTINY_VALIDATE_ONLY=ON")
        if rules_override is not None:
            validate_rules(rules_override)
            override = Path(directory) / "source_rules.json"
            override.write_text(json_text(rules_override), encoding="utf-8")
            command.insert(1, f"-DDESTINY_RULES_FILE={override.as_posix()}")
        try:
            result = run_command(command, cwd=inventory.root, timeout=30, cancel=cancel)
        except OSError as exc:
            raise ConfigError(f"Cannot run CMake selection preview: {exc}") from exc
        if result.returncode:
            raise ConfigError(f"CMake selection preview failed:\n{result.stdout}{result.stderr}")
        return read_json(output)


def preview_header(
    inventory: Inventory,
    module: str,
    facts: dict,
    *,
    cmake: str = "cmake",
    cancel: threading.Event | None = None,
) -> str:
    check_cancelled(cancel)
    if module not in {item.path for item in inventory.modules if item.is_define}:
        raise ConfigError(f"Header preview requires a registered define module: {module}")
    with tempfile.TemporaryDirectory(prefix="destiny-header-") as directory:
        scratch = Path(directory)
        document = scratch / "facts.json"
        document.write_text(json_text(facts), encoding="utf-8")
        output = scratch / "cmake_config.hpp"
        result = run_command(
            [
                cmake,
                f"-DDESTINY_MODULE={module}",
                f"-DDESTINY_FACTS={document.as_posix()}",
                f"-DDESTINY_OUTPUT={output.as_posix()}",
                "-P",
                ENGINE_ROOT / "cmake/scripts/PreviewHeader.cmake",
            ],
            cwd=inventory.root,
            timeout=30,
            cancel=cancel,
        )
        if result.returncode:
            raise ConfigError(f"CMake header preview failed: {result.stdout}{result.stderr}")
        return output.read_text(encoding="utf-8")


def validate_module_rules(
    inventory: Inventory,
    module: str,
    declarations: tuple[Declaration, ...],
    *,
    rules_override: dict | None = None,
    cmake: str = "cmake",
    cancel: threading.Event | None = None,
) -> None:
    """Validate rule structure and references without requiring host capability matches."""
    data = {"schema_version": 1, "modules": {}}
    for declaration in declarations:
        fields = {}
        for field in declaration.fields:
            observation = Observation.unavailable(
                "Declaration-only validation; hardware was not probed",
                status="unimplemented",
                provider="schema-validation",
            )
            fields[field.id] = observation.to_data(field)
        data["modules"][declaration.module] = fields
    with tempfile.TemporaryDirectory(prefix="destiny-rule-validation-") as directory:
        facts = Path(directory) / "declarations.json"
        facts.write_text(json_text(data), encoding="utf-8")
        preview_selection(
            inventory,
            module,
            facts,
            cmake=cmake,
            rules_override=rules_override,
            validate_only=True,
            cancel=cancel,
        )
