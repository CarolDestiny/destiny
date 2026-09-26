from dataclasses import replace
import json
import os
from pathlib import Path
import sys
import threading
import unittest

from tests.build_system.support import Workspace
from tool.build_support.errors import BuildError
from tool.build_support.compiler import compiler_fingerprint
from tool.build_support.process import ProcessFailure, run_command
from tool.find_compiler.discovery import discover, pair_for
from tool.find_compiler.model import Toolchain
from tool.find_compiler.presets import merge_presets, write_presets
from tool.find_compiler.validation import identify


def chain(host="windows", architecture="x64"):
    return Toolchain(
        "C:/gcc/bin/gcc.exe",
        "C:/gcc/bin/g++.exe",
        "gcc",
        "16.2.0",
        architecture,
        host,
        "x86_64-w64-mingw32",
        (),
        "available",
    )


class CompilerToolsTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace()
        self.addCleanup(self.w.close)

    def test_discovery_pairs_drivers_without_running_them(self):
        w = self.w
        for name in (
            "x64/bin/g++.exe",
            "x64/bin/gcc.exe",
            "x86/bin/i686-w64-mingw32-clang++.exe",
            "x86/bin/i686-w64-mingw32-clang.exe",
            "orphan/clang++.exe",
            "include/bin/g++.exe",
            "include/bin/gcc.exe",
        ):
            w.write(name, "not executable")
        result = discover([w.root], include_defaults=False)
        self.assertEqual(len(result), 2)
        self.assertIsNone(pair_for(w.root / "orphan/clang++.exe"))

    def test_macros_identify_clang_even_when_named_gcc(self):
        result = identify(
            {
                "__clang__": "1",
                "__clang_major__": "22",
                "__clang_minor__": "1",
                "__clang_patchlevel__": "8",
                "__GNUC__": "4",
                "__x86_64__": "1",
            }
        )
        self.assertEqual(result, ("clang", "22.1.8", "x64"))

    def test_merge_preserves_users_other_platforms_and_unknown_root_keys(self):
        existing = {
            "version": 6,
            "vendor": {"user": "keep"},
            "configurePresets": [{"name": "user", "generator": "Ninja"}],
        }
        linux = chain("linux")
        first = merge_presets(
            existing, [linux], python=Path("/usr/bin/python3"), ninja=Path("/usr/bin/ninja")
        )
        merged = merge_presets(
            first, [chain()], python=Path("C:/Python/python.exe"), ninja=Path("C:/ninja.exe")
        )
        self.assertEqual(merged["vendor"], existing["vendor"])
        self.assertEqual(merged["configurePresets"][0], existing["configurePresets"][0])
        self.assertEqual(len(merged["configurePresets"]), 5)
        repeat = merge_presets(
            merged, [chain()], python=Path("C:/Python/python.exe"), ninja=Path("C:/ninja.exe")
        )
        self.assertEqual(repeat, merged)
        self.assertEqual(len(existing["configurePresets"]), 1)

    def test_unowned_name_collision_does_not_overwrite(self):
        preset = merge_presets(
            {"version": 6}, [chain()], python=Path("python"), ninja=Path("ninja")
        )
        preset["configurePresets"][0].pop("vendor")
        with self.assertRaisesRegex(BuildError, "not owned"):
            merge_presets(preset, [chain()], python=Path("python"), ninja=Path("ninja"))

    def test_unavailable_results_cannot_generate_presets(self):
        with self.assertRaisesRegex(BuildError, "validated"):
            merge_presets(
                {"version": 6},
                [replace(chain(), status="unavailable")],
                python=Path("python"),
                ninja=Path("ninja"),
            )

    def test_write_presets_is_incremental_and_does_not_create_build_artifacts(self):
        w = self.w
        w.write(
            "CMakePresets.json",
            '{"version":6,"configurePresets":[{"name":"destiny-base","hidden":true}]}',
        )
        ninja = w.write("tools/ninja", "")
        c = w.write("compiler/gcc.exe", "fixture-c-driver")
        cxx = w.write("compiler/g++.exe", "fixture-cxx-driver")
        toolchain = replace(
            chain(), c=str(c), cxx=str(cxx), compiler_fingerprint=compiler_fingerprint((c, cxx))
        )
        path = write_presets(w.root, [toolchain], ninja=ninja)
        before = path.stat().st_mtime_ns
        write_presets(w.root, [toolchain], ninja=ninja)
        self.assertEqual(path.stat().st_mtime_ns, before)
        self.assertFalse((w.root / "build").exists())

    def test_bounded_process_timeout_and_output_limit(self):
        with self.assertRaises(ProcessFailure) as caught:
            run_command(
                [sys.executable, "-c", "import time; time.sleep(10)"], cwd=self.w.root, timeout=0.15
            )
        self.assertEqual(caught.exception.phase, "timeout")
        with self.assertRaises(ProcessFailure) as caught:
            run_command(
                [sys.executable, "-c", 'print("x"*65536)'], cwd=self.w.root, output_limit=128
            )
        self.assertEqual(caught.exception.phase, "output-limit")

    def test_cancellation_and_startup_errors(self):
        stop = threading.Event()
        stop.set()
        with self.assertRaises(ProcessFailure) as caught:
            run_command(
                [sys.executable, "-c", "raise RuntimeError()"], cwd=self.w.root, cancel=stop
            )
        self.assertEqual(caught.exception.phase, "cancelled")
        with self.assertRaises(ProcessFailure) as caught:
            run_command([self.w.root / "missing-compiler"], cwd=self.w.root)
        self.assertEqual(caught.exception.phase, "startup")

    def test_input_and_output_capture(self):
        result = run_command(
            [
                sys.executable,
                "-c",
                'import sys; print(sys.stdin.read()); print("err",file=sys.stderr)',
            ],
            cwd=self.w.root,
            input_text="payload",
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "payload")
        self.assertEqual(result.stderr.strip(), "err")

    def test_manual_validation_does_not_claim_untested_combinations_failed(self):
        from tool.find_compiler.model import combination_summary

        summary = combination_summary([chain()])
        statuses = {(item["family"], item["architecture"]): item["status"] for item in summary}
        self.assertEqual(statuses[("gcc", "x64")], "available")
        self.assertEqual(statuses[("gcc", "x86")], "unchecked")
        self.assertEqual(statuses[("clang", "x64")], "unchecked")
        self.assertTrue(
            all(
                item["status"] == "not-found"
                for item in combination_summary([], scan_complete=True)
            )
        )
        failed = replace(chain(), status="unavailable", phase="link", reason="Missing runtime")
        summary = combination_summary([failed])
        self.assertEqual(
            next(
                item["status"]
                for item in summary
                if item["family"] == "gcc" and item["architecture"] == "x64"
            ),
            "unavailable",
        )

    def test_spaces_and_unicode_driver_paths_survive_discovery_and_validation_arguments(self):
        from unittest.mock import patch
        from tool.build_support.process import Result
        from tool.find_compiler.validation import validate

        c = self.w.write("compiler space \u03a9/bin/gcc.exe", "fixture C driver")
        cxx = self.w.write("compiler space \u03a9/bin/g++.exe", "fixture C++ driver")
        candidates = discover([c.parent.parent], include_defaults=False)
        self.assertEqual(len(candidates), 1)
        definitions = {
            "__GNUC__": "16",
            "__GNUC_MINOR__": "2",
            "__GNUC_PATCHLEVEL__": "0",
            "__x86_64__": "1",
            "__MINGW32__": "1",
        }
        observed = []

        def run(command, **kwargs):
            observed.append(command)
            if "-dumpmachine" in command:
                return Result(0, "x86_64-w64-mingw32", "")
            return Result(0, "destiny:64:32", "")

        with (
            patch("tool.find_compiler.validation.platform.system", return_value="Windows"),
            patch("tool.find_compiler.validation.macros", return_value=definitions) as macros,
            patch("tool.find_compiler.validation.run_command", side_effect=run),
            patch("tool.find_compiler.validation.executable_architecture", return_value="x64"),
            patch("tool.find_compiler.validation.stage_runtime"),
        ):
            result = validate(candidates[0], "x64")
        self.assertEqual(result.status, "available")
        self.assertEqual((result.c, result.cxx), (str(c), str(cxx)))
        self.assertEqual(result.compiler_fingerprint, compiler_fingerprint((c, cxx)))
        self.assertEqual([command[0] for command in observed[:4]], [cxx, c, cxx, cxx])
        self.assertEqual(macros.call_args_list[0].args[0], cxx)
