from __future__ import annotations
import platform
from ..contracts import Observation, ProbeContext


def platform_facts(context: ProbeContext) -> dict[str, Observation]:
    system = str(context.target.get("system") or platform.system())
    bits = str(context.target.get("pointer_bytes", ""))
    result = {
        name: Observation.available(
            system == expected,
            provider="cmake-target" if context.target.get("system") else "host-platform",
        )
        for name, expected in (("windows", "Windows"), ("linux", "Linux"), ("macos", "Darwin"))
    }
    for name, size in (("x86", "4"), ("x64", "8")):
        result[name] = (
            Observation.available(bits == size, provider="cmake-target")
            if bits in ("4", "8")
            else Observation.unavailable(
                "Target pointer width was not provided",
                status="unsupported",
                provider="cmake-target",
            )
        )
    return result
