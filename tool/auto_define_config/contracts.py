"""Versioned field declarations and probe observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping

from .errors import ConfigError

IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)*\Z")
MACRO = re.compile(r"DESTINY_DEFINE_[A-Z][A-Z0-9_]*\Z")
STATUSES = frozenset(
    {"available", "unavailable", "denied", "unsupported", "unimplemented", "timeout"}
)


def require_members(data: Any, *, required: set[str], optional: set[str], label: str) -> dict:
    if not isinstance(data, dict):
        raise ConfigError(f"{label} must be an object")
    missing = required - data.keys()
    unknown = data.keys() - required - optional
    if missing or unknown:
        raise ConfigError(
            f"{label}: missing members {sorted(missing)}, unknown members {sorted(unknown)}"
        )
    return data


def validate_value(kind: str, value: Any, label: str) -> None:
    types = {"boolean": bool, "integer": int, "string": str}
    if kind not in types or type(value) is not types[kind]:
        raise ConfigError(f"{label} requires a {kind} value")
    if kind == "integer" and not -(2**63) <= value < 2**63:
        raise ConfigError(f"{label} exceeds the signed 64-bit integer range")
    if kind == "string" and any(ord(c) < 32 for c in value):
        raise ConfigError(f"{label} contains unsupported control characters")


@dataclass(frozen=True)
class Field:
    id: str
    type: str
    macro: str
    description: str
    unit: str | None = None
    alias: str | None = None
    kind: str = "observation"
    default: bool | int | str | None = None

    @classmethod
    def from_data(cls, data: Any) -> Field:
        require_members(
            data,
            required={"id", "type", "macro", "description"},
            optional={"unit", "alias", "kind", "default"},
            label="Field",
        )
        for key in ("id", "type", "macro", "description"):
            if not isinstance(data[key], str) or not data[key]:
                raise ConfigError(f"Field {key} must be a nonempty string")
        if not IDENTIFIER.fullmatch(data["id"]):
            raise ConfigError(f"Invalid field identifier: {data['id']}")
        if data["type"] not in ("boolean", "integer", "string"):
            raise ConfigError(f"Unsupported field type: {data['type']}")
        if not data["macro"].startswith("DESTINY_DEFINE_CMAKE_") or not MACRO.fullmatch(
            data["macro"]
        ):
            raise ConfigError(f"Invalid generated macro: {data['macro']}")
        alias = data.get("alias")
        if alias is not None and (
            not isinstance(alias, str)
            or not MACRO.fullmatch(alias)
            or alias.startswith("DESTINY_DEFINE_CMAKE_")
        ):
            raise ConfigError(f"Invalid public macro alias: {alias}")
        unit = data.get("unit")
        if unit is not None and (
            data["type"] != "integer" or not isinstance(unit, str) or not unit
        ):
            raise ConfigError("Only integer fields may declare a nonempty unit")
        kind = data.get("kind", "observation")
        if kind not in ("observation", "option"):
            raise ConfigError(f"Invalid field kind: {kind}")
        if kind == "option":
            if "default" not in data:
                raise ConfigError("An option requires an explicit default")
            validate_value(data["type"], data["default"], data["id"])
        elif "default" in data:
            raise ConfigError("Observed hardware cannot declare a configurable default")
        return cls(**data)

    @property
    def exported_macros(self) -> tuple[str, ...]:
        names = [self.macro, f"{self.macro}_AVAILABLE"]
        if self.alias:
            names.extend((self.alias, f"{self.alias}_AVAILABLE"))
        return tuple(names)


@dataclass(frozen=True)
class Declaration:
    module: str
    fields: tuple[Field, ...]

    @classmethod
    def from_data(cls, data: Any, *, module: str) -> Declaration:
        require_members(
            data,
            required={"schema_version", "module", "fields"},
            optional=set(),
            label="Fields document",
        )
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ConfigError("Fields document requires schema_version 1")
        if data["module"] != module:
            raise ConfigError(f"Fields document belongs to {data['module']}, expected {module}")
        if not isinstance(data["fields"], list):
            raise ConfigError("fields must be an array")
        fields = tuple(Field.from_data(entry) for entry in data["fields"])
        validate_declarations((cls(module, fields),))
        return cls(module, fields)


def validate_declarations(declarations: tuple[Declaration, ...]) -> None:
    identifiers: dict[str, str] = {}
    macros: dict[str, str] = {}
    for declaration in declarations:
        for item in declaration.fields:
            if item.id in identifiers:
                raise ConfigError(
                    f"Duplicate field {item.id}: {identifiers[item.id]} and {declaration.module}"
                )
            identifiers[item.id] = declaration.module
            for macro in item.exported_macros:
                if macro in macros:
                    raise ConfigError(
                        f"Duplicate generated macro {macro}: {macros[macro]} and {item.id}"
                    )
                macros[macro] = item.id


@dataclass(frozen=True)
class Observation:
    status: str
    value: bool | int | str | None = None
    provider: str = ""
    reason: str = ""

    @classmethod
    def available(cls, value: bool | int | str, *, provider: str) -> Observation:
        return cls("available", value=value, provider=provider)

    @classmethod
    def unavailable(
        cls, reason: str, *, status: str = "unavailable", provider: str = "probe"
    ) -> Observation:
        return cls(status, provider=provider, reason=reason)

    def validate(self, definition: Field) -> None:
        if (
            not isinstance(self.status, str)
            or self.status not in STATUSES
            or not isinstance(self.provider, str)
            or not self.provider
        ):
            raise ConfigError(f"Invalid observation status/provider for {definition.id}")
        if not isinstance(self.reason, str):
            raise ConfigError(f"Invalid observation reason for {definition.id}")
        if self.status == "available":
            validate_value(definition.type, self.value, definition.id)
        elif self.value is not None or not self.reason:
            raise ConfigError(
                f"Unavailable observation {definition.id} needs a reason and no value"
            )

    def to_data(self, definition: Field) -> dict:
        self.validate(definition)
        value = self.value
        # Decimal text keeps CMake JSON parsing from rounding 64-bit observations.
        if value is not None and definition.type == "integer":
            value = str(value)
        return {
            "type": definition.type,
            "unit": definition.unit,
            "status": self.status,
            "value": value,
            "provider": self.provider,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ProbeContext:
    project_root: Path
    module: str
    fields: tuple[Field, ...]
    target: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
