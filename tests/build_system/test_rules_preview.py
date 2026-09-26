import json
import unittest

from tests.build_system.support import Workspace
from tool.auto_define_config.errors import ConfigError
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.preview import preview_selection
from tool.auto_define_config.rules import load_rules, validate_rules
from tool.auto_define_config.sync import Synchronizer


class RuleStructureTests(unittest.TestCase):
    def test_duplicates_are_rejected_before_cmake_json_normalization(self):
        w = Workspace()
        self.addCleanup(w.close)
        path = w.write(
            "source_rules.json", '{"schema_version":1,"aliases":{"a":true,"a":false},"groups":[]}'
        )
        with self.assertRaisesRegex(ConfigError, "Duplicate JSON member"):
            load_rules(path)

    def test_schema_and_source_paths_are_strict(self):
        for source in ("../escape.cpp", "src/../escape.cpp", "src//name.cpp", "src/a;bad.cpp"):
            rules = {
                "schema_version": 1,
                "aliases": {},
                "groups": [
                    {"name": "g", "candidates": [{"name": "a", "when": True, "sources": [source]}]}
                ],
            }
            with self.subTest(source=source), self.assertRaises(ConfigError):
                validate_rules(rules)
        with self.assertRaises(ConfigError):
            validate_rules({"schema_version": True, "aliases": {}, "groups": []})

    def test_bad_unused_alias_stops_configuration_check(self):
        w = Workspace()
        self.addCleanup(w.close)
        w.module("iso/cpu")
        w.write(
            "source/iso/cpu/source_rules.json",
            json.dumps({"schema_version": 1, "aliases": {"unused": {"any": []}}, "groups": []}),
        )
        with self.assertRaisesRegex(ConfigError, "nonempty"):
            Synchronizer(load_inventory(w.root)).check()

    def test_preview_invokes_the_native_selector_without_rewriting_sources(self):
        w = Workspace()
        self.addCleanup(w.close)
        w.module("iso/cpu")
        w.write("source/iso/cpu/src/cpu_while_fast.cpp", "int cpu;\n")
        rule_file = w.write(
            "source/iso/cpu/source_rules.json",
            json.dumps({"schema_version": 1, "aliases": {"fast": {"ref": "avx2"}}, "groups": []}),
        )
        facts = w.write(
            "facts.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "modules": {
                        "define/cpu": {
                            "avx2": {
                                "type": "boolean",
                                "value": True,
                                "status": "available",
                                "unit": None,
                                "provider": "fixture",
                                "reason": "",
                            }
                        }
                    },
                }
            ),
        )
        before = rule_file.read_bytes()
        result = preview_selection(load_inventory(w.root), "iso/cpu", facts)
        self.assertTrue(result["sources"]["src/cpu_while_fast.cpp"]["selected"])
        self.assertEqual(before, rule_file.read_bytes())
        self.assertFalse((w.root / "tool").exists())
