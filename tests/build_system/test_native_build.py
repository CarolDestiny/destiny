import json
import os
from pathlib import Path
import unittest

from tests.build_system.support import ROOT, Workspace
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.sync import Synchronizer


class NativeBuildTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace(framework=True)
        self.addCleanup(self.workspace.close)

    def synchronize(self):
        Synchronizer(load_inventory(self.workspace.root)).apply()

    def commands(self):
        data = json.loads((self.workspace.root / "out/compile_commands.json").read_text())
        return {Path(item["file"]).name: item["command"] for item in data}

    def test_mixed_standards_header_mapping_and_private_nonleakage(self):
        w = self.workspace
        w.module("define/base", "destiny_add_module(INTERFACE CXX_STANDARD 17)")
        w.write(
            "source/define/base/include/base.hpp", "#pragma once\ninline constexpr int base = 7;\n"
        )
        w.module(
            "iso/cpu",
            "destiny_add_module(CXX_STANDARD 23 PUBLIC_CXX_STANDARD 20)\ndestiny_depends(PUBLIC define/base)",
        )
        w.write(
            "source/iso/cpu/include/cpu.hpp",
            "#pragma once\n#include <concepts>\n#include <destiny/define/base/base.hpp>\nint cpu();\n",
        )
        w.write(
            "source/iso/cpu/src/cpu.cpp",
            "#include <destiny/iso/cpu/cpu.hpp>\nstatic_assert(__cplusplus > 202002L);\nint cpu() { return base; }\n",
        )
        w.module(
            "core/task", "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PRIVATE iso/cpu)"
        )
        w.write("source/core/task/include/task.hpp", "#pragma once\nint task();\n")
        w.write(
            "source/core/task/src/task.cpp",
            "#include <destiny/core/task/task.hpp>\n#include <destiny/iso/cpu/cpu.hpp>\nstatic_assert(__cplusplus >= 202002L);\nint task() { return cpu(); }\n",
        )
        w.write(
            "source/core/task/demo/task_main.cpp",
            "#include <destiny/core/task/task.hpp>\nint main() { return task() == 7 ? 0 : 1; }\n",
        )
        # Separate C++17 implementation ensures the default C++20 is not imposed globally.
        w.module(
            "iso/plain", "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PUBLIC define/base)"
        )
        w.write("source/iso/plain/include/plain.hpp", "#pragma once\nint plain();\n")
        w.write(
            "source/iso/plain/src/plain.cpp",
            "#include <destiny/define/base/base.hpp>\nstatic_assert(__cplusplus == 201703L);\nint plain() { return base; }\n",
        )
        self.synchronize()
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        commands = self.commands()
        self.assertIn("-std=c++23", commands["cpu.cpp"])
        self.assertIn("-std=c++20", commands["task.cpp"])
        self.assertIn("-std=c++17", commands["plain.cpp"])
        inventory = load_inventory(w.root)
        task = next(m for m in inventory.modules if m.path == "core/task")
        self.assertEqual(task.effective_public_cxx_standard, 17)
        executable = (
            w.root / "out/core/task/demo" / ("task_main.exe" if os.name == "nt" else "task_main")
        )
        w.run(str(executable))
        report = (w.root / "out/reports/source-selection-Debug.txt").read_text()
        self.assertIn("        task\n", report)
        self.assertIn("C++ minimum: 17; effective: 20; public: 17", report)

    def test_source_and_header_add_remove_and_noop(self):
        w = self.workspace
        w.module("iso/plain", "destiny_add_module(CXX_STANDARD 17)")
        header = w.write(
            "source/iso/plain/include/value.hpp", "#pragma once\ninline constexpr int value = 1;\n"
        )
        w.write(
            "source/iso/plain/src/value.cpp",
            "#include <destiny/iso/plain/value.hpp>\nint value_copy() { return value; }\n",
        )
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        forwarding = next((w.root / "out/generated/include").rglob("value.hpp"))
        original_mtime = forwarding.stat().st_mtime_ns
        w.configure()
        self.assertEqual(original_mtime, forwarding.stat().st_mtime_ns)
        new_source = w.write("source/iso/plain/src/extra.cpp", "int extra() { return 5; }\n")
        new_header = w.write("source/iso/plain/include/extra.hpp", "#pragma once\n")
        w.run("cmake", "--build", str(w.root / "out"))
        self.assertIn("extra.cpp", self.commands())
        forwarded_extra = next((w.root / "out/generated/include").rglob("extra.hpp"))
        new_source.unlink()
        new_header.unlink()
        w.run("cmake", "--build", str(w.root / "out"))
        self.assertNotIn("extra.cpp", self.commands())
        self.assertFalse(forwarded_extra.exists())
        self.assertTrue(header.exists())

    def test_missing_probe_fails_without_source_writes(self):
        w = self.workspace
        w.module("define/platform")
        result = w.configure(ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not synchronized", result.stderr)
        self.assertFalse((w.root / "tool/auto_define_config/define").exists())

    def test_enabled_programs_never_run_during_build(self):
        w = self.workspace
        w.module("core/plain", "destiny_add_module(CXX_STANDARD 17)")
        w.write(
            "source/core/plain/demo/run.cpp",
            '#include <fstream>\nint main() { std::ofstream("ran.marker") << "run"; }\n',
        )
        w.write("source/core/plain/bench/run.cpp", "int main() { return 0; }\n")
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        self.assertFalse(list(w.root.rglob("ran.marker")))
        executable = w.root / "out/core/plain/demo" / ("run.exe" if os.name == "nt" else "run")
        w.run("cmake", "-E", "chdir", str(w.root), str(executable))
        self.assertTrue((w.root / "ran.marker").exists())
        w.configure("-DDESTINY_BUILD_DEMOS=OFF", "-DDESTINY_BUILD_BENCHMARKS=OFF")
        report = (w.root / "out/reports/source-selection-Debug.txt").read_text()
        self.assertNotIn("Executable [", report)

    def test_explicit_static_without_sources_fails(self):
        self.workspace.module("iso/empty", "destiny_add_module(STATIC)")
        result = self.workspace.configure(ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("STATIC module has no implementation", result.stderr)

    def test_unknown_condition_is_not_silently_compiled(self):
        self.workspace.module("iso/conditional")
        self.workspace.write(
            "source/iso/conditional/src/example_while_windows.cpp", "int sample;\n"
        )
        result = self.workspace.configure(ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown condition field", result.stderr)

    def test_per_module_facts_generate_macros_and_keep_header_stable(self):
        w = self.workspace
        w.module("define/environment", "destiny_add_module(CXX_STANDARD 17)")
        self.synchronize()
        w.write(
            "tool/auto_define_config/define/environment/fields.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "module": "define/environment",
                    "fields": [
                        {
                            "id": "cpu.intel",
                            "type": "boolean",
                            "macro": "DESTINY_DEFINE_CMAKE_CPU_INTEL",
                            "alias": "DESTINY_DEFINE_CPU_INTEL",
                            "description": "CPU vendor",
                        },
                        {
                            "id": "memory.bytes",
                            "type": "integer",
                            "unit": "bytes",
                            "macro": "DESTINY_DEFINE_CMAKE_MEMORY_BYTES",
                            "description": "Memory capacity",
                        },
                    ],
                }
            ),
        )
        w.write(
            "tool/auto_define_config/define/environment/probe.py",
            "from tool.auto_define_config.contracts import Observation\n"
            "def probe(context):\n"
            '    return {"cpu.intel": Observation.unavailable("denied", status="denied"),\n'
            '            "memory.bytes": Observation.available(9007199254740993, provider="fixture")}\n',
        )
        w.module(
            "iso/macros",
            "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PUBLIC define/environment)",
        )
        w.write(
            "source/iso/macros/src/check.cpp",
            "#include <destiny/define/environment/cmake_config.hpp>\n"
            "static_assert(DESTINY_DEFINE_CPU_INTEL == 0);\n"
            "static_assert(!DESTINY_DEFINE_CPU_INTEL);\n"
            "static_assert(DESTINY_DEFINE_CPU_INTEL_AVAILABLE == 0);\n"
            "static_assert(DESTINY_DEFINE_CMAKE_MEMORY_BYTES == 9007199254740993LL);\n",
        )
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        generated = next((w.root / "out/generated/config").rglob("cmake_config.hpp"))
        before = generated.stat().st_mtime_ns
        w.configure()
        self.assertEqual(before, generated.stat().st_mtime_ns)
        facts = json.loads((w.root / "out/generated/facts.json").read_text())
        self.assertEqual(
            facts["modules"]["define/environment"]["memory.bytes"]["value"], "9007199254740993"
        )

    def test_forwarding_include_paths_with_spaces_and_unicode(self):
        w = self.workspace
        project = w.root / "project with space-\u6d4b\u8bd5"
        project.mkdir()
        for child in list(w.root.iterdir()):
            if child != project:
                child.rename(project / child.name)
        w.root = project
        w.module("iso/plain", "destiny_add_module(CXX_STANDARD 17)")
        w.write(
            "source/iso/plain/include/detail/value.hpp",
            "#pragma once\ninline constexpr int value = 8;\n",
        )
        w.write("source/iso/plain/include/plain.hpp", '#pragma once\n#include "detail/value.hpp"\n')
        w.write(
            "source/iso/plain/src/plain.cpp",
            "#include <destiny/iso/plain/plain.hpp>\nstatic_assert(value == 8);\n",
        )
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))

    def test_private_standard_and_headers_do_not_leak_to_downstream_consumer(self):
        w = self.workspace
        w.write("cmake/DestinyLayers.cmake", "destiny_register_layers(define iso core app)\n")
        w.module("iso/detail", "destiny_add_module(CXX_STANDARD 23)")
        w.write("source/iso/detail/include/detail.hpp", "#pragma once\nint detail();\n")
        w.write(
            "source/iso/detail/src/detail.cpp",
            "static_assert(__cplusplus > 202002L);\nint detail() { return 4; }\n",
        )
        w.module(
            "core/api", "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PRIVATE iso/detail)"
        )
        w.write("source/core/api/include/api.hpp", "#pragma once\nint api();\n")
        w.write(
            "source/core/api/src/api.cpp",
            "#include <destiny/iso/detail/detail.hpp>\nint api() { return detail(); }\n",
        )
        w.module(
            "app/client", "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PUBLIC core/api)"
        )
        w.write(
            "source/app/client/demo/client.cpp",
            "#include <destiny/core/api/api.hpp>\nstatic_assert(__cplusplus == 201703L);\nint main() { return api() == 4 ? 0 : 1; }\n",
        )
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        commands = self.commands()
        self.assertIn("-std=c++23", commands["api.cpp"])
        self.assertIn("-std=c++17", commands["client.cpp"])
        w.write(
            "source/app/client/demo/client.cpp",
            "#include <destiny/iso/detail/detail.hpp>\nint main() { return detail(); }\n",
        )
        result = w.run("cmake", "--build", str(w.root / "out"), ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destiny/iso/detail/detail.hpp", result.stdout + result.stderr)

    def test_rules_select_translation_units_and_reconfigure_without_fallback_compilation(self):
        w = self.workspace
        w.module("iso/selection", "destiny_add_module(CXX_STANDARD 17)")
        w.write("source/iso/selection/src/value_while_fast.cpp", "int answer() { return 3; }\n")
        w.write(
            "source/iso/selection/src/value_while_slow.cpp",
            '#error "An unselected source must never compile"\n',
        )
        rules = {
            "schema_version": 1,
            "aliases": {"fast": True, "slow": True},
            "groups": [
                {
                    "name": "backend",
                    "candidates": [
                        {
                            "name": "fast",
                            "when": {"ref": "fast"},
                            "sources": ["src/value_while_fast.cpp"],
                        },
                        {
                            "name": "slow",
                            "when": {"ref": "slow"},
                            "sources": ["src/value_while_slow.cpp"],
                        },
                    ],
                }
            ],
        }
        rule_file = w.write("source/iso/selection/source_rules.json", json.dumps(rules))
        result = w.configure()
        self.assertIn("Excluded: src/value_while_slow.cpp", result.stdout)
        w.run("cmake", "--build", str(w.root / "out"))
        self.assertNotIn("value_while_slow.cpp", self.commands())
        report = json.loads((w.root / "out/reports/source-selection-Debug.json").read_text())
        self.assertEqual(report["modules"]["iso/selection"]["groups"]["backend"], "fast")
        rules["groups"][0]["candidates"].reverse()
        rule_file.write_text(json.dumps(rules), encoding="utf-8")
        result = w.run("cmake", "--build", str(w.root / "out"), ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("An unselected source must never compile", result.stdout + result.stderr)
        self.assertNotIn("value_while_fast.cpp", self.commands())

    def test_vendored_gtest_pretest_discovery_and_project_root_working_directory(self):
        import shutil

        w = self.workspace
        shutil.copytree(ROOT / "thirdLib/googletest", w.root / "thirdLib/googletest")
        w.module("iso/tests", "destiny_add_module(CXX_STANDARD 17)")
        w.write("root-resource.txt", "root resource")
        w.write(
            "source/iso/tests/test/root.cpp",
            r"""#include <gtest/gtest.h>
#include <filesystem>
#include <fstream>
struct Started {
    Started() { std::ofstream("out/runtime-started.txt", std::ios::app) << std::filesystem::current_path().string() << '\n'; }
};
Started started;
TEST(Runtime, RootResource) {
    EXPECT_TRUE(std::filesystem::exists("root-resource.txt"));
    EXPECT_TRUE(std::filesystem::exists("source/iso/tests/CMakeLists.txt"));
}
""",
        )
        w.configure("-DDESTINY_BUILD_TESTS=ON")
        self.assertFalse((w.root / "out/runtime-started.txt").exists())
        w.run("cmake", "--build", str(w.root / "out"), "--parallel", "4")
        self.assertFalse((w.root / "out/runtime-started.txt").exists())
        result = w.run("ctest", "--test-dir", str(w.root / "out"), "--output-on-failure")
        self.assertIn("100% tests passed", result.stdout)
        marker = (w.root / "out/runtime-started.txt").read_text()
        directories = marker.splitlines()
        self.assertGreaterEqual(len(directories), 2)  # discovery plus execution
        self.assertTrue(all(Path(value).resolve() == w.root.resolve() for value in directories))
        self.assertTrue(list((w.root / "out/reports/test").rglob("*.xml")))
        self.assertEqual(list(w.root.glob("cmake_test_discovery_*.json")), [])
        discovered = w.run("ctest", "--test-dir", str(w.root / "out"), "--show-only=json-v1")
        tests = json.loads(discovered.stdout)["tests"]
        self.assertTrue(tests)
        for test in tests:
            properties = {item["name"]: item["value"] for item in test["properties"]}
            self.assertEqual(Path(properties["WORKING_DIRECTORY"]).resolve(), w.root.resolve())
