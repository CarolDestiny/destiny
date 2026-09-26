from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


class Workspace:
    def __init__(self, *, framework: bool = False):
        parent = ROOT / "build" / "verification"
        parent.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(prefix="case-", dir=parent)
        self.root = Path(self._temporary.name)
        if framework:
            for name in ("cmake", "tool"):
                shutil.copytree(
                    ROOT / name, self.root / name, ignore=shutil.ignore_patterns("__pycache__")
                )
            shutil.copy2(ROOT / "CMakeLists.txt", self.root / "CMakeLists.txt")

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def module(self, name: str, registration: str = "destiny_add_module()") -> Path:
        return self.write(f"source/{name}/CMakeLists.txt", registration + "\n")

    def close(self) -> None:
        if not self.root.resolve().is_relative_to((ROOT / "build" / "verification").resolve()):
            raise RuntimeError("Refusing cleanup outside validation workspace")
        self._temporary.cleanup()

    def run(
        self, *args: str, ok: bool = True, cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        result = subprocess.run(
            args,
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if ok and result.returncode:
            raise AssertionError(
                f"Command failed ({result.returncode}): {args}\n{result.stdout}\n{result.stderr}"
            )
        return result

    def configure(self, *extra: str, ok: bool = True) -> subprocess.CompletedProcess:
        compiler = os.environ.get("DESTINY_TEST_CXX", shutil.which("g++"))
        c_compiler = os.environ.get("DESTINY_TEST_CC", shutil.which("gcc"))
        return self.run(
            "cmake",
            "-S",
            str(self.root),
            "-B",
            str(self.root / "out"),
            "-G",
            "Ninja",
            "-DCMAKE_BUILD_TYPE=Debug",
            f"-DCMAKE_C_COMPILER={Path(c_compiler).as_posix()}",
            f"-DCMAKE_CXX_COMPILER={Path(compiler).as_posix()}",
            f"-DPython3_EXECUTABLE={Path(sys.executable).as_posix()}",
            "-DDESTINY_NATIVE_OPTIMIZATION=OFF",
            "-DDESTINY_BUILD_TESTS=OFF",
            *extra,
            ok=ok,
        )
