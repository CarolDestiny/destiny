"""Compiler predefines and binary-architecture inspection shared by both tools."""

from __future__ import annotations
from pathlib import Path
import hashlib
import re
import struct
import threading
from .pe import read_pe
from .process import ProcessFailure, check_cancelled, compiler_environment, run_command


def compiler_fingerprint(paths: tuple[Path, ...], cancel: threading.Event | None = None) -> str:
    digest = hashlib.sha256()
    for path in paths:
        check_cancelled(cancel)
        digest.update(str(path.absolute()).encode("utf-8") + b"\0")
        content = hashlib.sha256()
        with path.open("rb") as stream:
            while block := stream.read(1024 * 1024):
                check_cancelled(cancel)
                content.update(block)
        digest.update(content.digest())
    return digest.hexdigest()


def macros(
    compiler: Path,
    flags: tuple[str, ...],
    language: str,
    scratch: Path,
    cancel: threading.Event | None = None,
) -> dict[str, str]:
    result = run_command(
        [compiler, *flags, "-dM", "-E", "-x", language, "-"],
        cwd=scratch,
        env=compiler_environment(compiler),
        timeout=15,
        cancel=cancel,
    )
    if result.returncode:
        raise ProcessFailure(
            "identity", f"Cannot preprocess using {compiler}: {result.stderr.strip()}"
        )
    return dict(re.findall(r"^#define ([A-Za-z_][A-Za-z0-9_]*)\s+([^\r\n]+)", result.stdout, re.M))


def identify(definitions: dict[str, str]) -> tuple[str, str, str]:
    if "__clang__" in definitions:
        family = "clang"
        parts = ("__clang_major__", "__clang_minor__", "__clang_patchlevel__")
    elif "__GNUC__" in definitions:
        family = "gcc"
        parts = ("__GNUC__", "__GNUC_MINOR__", "__GNUC_PATCHLEVEL__")
    else:
        raise ProcessFailure("identity", "Compiler is neither GCC nor Clang")
    version = ".".join(definitions.get(name, "0") for name in parts)
    architecture = (
        "x64" if "__x86_64__" in definitions else "x86" if "__i386__" in definitions else "other"
    )
    return family, version, architecture


def executable_architecture(path: Path) -> str:
    with path.open("rb") as stream:
        header = stream.read(32)
    if header[:2] == b"MZ":
        return read_pe(path).architecture
    if header[:4] == b"\x7fELF" and len(header) >= 20:
        order = "<" if header[5] == 1 else ">"
        machine = struct.unpack_from(order + "H", header, 18)[0]
        if (header[4], machine) == (1, 3):
            return "x86"
        if (header[4], machine) == (2, 62):
            return "x64"
    if header[:4] in (b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
        cpu = struct.unpack_from("<I", header, 4)[0]
        if cpu == 7:
            return "x86"
        if cpu == 0x1000007:
            return "x64"
    raise ProcessFailure(
        "architecture", f"Unsupported or unexpected executable architecture: {path}"
    )
