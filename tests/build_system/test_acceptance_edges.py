"""Acceptance-level edge cases missing from the initial happy-path matrix."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from tests.build_system.support import ROOT, Workspace
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.sync import Synchronizer
from tool.find_compiler.model import Candidate
from tool.find_compiler.validation import validate


class AcceptanceEdgeTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace(framework=True)
        self.addCleanup(self.w.close)

    def test_category_switches_are_independent_and_gtest_does_not_raise_library_standard(self):
        w = self.w
        shutil.copytree(ROOT / "thirdLib/googletest", w.root / "thirdLib/googletest")
        w.module("core/categories", "destiny_add_module(CXX_STANDARD 11)")
        w.write(
            "source/core/categories/src/library.cpp",
            'static_assert(__cplusplus == 201103L, "library minimum leaked");\nint answer() { return 42; }\n',
        )
        w.write(
            "source/core/categories/demo/example.cpp",
            "int answer();\nint main() { return answer() == 42 ? 0 : 1; }\n",
        )
        w.write("source/core/categories/bench/measure.cpp", "int main() { return 0; }\n")
        w.write(
            "source/core/categories/test/check.cpp",
            "#include <gtest/gtest.h>\nstatic_assert(__cplusplus >= 201703L);\nTEST(Standard, RaisedOnlyHere) { EXPECT_TRUE(true); }\n",
        )
        for disabled in (None, "TESTS", "BENCHMARKS", "DEMOS", "ALL"):
            options = [
                f"-DDESTINY_BUILD_{name}={'OFF' if disabled in (name, 'ALL') else 'ON'}"
                for name in ("TESTS", "BENCHMARKS", "DEMOS")
            ]
            with self.subTest(disabled=disabled):
                w.configure(*options)
                w.run("cmake", "--build", str(w.root / "out"), "--parallel", "4")
                data = json.loads((w.root / "out/reports/source-selection-Debug.json").read_text())
                actual = {item["category"] for item in data["programs"]}
                expected = {
                    category
                    for category, option in (
                        ("test", "TESTS"),
                        ("bench", "BENCHMARKS"),
                        ("demo", "DEMOS"),
                    )
                    if disabled not in (option, "ALL")
                }
                self.assertEqual(actual, expected)
                commands = json.loads((w.root / "out/compile_commands.json").read_text())
                library = next(
                    item["command"] for item in commands if item["file"].endswith("library.cpp")
                )
                self.assertIn("-std=c++11", library)

    def test_removed_define_module_cannot_leave_live_generated_macros(self):
        w = self.w
        registration = w.module("define/removed", "destiny_add_module(INTERFACE CXX_STANDARD 17)")
        service = Synchronizer(load_inventory(w.root))
        service.apply()
        w.write(
            "tool/auto_define_config/define/removed/fields.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "module": "define/removed",
                    "fields": [
                        {
                            "id": "removed",
                            "type": "boolean",
                            "macro": "DESTINY_DEFINE_CMAKE_REMOVED",
                            "description": "Temporary field",
                            "kind": "option",
                            "default": True,
                        }
                    ],
                }
            ),
        )
        w.configure()
        generated = next((w.root / "out/generated/config").rglob("cmake_config.hpp"))
        maintained = w.root / "tool/auto_define_config/define/removed/probe.py"
        before = maintained.read_bytes()
        registration.unlink()
        w.run("cmake", "--build", str(w.root / "out"))
        self.assertFalse(generated.exists())
        self.assertEqual(maintained.read_bytes(), before)
        self.assertEqual(
            json.loads((w.root / "out/generated/facts.json").read_text())["modules"], {}
        )

    def test_generated_header_collision_and_unknown_standard_fail_early(self):
        w = self.w
        registration = w.module("define/config", "destiny_add_module(CXX_STANDARD 17)")
        Synchronizer(load_inventory(w.root)).apply()
        collision = w.write("source/define/config/include/cmake_config.hpp", "#pragma once\n")
        result = w.configure(ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("collides", result.stderr)
        collision.unlink()
        registration.write_text("destiny_add_module(CXX_STANDARD 27)\n")
        result = w.configure(ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported C++ standard", result.stderr)

    def test_macro_changes_trigger_reconfigure_without_touching_maintained_files(self):
        w = self.w
        w.module("define/options", "destiny_add_module(CXX_STANDARD 17)")
        Synchronizer(load_inventory(w.root)).apply()
        w.write(
            "tool/auto_define_config/define/options/fields.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "module": "define/options",
                    "fields": [
                        {
                            "id": "enabled",
                            "type": "boolean",
                            "macro": "DESTINY_DEFINE_CMAKE_ENABLED",
                            "description": "Enabled",
                            "kind": "option",
                            "default": False,
                        }
                    ],
                }
            ),
        )
        w.module(
            "iso/choice",
            "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PUBLIC define/options)",
        )
        w.write(
            "source/iso/choice/src/value_while_enabled.cpp",
            "#include <destiny/define/options/cmake_config.hpp>\nstatic_assert(DESTINY_DEFINE_CMAKE_ENABLED == 1);\n",
        )
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        report = json.loads((w.root / "out/reports/source-selection-Debug.json").read_text())
        self.assertFalse(
            report["modules"]["iso/choice"]["sources"]["src/value_while_enabled.cpp"]["selected"]
        )
        w.write("cache/auto_define_config/options.json", '{"enabled":true}\n')
        w.run("cmake", "--build", str(w.root / "out"))
        report = json.loads((w.root / "out/reports/source-selection-Debug.json").read_text())
        self.assertTrue(
            report["modules"]["iso/choice"]["sources"]["src/value_while_enabled.cpp"]["selected"]
        )
        (w.root / "cache/auto_define_config/options.json").unlink()
        w.run("cmake", "--build", str(w.root / "out"))
        report = json.loads((w.root / "out/reports/source-selection-Debug.json").read_text())
        self.assertFalse(
            report["modules"]["iso/choice"]["sources"]["src/value_while_enabled.cpp"]["selected"]
        )
        for directory in ("source", "tool"):
            self.assertFalse(list((w.root / directory).rglob("__pycache__")))

    def test_macos_32bit_validation_reports_unsupported_without_faking_a_build(self):
        definitions = {
            "__clang__": "1",
            "__clang_major__": "18",
            "__clang_minor__": "0",
            "__clang_patchlevel__": "0",
            "__x86_64__": "1",
        }
        with (
            patch("tool.find_compiler.validation.platform.system", return_value="Darwin"),
            patch("tool.find_compiler.validation.macros", return_value=definitions),
            patch("tool.find_compiler.validation.run_command") as execute,
        ):
            result = validate(Candidate(self.w.root / "clang", self.w.root / "clang++"), "x86")
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.phase, "architecture")
        self.assertIn("32-bit", result.reason)
        execute.assert_not_called()

    def test_vendored_googletest_matches_every_recorded_source_hash_and_license(self):
        provenance = json.loads((ROOT / "thirdLib/googletest.provenance.json").read_text())
        self.assertEqual(provenance["commit"], "063de7e9578f82b369302001269680b4b1553359")
        source = ROOT / "thirdLib/googletest"
        actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
        self.assertEqual(actual, set(provenance["files_sha256"]))
        for relative, expected in provenance["files_sha256"].items():
            self.assertEqual(
                hashlib.sha256((source / relative).read_bytes()).hexdigest(), expected, relative
            )
        self.assertTrue((ROOT / "thirdLib" / provenance["license_file"]).is_file())
        self.assertFalse((source / ".git").exists())

    def test_ordinary_header_and_source_edits_rebuild_their_consumers(self):
        w = self.w
        w.module("core/edits", "destiny_add_module(CXX_STANDARD 17)")
        header = w.write(
            "source/core/edits/include/value.hpp",
            "#pragma once\nconstexpr int value = 7;\nint answer();\n",
        )
        source = w.write(
            "source/core/edits/src/value.cpp",
            "#include <destiny/core/edits/value.hpp>\nint answer() { return value * 2; }\n",
        )
        w.write(
            "source/core/edits/demo/show.cpp",
            "#include <destiny/core/edits/value.hpp>\n#include <iostream>\nint main() { std::cout << answer(); }\n",
        )
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        report = json.loads((w.root / "out/reports/source-selection-Debug.json").read_text())
        executable = report["programs"][0]["executable"]
        self.assertEqual(w.run(executable).stdout, "14")
        forwarding = next((w.root / "out/generated/include").rglob("value.hpp"))
        stamp = forwarding.stat().st_mtime_ns
        header.write_text(header.read_text().replace("value = 7", "value = 11"))
        w.run("cmake", "--build", str(w.root / "out"))
        self.assertEqual(w.run(executable).stdout, "22")
        source.write_text(source.read_text().replace("value * 2", "value * 3"))
        w.run("cmake", "--build", str(w.root / "out"))
        self.assertEqual(w.run(executable).stdout, "33")
        self.assertEqual(forwarding.stat().st_mtime_ns, stamp)

    def test_compile_failure_cannot_choose_a_fallback_or_print_completion_summary(self):
        w = self.w
        w.module("core/required", "destiny_add_module(CXX_STANDARD 17)")
        w.write(
            "source/core/required/src/fast.cpp",
            "#error Selected implementation deliberately fails\n",
        )
        w.write("source/core/required/src/fallback.cpp", "int fallback() { return 0; }\n")
        w.write(
            "source/core/required/source_rules.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "aliases": {},
                    "groups": [
                        {
                            "name": "backend",
                            "candidates": [
                                {"name": "fast", "when": True, "sources": ["src/fast.cpp"]},
                                {"name": "fallback", "when": True, "sources": ["src/fallback.cpp"]},
                            ],
                        }
                    ],
                }
            ),
        )
        w.configure()
        selected_path = w.root / "out/reports/source-selection-Debug.json"
        before = selected_path.read_bytes()
        self.assertEqual(
            json.loads(before)["modules"]["core/required"]["groups"]["backend"], "fast"
        )
        failed = w.run("cmake", "--build", str(w.root / "out"), "--parallel", "4", ok=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("Selected implementation deliberately fails", failed.stdout + failed.stderr)
        self.assertNotIn("Source selection report", failed.stdout + failed.stderr)
        self.assertEqual(selected_path.read_bytes(), before)
        commands = json.loads((w.root / "out/compile_commands.json").read_text())
        self.assertEqual([Path(item["file"]).name for item in commands], ["fast.cpp"])
