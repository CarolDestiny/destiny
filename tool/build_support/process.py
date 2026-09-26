"""Bounded, cancellable subprocesses for probes and interactive tools."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time
from typing import Mapping, Sequence

from .errors import BuildError


class ProcessFailure(BuildError):
    def __init__(self, phase: str, message: str):
        self.phase = phase
        super().__init__(message)


def check_cancelled(cancel: threading.Event | None) -> None:
    if cancel is not None and cancel.is_set():
        raise ProcessFailure("cancelled", "Operation was cancelled before publication")


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str
    stderr: str


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/taskkill.exe"
        try:
            subprocess.run(
                [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def run_command(
    command: Sequence[str | Path],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    input_text: str = "",
    timeout: float = 30,
    output_limit: int = 1024 * 1024,
    cancel: threading.Event | None = None,
) -> Result:
    if cancel is not None and cancel.is_set():
        raise ProcessFailure("cancelled", "Operation was cancelled")
    arguments = [str(item) for item in command]
    with (
        tempfile.TemporaryFile() as source,
        tempfile.TemporaryFile() as out,
        tempfile.TemporaryFile() as err,
    ):
        source.write(input_text.encode("utf-8"))
        source.seek(0)
        options = (
            {"creationflags": subprocess.CREATE_NO_WINDOW}
            if os.name == "nt"
            else {"start_new_session": True}
        )
        try:
            process = subprocess.Popen(
                arguments,
                cwd=cwd,
                env=env,
                stdin=source,
                stdout=out,
                stderr=err,
                shell=False,
                **options,
            )
        except OSError as exc:
            raise ProcessFailure("startup", f"Cannot start {arguments[0]}: {exc}") from exc
        started = time.monotonic()
        try:
            while process.poll() is None:
                if cancel is not None and cancel.is_set():
                    raise ProcessFailure("cancelled", f"Cancelled {arguments[0]}")
                if time.monotonic() - started > timeout:
                    raise ProcessFailure("timeout", f"Timeout after {timeout:g}s: {arguments[0]}")
                if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > output_limit:
                    raise ProcessFailure(
                        "output-limit", f"Output exceeded {output_limit} bytes: {arguments[0]}"
                    )
                time.sleep(0.025)
            if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > output_limit:
                raise ProcessFailure(
                    "output-limit", f"Output exceeded {output_limit} bytes: {arguments[0]}"
                )
            out.seek(0)
            err.seek(0)
            return Result(
                process.returncode,
                out.read().decode("utf-8", "replace"),
                err.read().decode("utf-8", "replace"),
            )
        finally:
            _stop(process)


def compiler_environment(compiler: Path) -> dict[str, str]:
    environment = os.environ.copy()
    for name in (
        "CC",
        "CXX",
        "CFLAGS",
        "CXXFLAGS",
        "CPPFLAGS",
        "LDFLAGS",
        "CPATH",
        "C_INCLUDE_PATH",
        "CPLUS_INCLUDE_PATH",
        "LIBRARY_PATH",
        "GCC_EXEC_PREFIX",
        "COMPILER_PATH",
    ):
        environment.pop(name, None)
    paths = [str(compiler.resolve().parent)]
    for item in os.environ.get("PATH", "").split(os.pathsep):
        path = Path(item)
        if not item or path.resolve() == compiler.resolve().parent:
            continue
        if os.name == "nt" and any(
            (path / name).exists() for name in ("gcc.exe", "clang.exe", "g++.exe", "clang++.exe")
        ):
            continue
        paths.append(item)
    environment["PATH"] = os.pathsep.join(paths)
    environment["LC_ALL"] = "C"
    return environment
