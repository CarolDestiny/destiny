"""Real configure checks distinguish module minima from global hardware facts."""

import json
import unittest

from tests.build_system.support import Workspace
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.sync import Synchronizer


class CompileContextTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace(framework=True)
        self.addCleanup(self.w.close)

    def contexts(self):
        path = self.w.root / "out/generated/probe-context.json"
        return json.loads(path.read_text())["compilation_contexts"]

    def cache_keys(self):
        return {entry["cache_key"] for entry in self.contexts().values()}

    def test_resolved_module_contexts_are_separate_from_shared_macro_facts(self):
        w = self.w
        w.module("define/base", "destiny_add_module(INTERFACE CXX_STANDARD 20)")
        w.module(
            "iso/private",
            "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PRIVATE define/base)",
        )
        w.write("source/iso/private/src/value.cpp", "int value() { return 7; }\n")
        w.module("iso/modern", "destiny_add_module(CXX_STANDARD 23 PUBLIC_CXX_STANDARD 17)")
        w.write("source/iso/modern/src/value.cpp", "static_assert(__cplusplus > 202002L);\n")
        w.module(
            "core/consumer",
            "destiny_add_module(CXX_STANDARD 17)\ndestiny_depends(PUBLIC iso/modern)",
        )
        Synchronizer(load_inventory(w.root)).apply()
        w.configure()
        w.run("cmake", "--build", str(w.root / "out"))
        contexts = self.contexts()
        self.assertEqual(contexts["iso/private"]["minimum_standard"], 20)
        self.assertEqual(contexts["iso/modern"]["minimum_standard"], 23)
        self.assertEqual(contexts["core/consumer"]["minimum_standard"], 17)
        self.assertEqual(contexts["define/base"], contexts["iso/private"])
        self.assertEqual(len(self.cache_keys()), 3)
        self.assertTrue(
            all(c["standard_available"] and not c["extensions"] for c in contexts.values())
        )
        facts = json.loads((w.root / "out/generated/facts.json").read_text())
        self.assertEqual(facts["compilation_contexts"], contexts)
        self.assertEqual(facts["modules"], {"define/base": {}})
        report = json.loads((w.root / "out/reports/source-selection-Debug.json").read_text())
        for module, context in contexts.items():
            self.assertEqual(report["modules"][module]["compilation_context"], context)

    def test_cache_tracks_flags_configuration_standard_and_compiler_content(self):
        w = self.w
        registration = w.module("core/context", "destiny_add_module(CXX_STANDARD 17)")
        w.write("source/core/context/src/value.cpp", "int value() { return 1; }\n")
        w.configure()
        initial = self.cache_keys()
        data_file = w.root / "out/generated/probe-context.json"
        stamp = data_file.stat().st_mtime_ns
        w.configure()
        self.assertEqual(self.cache_keys(), initial)
        self.assertEqual(data_file.stat().st_mtime_ns, stamp)
        w.configure("-DCMAKE_CXX_FLAGS=-DDESTINY_CONTEXT_FLAG=1")
        flags = self.cache_keys()
        self.assertTrue(flags.isdisjoint(initial))
        w.configure("-DCMAKE_CXX_FLAGS=-DDESTINY_CONTEXT_FLAG=1", "-DCMAKE_BUILD_TYPE=Release")
        release = self.cache_keys()
        self.assertTrue(release.isdisjoint(flags))
        registration.write_text("destiny_add_module(CXX_STANDARD 23)\n")
        w.configure("-DCMAKE_CXX_FLAGS=-DDESTINY_CONTEXT_FLAG=1", "-DCMAKE_BUILD_TYPE=Release")
        self.assertTrue(self.cache_keys().isdisjoint(release))
        context = self.contexts()["core/context"]
        import hashlib
        from pathlib import Path

        compiler = Path(context["CMAKE_CXX_COMPILER"])
        self.assertEqual(
            context["compiler_digest"], hashlib.sha256(compiler.read_bytes()).hexdigest()
        )
        cache = (w.root / "out/CMakeCache.txt").read_text()
        for key in initial | flags | release | self.cache_keys():
            self.assertIn(f"DESTINY_DIALECT_{key}:INTERNAL=1", cache)

    def test_rejected_mode_fails_before_conditional_source_selection(self):
        w = self.w
        w.module("core/rejected", "destiny_add_module(CXX_STANDARD 23)")
        w.write("source/core/rejected/src/rejected_while_unknown.cpp", "#error Never select this\n")
        root = w.root / "CMakeLists.txt"
        root.write_text(
            root.read_text().replace(
                "include(Destiny)",
                'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++2099")\ninclude(Destiny)',
            )
        )
        result = w.configure(ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "C++23 compilation context is unavailable for core/rejected",
            result.stdout + result.stderr,
        )
        self.assertNotIn("Unknown condition field", result.stdout + result.stderr)
        self.assertFalse((w.root / "out/generated/facts.json").exists())

    def test_unadvertised_supported_standard_identifier_is_not_silently_lowered(self):
        w = self.w
        w.module("core/rejected", "destiny_add_module(CXX_STANDARD 23)")
        root = w.root / "CMakeLists.txt"
        root.write_text(
            root.read_text().replace(
                "include(Destiny)",
                "list(REMOVE_ITEM CMAKE_CXX_COMPILE_FEATURES cxx_std_23)\ninclude(Destiny)",
            )
        )
        result = w.configure(ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "cannot provide C++23 required by core/rejected", result.stdout + result.stderr
        )
