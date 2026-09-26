"""Structural rule validation; expression evaluation belongs exclusively to CMake."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
from typing import Any

from .contracts import IDENTIFIER, require_members
from .errors import ConfigError
from tool.build_support.storage import read_json

NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")


def validate_expression(expression: Any, *, depth: int = 0) -> None:
    if depth > 64:
        raise ConfigError("Condition nesting exceeds 64 levels")
    if type(expression) is bool:
        return
    require_members(
        expression,
        required=set(),
        optional={"ref", "all", "any", "not", "compare"},
        label="Condition",
    )
    if len(expression) != 1:
        raise ConfigError("Condition must contain exactly one operator")
    operation, value = next(iter(expression.items()))
    if operation == "ref":
        if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
            raise ConfigError("Condition ref must be a field or alias identifier")
    elif operation in ("all", "any"):
        if not isinstance(value, list) or not value:
            raise ConfigError(f"{operation} needs a nonempty array of conditions")
        for child in value:
            validate_expression(child, depth=depth + 1)
    elif operation == "not":
        validate_expression(value, depth=depth + 1)
    else:
        require_members(
            value, required={"field", "op", "value"}, optional={"unit"}, label="Comparison"
        )
        if not isinstance(value["field"], str) or not IDENTIFIER.fullmatch(value["field"]):
            raise ConfigError("Comparison field must be an identifier")
        if value["op"] not in ("eq", "ne", "lt", "le", "gt", "ge"):
            raise ConfigError("Comparison op must be eq, ne, lt, le, gt or ge")
        if not isinstance(value["value"], str):
            raise ConfigError(
                "Comparison values use strings; integer values use exact decimal text"
            )
        if "unit" in value and (not isinstance(value["unit"], str) or not value["unit"]):
            raise ConfigError("Comparison unit must be a nonempty string")


def _name(name: Any, label: str) -> str:
    if not isinstance(name, str) or not NAME.fullmatch(name) or name.lower() in ("true", "false"):
        raise ConfigError(f"Invalid {label} name: {name}")
    return name


def validate_rules(data: Any) -> dict:
    require_members(
        data, required={"schema_version", "aliases", "groups"}, optional=set(), label="Source rules"
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ConfigError("Source rules require schema_version 1")
    if not isinstance(data["aliases"], dict) or not isinstance(data["groups"], list):
        raise ConfigError("Source rules need aliases object and groups array")
    for name, expression in data["aliases"].items():
        _name(name, "alias")
        validate_expression(expression)
    seen_groups = set()
    claimed = set()
    for group in data["groups"]:
        require_members(
            group, required={"name", "candidates"}, optional=set(), label="Implementation group"
        )
        name = _name(group["name"], "group")
        if name in seen_groups:
            raise ConfigError(f"Duplicate implementation group: {name}")
        seen_groups.add(name)
        candidates = group["candidates"]
        if not isinstance(candidates, list) or not candidates:
            raise ConfigError(f"Implementation group {name} needs candidates")
        seen_candidates = set()
        for candidate in candidates:
            require_members(
                candidate, required={"name", "when", "sources"}, optional=set(), label="Candidate"
            )
            cname = _name(candidate["name"], "candidate")
            if cname in seen_candidates:
                raise ConfigError(f"Duplicate candidate: {name}/{cname}")
            seen_candidates.add(cname)
            validate_expression(candidate["when"])
            members = candidate["sources"]
            if not isinstance(members, list) or not members:
                raise ConfigError(f"Candidate {name}/{cname} needs source files")
            for source in members:
                if (
                    not isinstance(source, str)
                    or not source.startswith("src/")
                    or any(c in source for c in (";", "\\", "\n", "\r"))
                ):
                    raise ConfigError(f"Invalid candidate source path: {source}")
                path = PurePosixPath(source)
                if ".." in path.parts or path.as_posix() != source or path.suffix != ".cpp":
                    raise ConfigError(
                        f"Source must be a canonical module-relative src/*.cpp path: {source}"
                    )
                if source in claimed:
                    raise ConfigError(f"Source belongs to multiple candidates: {source}")
                claimed.add(source)
    return data


def load_rules(path: Path) -> dict:
    return validate_rules(read_json(path))
