"""Execute the documented extension recipe rather than a separately maintained copy."""

import json
from pathlib import Path
import re
import sys
import unittest

from tests.build_system.support import ROOT, Workspace
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.sync import Synchronizer


class ExtensionRecipeTests(unittest.TestCase):
    def test_documented_files_build_probe_select_and_run_from_the_project_root(self):
        text = (ROOT / "agent/build/EXTENDING.md").read_text(encoding="utf-8")
        blocks = re.findall(r"File: `([^`]+)`\n\n```[^\n]*\n(.*?)```", text, re.S)
        self.assertEqual(len(blocks), 9)
        self.assertEqual(len(dict(blocks)), len(blocks))
        w = Workspace(framework=True)
        self.addCleanup(w.close)
        registration = "source/define/memory/CMakeLists.txt"
        w.write(registration, dict(blocks)[registration])
        created = Synchronizer(load_inventory(w.root)).apply()
        self.assertEqual(len(created), 2)
        self.assertTrue(all(item.status == "created" for item in created))
        for path, content in blocks:
            self.assertTrue((w.root / path).resolve().is_relative_to(w.root.resolve()))
            w.write(path, content)
        self.assertTrue(
            all(item.status == "unchanged" for item in Synchronizer(load_inventory(w.root)).apply())
        )
        w.run(sys.executable, "-B", "-m", "tool.auto_define_config", "check")
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        report = json.loads((w.root / "out/reports/source-selection-Debug.json").read_text())
        facts = json.loads((w.root / "out/generated/facts.json").read_text())
        winner = report["modules"]["iso/buffer"]["groups"]["buffer_strategy"]
        executable = report["programs"][0]["executable"]
        result = w.run("cmake", "-E", "chdir", str(w.root), executable, cwd=w.root / "out")
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], winner)
        self.assertEqual(Path(lines[1]).resolve(), w.root.resolve())
        header = next((w.root / "out/generated/config").rglob("cmake_config.hpp")).read_text()
        memory = facts["modules"]["define/memory"]["memory.total_bytes"]
        if memory["status"] == "available":
            self.assertIn(
                "#define DESTINY_DEFINE_CMAKE_MEMORY_TOTAL_BYTES " + memory["value"], header
            )
        w.write("cache/auto_define_config/options.json", '{"fast_buffers": false}\n')
        w.run("cmake", "--build", str(w.root / "out"))
        result = w.run("cmake", "-E", "chdir", str(w.root), executable, cwd=w.root / "out")
        self.assertEqual(result.stdout.splitlines()[0], "small")
