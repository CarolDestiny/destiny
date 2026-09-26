"""CPUID/OS state observations and separate current-compiler ISA enablement."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
from typing import Any

from tool.build_support.errors import BuildError
from tool.build_support.process import ProcessFailure, compiler_environment, run_command
from tool.build_support.runtime import stage_runtime
from tool.build_support.compiler import compiler_fingerprint, macros
from ..contracts import Observation, ProbeContext
from ..errors import ConfigError

FEATURES = ("avx2", "avx512f", "avx512bw")


def decode_cpu(data: Any) -> dict[str, bool]:
    if not isinstance(data, dict) or set(data) != {
        "vendor",
        "leaf1_ecx",
        "leaf7_ebx",
        "xcr0_low",
        "target_bits",
    }:
        raise ConfigError("Native CPU provider returned an invalid object")
    vendor = data["vendor"]
    if (
        not isinstance(vendor, list)
        or len(vendor) != 3
        or not all(type(v) is int and 0 <= v < 2**32 for v in vendor)
    ):
        raise ConfigError("Native CPU provider returned invalid vendor registers")
    for key in ("leaf1_ecx", "leaf7_ebx", "xcr0_low"):
        if type(data[key]) is not int or not 0 <= data[key] < 2**32:
            raise ConfigError(f"Invalid CPU register: {key}")
    if data["target_bits"] not in (32, 64):
        raise ConfigError("CPU provider target width is not x86/x64")
    identity = struct.pack("<III", *vendor)
    ecx, ebx, xcr0 = data["leaf1_ecx"], data["leaf7_ebx"], data["xcr0_low"]
    avx_state = (
        (ecx & (1 << 26)) and (ecx & (1 << 27)) and (ecx & (1 << 28)) and (xcr0 & 0x6) == 0x6
    )
    avx512_state = avx_state and (xcr0 & 0xE6) == 0xE6
    return {
        "cpuIntel": identity == b"GenuineIntel",
        "cpuAMD": identity == b"AuthenticAMD",
        "avx2": bool(avx_state and (ebx & (1 << 5))),
        "avx512f": bool(avx512_state and (ebx & (1 << 16))),
        "avx512bw": bool(avx512_state and (ebx & (1 << 16)) and (ebx & (1 << 30))),
    }


def _observe(context: ProbeContext, scratch: Path) -> dict[str, bool]:
    compiler = Path(str(context.target["compiler"]))
    pointer = str(context.target.get("pointer_bytes", ""))
    if pointer not in ("4", "8"):
        raise ProcessFailure("architecture", "CPU provider needs the selected target pointer width")
    architecture = "x86" if pointer == "4" else "x64"
    source = Path(__file__).parent / "native/cpu.cpp"
    signature = compiler_fingerprint((compiler,))
    key = hashlib.sha256(source.read_bytes() + str((signature, architecture)).encode()).hexdigest()[
        :24
    ]
    cache = scratch / key
    cache.mkdir(parents=True, exist_ok=True)
    executable = cache / ("cpu.exe" if os.name == "nt" else "cpu")
    environment = compiler_environment(compiler)
    if not executable.exists():
        output = run_command(
            [
                compiler,
                "-m32" if pointer == "4" else "-m64",
                "-std=c++11",
                "-O0",
                source,
                "-o",
                executable,
            ],
            cwd=cache,
            env=environment,
            timeout=30,
        )
        if output.returncode:
            raise ProcessFailure("compile", f"CPU helper compilation failed: {output.stderr}")
    if os.name == "nt":
        try:
            stage_runtime(executable, compiler, cache)
        except BuildError as exc:
            raise ProcessFailure("runtime", str(exc)) from exc
    output = run_command([executable], cwd=cache, env=environment, timeout=5)
    if output.returncode:
        raise ProcessFailure(
            "run", f"CPU helper could not execute ({output.returncode}): {output.stderr}"
        )
    try:
        data = json.loads(output.stdout)
    except ValueError as exc:
        raise ConfigError("Native CPU provider returned malformed JSON") from exc
    result = decode_cpu(data)
    if data["target_bits"] != int(pointer) * 8:
        raise ConfigError("CPU helper ran with the wrong target architecture")
    flags = context.target.get("compiler_flags", [])
    if not isinstance(flags, list) or not all(isinstance(x, str) for x in flags):
        raise ConfigError("compiler_flags must be an argument array")
    definitions = macros(compiler, tuple(flags), "c++", cache)
    for feature in FEATURES:
        result[feature] = result[feature] and f"__{feature.upper()}__" in definitions
    return result


def cpu_facts(context: ProbeContext) -> dict[str, Observation]:
    if not context.target.get("compiler"):
        return {
            name: Observation.unavailable(
                "Selected compiler context is required",
                status="unsupported",
                provider="native-cpuid",
            )
            for name in ("cpuIntel", "cpuAMD", *FEATURES)
        }
    try:
        if context.target.get("probe_cache"):
            root = Path(str(context.target["probe_cache"])).resolve()
            if root.is_relative_to(
                (context.project_root / "source").resolve()
            ) or root.is_relative_to((context.project_root / "tool").resolve()):
                raise ConfigError("Probe cache must not be stored in maintained source directories")
            root.mkdir(parents=True, exist_ok=True)
            values = _observe(context, root)
        else:
            with tempfile.TemporaryDirectory(prefix="destiny-cpu-") as directory:
                values = _observe(context, Path(directory))
        return {
            name: Observation.available(
                value, provider="cpuid-os-compiler" if name in FEATURES else "native-cpuid"
            )
            for name, value in values.items()
        }
    except ProcessFailure as exc:
        status = "timeout" if exc.phase == "timeout" else "unavailable"
        return {
            name: Observation.unavailable(str(exc), status=status, provider="native-cpuid")
            for name in ("cpuIntel", "cpuAMD", *FEATURES)
        }
    except PermissionError as exc:
        return {
            name: Observation.unavailable(str(exc), status="denied", provider="native-cpuid")
            for name in ("cpuIntel", "cpuAMD", *FEATURES)
        }
    except OSError as exc:
        return {
            name: Observation.unavailable(str(exc), provider="native-cpuid")
            for name in ("cpuIntel", "cpuAMD", *FEATURES)
        }
