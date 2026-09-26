"""Execute registered probes and validate observations before publishing facts."""

from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .contracts import Observation, ProbeContext, validate_value
from .errors import ConfigError
from .inventory import Inventory
from tool.build_support.storage import contained_path
from .sync import Synchronizer


def collect_facts(
    inventory: Inventory,
    *,
    target: Mapping[str, Any] | None = None,
    options: Mapping[str, Any] | None = None,
    module: str | None = None,
) -> dict:
    service = Synchronizer(inventory)
    service.check()
    declarations = service.declarations()
    selected = [item for item in declarations if module is None or item.module == module]
    if module is not None and not selected:
        raise ConfigError(f"No registered define module: {module}")
    configurable = {
        item.id
        for declaration in declarations
        for item in declaration.fields
        if item.kind == "option"
    }
    options = dict(options or {})
    unknown = options.keys() - configurable
    if unknown:
        raise ConfigError(f"Overrides are not declared configurable options: {sorted(unknown)}")
    target = MappingProxyType(dict(target or {}))
    by_path = {item.path: item for item in inventory.modules}
    result: dict = {"schema_version": 1, "modules": {}}
    if "compilation_contexts" in target:
        result["compilation_contexts"] = target["compilation_contexts"]
    for declaration in selected:
        owner = by_path[declaration.module]
        source = contained_path(service.root, f"{owner.probe_relative}/probe.py")
        context = ProbeContext(inventory.root, owner.path, declaration.fields, target)
        observations = _execute_probe(source, context)
        expected = {item.id for item in declaration.fields if item.kind == "observation"}
        if not isinstance(observations, dict) or set(observations) != expected:
            actual = (
                sorted(str(key) for key in observations)
                if isinstance(observations, dict)
                else type(observations).__name__
            )
            raise ConfigError(
                f"Probe {owner.path} must return exactly {sorted(expected)}, received {actual}"
            )
        fields = {}
        for definition in declaration.fields:
            if definition.kind == "option":
                value = options.get(definition.id, definition.default)
                validate_value(definition.type, value, definition.id)
                observation = Observation.available(
                    value, provider="user-option" if definition.id in options else "default-option"
                )
            else:
                observation = observations[definition.id]
            if not isinstance(observation, Observation):
                raise ConfigError(
                    f"Probe {owner.path} returned a non-Observation for {definition.id}"
                )
            fact = observation.to_data(definition)
            fact.update(macro=definition.macro, alias=definition.alias, kind=definition.kind)
            fields[definition.id] = fact
        result["modules"][owner.path] = fields
    return result


def _execute_probe(path: Path, context: ProbeContext) -> dict[str, Observation]:
    name = "_destiny_probe_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ConfigError(f"Cannot load probe: {path}")
    loaded = importlib.util.module_from_spec(spec)
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            code = compile(path.read_bytes(), str(path), "exec")
            exec(code, loaded.__dict__)
            callback = getattr(loaded, "probe", None)
            if not callable(callback):
                raise ConfigError(f"Probe must export probe(context): {path}")
            result = callback(context)
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(
            f"Probe implementation failed in {path}: {type(exc).__name__}: {exc}"
        ) from exc
    if output.getvalue():
        raise ConfigError(f"Probe wrote to stdout instead of returning observations: {path}")
    return result
