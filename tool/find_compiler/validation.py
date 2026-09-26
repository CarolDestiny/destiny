"""Compile, link, inspect and run a C/C++20 probe for one compiler/target pair."""

from __future__ import annotations

import os
from pathlib import Path
import platform
import tempfile
import threading

from tool.build_support.errors import BuildError
from tool.build_support.compiler import (
    compiler_fingerprint,
    executable_architecture,
    identify,
    macros,
)
from tool.build_support.process import ProcessFailure, compiler_environment, run_command
from tool.build_support.runtime import stage_runtime
from .model import Candidate, Toolchain

C_SOURCE = "int destiny_c_bits(void) { return (int)(sizeof(void*) * 8); }\n"
CXX_SOURCE = r"""#include <array>
#include <iostream>
#include <span>
#include <string>
extern "C" int destiny_c_bits(void);
int main() {
    std::array<int, 2> values{1, 2};
    std::span<const int> view(values);
    if (view.size() != 2 || destiny_c_bits() != sizeof(void*) * 8) return 1;
    std::cout << "destiny:" << sizeof(void*) * 8 << ':' << std::string(32, 'x').size();
}
"""


def validate(
    candidate: Candidate, architecture: str, *, cancel: threading.Event | None = None
) -> Toolchain:
    if architecture not in ("x86", "x64"):
        raise BuildError(f"Unsupported requested architecture: {architecture}")
    host = platform.system().lower()
    family, version, target = "unknown", "", ""
    signature = ""
    flags: tuple[str, ...] = ()
    phase = "identity"
    c, cxx = candidate.c.absolute(), candidate.cxx.absolute()

    def result(status: str, reason: str = "") -> Toolchain:
        return Toolchain(
            str(c),
            str(cxx),
            family,
            version,
            architecture,
            host,
            target,
            flags,
            status,
            "" if status == "available" else phase,
            reason,
            signature,
        )

    try:
        with tempfile.TemporaryDirectory(prefix="destiny-compiler-") as directory:
            scratch = Path(directory)
            definitions = macros(cxx, (), "c++", scratch, cancel)
            family, version, default_arch = identify(definitions)
            if host == "windows" and "__MINGW32__" not in definitions:
                raise ProcessFailure(
                    "identity",
                    "Windows support requires MinGW GCC or LLVM-MinGW, not MSVC ABI Clang",
                )
            if host == "darwin" and architecture == "x86":
                raise ProcessFailure(
                    "architecture", "32-bit x86 macOS programs are not supported by this tool"
                )
            flags = (
                ()
                if default_arch == architecture
                else ("-m32" if architecture == "x86" else "-m64",)
            )
            c_macros = macros(c, flags, "c", scratch, cancel)
            c_identity = identify(c_macros)
            chosen = macros(cxx, flags, "c++", scratch, cancel)
            if c_identity != identify(chosen) or c_identity[2] != architecture:
                raise ProcessFailure(
                    "identity",
                    f"C/C++ compiler family, version or architecture mismatch: {c_identity} vs {identify(chosen)}",
                )
            triple = run_command(
                [cxx, *flags, "-dumpmachine"],
                cwd=scratch,
                env=compiler_environment(cxx),
                timeout=15,
                cancel=cancel,
            )
            if triple.returncode:
                raise ProcessFailure("identity", "Cannot obtain compiler target triple")
            target = triple.stdout.strip()
            signature = compiler_fingerprint((c, cxx), cancel)
            (scratch / "probe.c").write_text(C_SOURCE, encoding="utf-8")
            (scratch / "probe.cpp").write_text(CXX_SOURCE, encoding="utf-8")
            steps = [
                ("compile-c", [c, *flags, "-c", "probe.c", "-o", "c.o"]),
                ("compile-cxx20", [cxx, *flags, "-std=c++20", "-c", "probe.cpp", "-o", "cxx.o"]),
                (
                    "link",
                    [
                        cxx,
                        *flags,
                        "c.o",
                        "cxx.o",
                        "-o",
                        "probe.exe" if host == "windows" else "probe",
                    ],
                ),
            ]
            for phase, command in steps:
                output = run_command(
                    command,
                    cwd=scratch,
                    env=compiler_environment(Path(command[0])),
                    timeout=45,
                    cancel=cancel,
                )
                if output.returncode:
                    return result(
                        "unavailable",
                        output.stderr.strip()
                        or output.stdout.strip()
                        or f"Exit status {output.returncode}",
                    )
            executable = scratch / ("probe.exe" if host == "windows" else "probe")
            phase = "architecture"
            actual = executable_architecture(executable)
            if actual != architecture:
                return result("unavailable", f"Expected {architecture}, executable is {actual}")
            phase = "runtime"
            environment = compiler_environment(cxx)
            if host == "windows":
                stage_runtime(executable, cxx, scratch)
                environment["PATH"] = str(
                    Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
                )
            phase = "run"
            output = run_command(
                [executable], cwd=scratch, env=environment, timeout=10, cancel=cancel
            )
            expected = f'destiny:{32 if architecture=="x86" else 64}:32'
            if output.returncode or output.stdout.strip() != expected:
                return result(
                    "unavailable",
                    f"Probe execution failed ({output.returncode}); expected {expected!r}, received {output.stdout!r}; {output.stderr}",
                )
            if compiler_fingerprint((c, cxx), cancel) != signature:
                raise ProcessFailure(
                    "identity", "Compiler executables changed during validation; retry"
                )
            return result("available")
    except ProcessFailure as exc:
        phase = exc.phase
        if phase == "cancelled":
            raise
        return result("unavailable", str(exc))
    except (BuildError, OSError) as exc:
        return result("unavailable", str(exc))
