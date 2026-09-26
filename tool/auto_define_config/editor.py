"""Headless editing transactions reused by the GUI and regression tests."""

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import Declaration, validate_declarations, validate_value
from .errors import ConfigError
from .inventory import Inventory
from .rules import validate_rules
from .preview import validate_module_rules
from .sync import Synchronizer
from tool.build_support.storage import fingerprint, json_text, read_json, replace_checked
from tool.build_support.process import check_cancelled

DEFAULT_RULES = {"schema_version": 1, "aliases": {}, "groups": []}


@dataclass
class Document:
    path: Path
    data: dict
    revision: str | None

    @classmethod
    def open(cls, path: Path, default: dict | None = None) -> Document:
        before = fingerprint(path)
        data = read_json(path) if before is not None else copy.deepcopy(default)
        if not isinstance(data, dict):
            raise ConfigError(f"Expected a JSON object: {path}")
        if fingerprint(path) != before:
            raise ConfigError(f"Document changed while loading: {path}")
        return cls(path, data, before)

    def save(self, data: dict) -> None:
        replace_checked(self.path, json_text(data), expected=self.revision)
        self.data = copy.deepcopy(data)
        self.revision = fingerprint(self.path)


class ProjectEditor:
    def __init__(self, inventory: Inventory, *, cmake: str = "cmake"):
        self.inventory = inventory
        self.cmake = cmake
        self.sync = Synchronizer(inventory)

    def rules(self, module: str) -> Document:
        if module not in {item.path for item in self.inventory.modules}:
            raise ConfigError(f"Unknown module: {module}")
        document = Document.open(
            self.inventory.root / "source" / module / "source_rules.json", DEFAULT_RULES
        )
        validate_rules(document.data)
        return document

    def fields(self, module: str) -> Document:
        owner = next(
            (item for item in self.inventory.modules if item.path == module and item.is_define),
            None,
        )
        if owner is None:
            raise ConfigError(f"Not a registered define module: {module}")
        path = self.sync.root / owner.probe_relative / "fields.json"
        document = Document.open(path)
        Declaration.from_data(document.data, module=module)
        return document

    def catalogue(self) -> dict[str, dict]:
        return {
            field.id: {
                "type": field.type,
                "unit": field.unit,
                "description": field.description,
                "kind": field.kind,
                "default": field.default,
            }
            for declaration in self.sync.declarations()
            for field in declaration.fields
        }

    def save_fields(
        self, document: Document, data: dict, *, cancel: threading.Event | None = None
    ) -> None:
        check_cancelled(cancel)
        module = document.data["module"]
        new = Declaration.from_data(data, module=module)
        others = tuple(item for item in self.sync.declarations() if item.module != module)
        declarations = (*others, new)
        validate_declarations(declarations)
        for owner in self.inventory.modules:
            validate_module_rules(
                self.inventory, owner.path, declarations, cmake=self.cmake, cancel=cancel
            )
        check_cancelled(cancel)
        document.save(data)

    def save_rules(
        self, document: Document, data: dict, *, cancel: threading.Event | None = None
    ) -> None:
        check_cancelled(cancel)
        validate_rules(data)
        module = document.path.parent.relative_to(self.inventory.root / "source").as_posix()
        validate_module_rules(
            self.inventory,
            module,
            self.sync.declarations(),
            rules_override=data,
            cmake=self.cmake,
            cancel=cancel,
        )
        check_cancelled(cancel)
        document.save(data)

    def save_options(self, document: Document, data: dict) -> None:
        options = {
            field.id: field
            for declaration in self.sync.declarations()
            for field in declaration.fields
            if field.kind == "option"
        }
        if not isinstance(data, dict) or data.keys() - options.keys():
            raise ConfigError("Only declared configurable options can be saved")
        for name, value in data.items():
            validate_value(options[name].type, value, name)
        document.save(data)

    def options(self) -> Document:
        return Document.open(self.inventory.root / "cache/auto_define_config/options.json", {})

    def sources(self, module: str) -> tuple[str, ...]:
        directory = self.inventory.root / "source" / module
        return tuple(
            sorted(
                path.relative_to(directory).as_posix()
                for path in (directory / "src").rglob("*.cpp")
            )
        )
