"""Incremental correspondence checks; existing source is never regenerated."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .contracts import Declaration, validate_declarations
from .errors import ConfigError
from .inventory import Inventory, MODULE_PATH
from tool.build_support.storage import (
    contained_path,
    create_missing,
    fingerprint,
    json_text,
    read_json,
    replace_checked,
)

PROBE_TEMPLATE = '''"""Observations for {module}; keep handwritten logic in this file."""
from tool.auto_define_config.contracts import Observation, ProbeContext


def probe(context: ProbeContext) -> dict[str, Observation]:
    return {{
        item.id: Observation.unavailable(
            "Probe implementation is not provided", status="unimplemented"
        )
        for item in context.fields if item.kind == "observation"
    }}
'''


@dataclass(frozen=True)
class SyncEntry:
    module: str
    file: str
    status: str
    reason: str = ""

    def to_data(self) -> dict:
        return asdict(self)


class Synchronizer:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory
        self.root = inventory.root / "tool" / "auto_define_config" / "define"

    def inspect(self) -> tuple[SyncEntry, ...]:
        entries = []
        expected = set()
        for module in self.inventory.modules:
            if not module.is_define:
                continue
            for name in ("probe.py", "fields.json"):
                relative = f"{module.probe_relative}/{name}"
                target = contained_path(self.root, relative)
                expected.add(target.relative_to(self.root).as_posix())
                parents = [parent for parent in target.parents if parent.is_relative_to(self.root)]
                invalid_parent = next(
                    (
                        parent
                        for parent in parents
                        if parent.is_symlink() or (parent.exists() and not parent.is_dir())
                    ),
                    None,
                )
                if target.is_symlink() or invalid_parent is not None:
                    status, reason = (
                        "conflict",
                        "Managed counterpart paths require real directories and regular files",
                    )
                elif target.is_file():
                    status, reason = "unchanged", ""
                elif target.exists():
                    status, reason = "conflict", "Expected a file"
                else:
                    status, reason = "missing", ""
                entries.append(SyncEntry(module.path, str(target), status, reason))
        if self.root.exists():
            for target in sorted(self.root.rglob("*")):
                if target.name not in ("probe.py", "fields.json") or not target.is_file():
                    continue
                relative = target.relative_to(self.root).as_posix()
                if relative not in expected:
                    parent = target.parent.relative_to(self.root).as_posix()
                    module = "define" if parent == "." else f"define/{parent}"
                    entries.append(SyncEntry(module, str(target), "orphaned"))
        return tuple(entries)

    def check(self) -> tuple[SyncEntry, ...]:
        entries = self.inspect()
        invalid = [item for item in entries if item.status in ("missing", "conflict")]
        if invalid:
            details = "\n".join(f"  {item.status}: {item.file} {item.reason}" for item in invalid)
            raise ConfigError(
                "Define probes are not synchronized. Run auto_define_config sync.\n" + details
            )
        self.declarations()
        from .rules import load_rules

        for module in self.inventory.modules:
            rule_file = self.inventory.root / "source" / module.path / "source_rules.json"
            if rule_file.exists():
                load_rules(rule_file)
        return entries

    def declarations(self) -> tuple[Declaration, ...]:
        result = []
        for module in self.inventory.modules:
            if module.is_define:
                path = contained_path(self.root, f"{module.probe_relative}/fields.json")
                result.append(Declaration.from_data(read_json(path), module=module.path))
        declarations = tuple(result)
        validate_declarations(declarations)
        return declarations

    def apply(self) -> tuple[SyncEntry, ...]:
        entries = self.inspect()
        conflicts = [item for item in entries if item.status == "conflict"]
        if conflicts:
            raise ConfigError(
                "Synchronization conflicts: " + "; ".join(item.file for item in conflicts)
            )
        result = []
        for item in entries:
            if item.status != "missing":
                result.append(item)
                continue
            path = Path(item.file)
            content = (
                PROBE_TEMPLATE.format(module=item.module)
                if path.name == "probe.py"
                else json_text({"schema_version": 1, "module": item.module, "fields": []})
            )
            created = create_missing(path, content)
            result.append(SyncEntry(item.module, item.file, "created" if created else "unchanged"))
        return tuple(result)

    def rename(self, old: str, new: str, *, dry_run: bool = True) -> dict:
        if (
            not MODULE_PATH.fullmatch(old)
            or not MODULE_PATH.fullmatch(new)
            or not old.startswith("define/")
            or not new.startswith("define/")
        ):
            raise ConfigError("Explicit counterpart renames require canonical define/module paths")
        registered = {item.path for item in self.inventory.modules}
        if old in registered or new not in registered:
            raise ConfigError(
                "Register the new module and remove the old registration before migrating its counterpart"
            )
        source = contained_path(self.root, old.removeprefix("define/"))
        destination = contained_path(self.root, new.removeprefix("define/"))
        if (
            not source.is_dir()
            or source.is_symlink()
            or destination.exists()
            or destination.is_relative_to(source)
        ):
            raise ConfigError(
                "Rename source must exist, and its independent destination must not exist"
            )
        if any(path.is_symlink() for path in source.rglob("*")) or any(
            path.is_symlink() for path in source.parents if path.is_relative_to(self.root)
        ):
            raise ConfigError("Counterpart migration does not follow symbolic links")
        if any(path.parent != source for path in source.rglob("fields.json")):
            raise ConfigError(
                "Migrate nested module counterparts individually, not as an implicit subtree rename"
            )
        declarations = source / "fields.json"
        revision = fingerprint(declarations)
        data = read_json(declarations)
        Declaration.from_data(data, module=old)
        data = dict(data, module=new)
        plan = {
            "old": old,
            "new": new,
            "source": str(source),
            "destination": str(destination),
            "dry_run": dry_run,
        }
        if dry_run:
            return plan
        if fingerprint(declarations) != revision:
            raise ConfigError("Fields changed during migration review")
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        try:
            replace_checked(destination / "fields.json", json_text(data), expected=revision)
        except Exception:
            destination.rename(source)
            raise
        return plan
