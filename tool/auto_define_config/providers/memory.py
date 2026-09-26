"""OS-visible physical memory, not installed DIMM inventory or available memory."""

from __future__ import annotations
import ctypes
from pathlib import Path
import platform
import re
import tempfile
from typing import Callable

from tool.build_support.process import ProcessFailure, run_command
from ..contracts import Observation
from ..errors import ConfigError


def parse_meminfo(text: str) -> int:
    match = re.search(r"^MemTotal:\s+([0-9]+)\s+kB\s*$", text, re.M)
    if match is None:
        raise ConfigError("Linux memory provider returned no valid MemTotal in kB")
    return int(match[1]) * 1024


def _windows_total() -> int:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_uint32),
            ("load", ctypes.c_uint32),
            ("total_physical", ctypes.c_uint64),
            ("available_physical", ctypes.c_uint64),
            ("total_pagefile", ctypes.c_uint64),
            ("available_pagefile", ctypes.c_uint64),
            ("total_virtual", ctypes.c_uint64),
            ("available_virtual", ctypes.c_uint64),
            ("available_extended", ctypes.c_uint64),
        ]

    value = MemoryStatus()
    value.length = ctypes.sizeof(value)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    query = kernel.GlobalMemoryStatusEx
    query.argtypes = [ctypes.POINTER(MemoryStatus)]
    query.restype = ctypes.c_int
    if not query(ctypes.byref(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return value.total_physical


def memory_facts(
    *,
    system: str | None = None,
    read_text: Callable[[Path], str] | None = None,
    windows_total: Callable[[], int] | None = None,
) -> dict[str, Observation]:
    system = system or platform.system()
    provider = {
        "Windows": "GlobalMemoryStatusEx",
        "Linux": "proc-meminfo",
        "Darwin": "sysctl-hw.memsize",
    }.get(system, "unknown-platform")
    try:
        if system == "Windows":
            amount = (windows_total or _windows_total)()
        elif system == "Linux":
            amount = parse_meminfo(
                (read_text or (lambda path: path.read_text(encoding="ascii")))(
                    Path("/proc/meminfo")
                )
            )
        elif system == "Darwin":
            with tempfile.TemporaryDirectory(prefix="destiny-memory-") as directory:
                result = run_command(
                    ["/usr/sbin/sysctl", "-n", "hw.memsize"], cwd=Path(directory), timeout=5
                )
            if result.returncode:
                raise OSError(result.stderr.strip() or "sysctl failed")
            if not result.stdout.strip().isdigit():
                raise ConfigError("sysctl memory provider returned invalid bytes")
            amount = int(result.stdout.strip())
        else:
            return {
                "memory.total_bytes": Observation.unavailable(
                    f"Unsupported OS: {system}", status="unsupported", provider=provider
                )
            }
        if type(amount) is not int or amount <= 0 or amount >= 2**63:
            raise ConfigError("OS memory capacity must be a positive signed 64-bit byte count")
        observation = Observation.available(amount, provider=provider)
    except PermissionError as exc:
        observation = Observation.unavailable(str(exc), status="denied", provider=provider)
    except ProcessFailure as exc:
        observation = Observation.unavailable(
            str(exc),
            status="timeout" if exc.phase == "timeout" else "unavailable",
            provider=provider,
        )
    except OSError as exc:
        observation = Observation.unavailable(str(exc), provider=provider)
    return {"memory.total_bytes": observation}
