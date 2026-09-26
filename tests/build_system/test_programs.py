import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

from tests.build_system.support import ROOT, Workspace
from tool.auto_define_config.errors import ConfigError
from tool.auto_define_config.inventory import load_inventory


class ProgramTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace(framework=True)
        self.addCleanup(self.w.close)

    def test_explicit_multifile_excludes_helpers_and_propagates_additional_dependency(self):
        w = self.w
        w.module("iso/extra", "destiny_add_module(CXX_STANDARD 20)")
        w.write(
            "source/iso/extra/include/value.hpp", "#pragma once\ninline constexpr int value = 9;\n"
        )
        w.module(
            "core/app",
            "destiny_add_module(CXX_STANDARD 17)\n"
            "destiny_add_program(demo combined SOURCES demo/main.cpp demo/helper.cpp DEPENDS iso/extra)",
        )
        w.write(
            "source/core/app/demo/main.cpp",
            "#include <destiny/iso/extra/value.hpp>\nstatic_assert(__cplusplus >= 202002L);\nint helper();\nint main() { return helper() == value ? 0 : 1; }\n",
        )
        w.write("source/core/app/demo/helper.cpp", "int helper() { return 9; }\n")
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        suffix = ".exe" if os.name == "nt" else ""
        directory = w.root / "out/core/app/demo"
        self.assertTrue((directory / ("combined" + suffix)).is_file())
        self.assertFalse((directory / ("helper" + suffix)).exists())
        self.assertFalse((directory / ("main" + suffix)).exists())
        w.run(str(directory / ("combined" + suffix)))
        data = json.loads((w.root / "out/generated/modules.json").read_text())
        module = next(m for m in data["modules"] if m["path"] == "core/app")
        self.assertEqual(module["programs"][0]["effective_cxx_standard"], 20)

    def test_invalid_program_edges_and_sources_fail_in_shared_registry(self):
        w = self.w
        registration = w.module("iso/app")
        w.module("iso/peer")
        w.write("source/iso/app/demo/main.cpp", "int main() {}\n")
        for statement in (
            "destiny_add_program(demo app SOURCES demo/main.cpp DEPENDS iso/peer)",
            "destiny_add_program(demo app SOURCES demo/missing.cpp)",
            "destiny_add_program(demo app CUSTOM_MAIN SOURCES demo/main.cpp)",
        ):
            with self.subTest(statement=statement):
                registration.write_text("destiny_add_module()\n" + statement + "\n")
                with self.assertRaises(ConfigError):
                    load_inventory(w.root)

    def test_custom_google_test_main_and_multiple_programs(self):
        w = self.w
        shutil.copytree(ROOT / "thirdLib/googletest", w.root / "thirdLib/googletest")
        w.module(
            "iso/tests",
            "destiny_add_module(CXX_STANDARD 17)\n"
            "destiny_add_program(test suite CUSTOM_MAIN SOURCES test/main.cpp test/cases.cpp)",
        )
        w.write(
            "source/iso/tests/test/main.cpp",
            "#include <gtest/gtest.h>\nint main(int argc, char** argv) { ::testing::InitGoogleTest(&argc, argv); return RUN_ALL_TESTS(); }\n",
        )
        w.write(
            "source/iso/tests/test/cases.cpp",
            "#include <gtest/gtest.h>\nTEST(Custom, Works) { EXPECT_EQ(2, 2); }\n",
        )
        w.write(
            "source/iso/tests/test/ordinary.cpp",
            "#include <gtest/gtest.h>\nTEST(Ordinary, Works) { EXPECT_TRUE(true); }\n",
        )
        w.configure("-DDESTINY_BUILD_TESTS=ON")
        w.run("cmake", "--build", str(w.root / "out"), "--parallel", "4")
        result = w.run("ctest", "--test-dir", str(w.root / "out"), "--output-on-failure")
        self.assertIn("100% tests passed", result.stdout)
        self.assertIn("Custom.Works", result.stdout)
        self.assertIn("Ordinary.Works", result.stdout)
        self.assertIn("2/2", result.stdout)

    @unittest.skipUnless(os.name == "nt", "Windows-only executable runtime staging")
    def test_program_starts_with_no_compiler_directory_on_path(self):
        w = self.w
        w.module("iso/program", "destiny_add_module(CXX_STANDARD 17)")
        w.write(
            "source/iso/program/demo/main.cpp",
            "#include <iostream>\n#include <string>\nint main() { std::string value(256, 'x'); std::cout << value.size(); }\n",
        )
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        directory = w.root / "out/iso/program/demo"
        receipt = json.loads((directory / ".destiny-runtime-main.exe.json").read_text())
        self.assertGreater(len(receipt["files"]), 0)
        self.assertTrue(all((directory / name).exists() for name in receipt["files"]))
        environment = os.environ.copy()
        environment["PATH"] = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32")
        result = subprocess.run(
            [str(directory / "main.exe")],
            cwd=w.root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "256")
