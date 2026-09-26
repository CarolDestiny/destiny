import json
import unittest

from tests.build_system.support import ROOT, Workspace


def fact(value, type="boolean", status="available", unit=None):
    return {
        "type": type,
        "value": value,
        "status": status,
        "unit": unit,
        "reason": "access denied" if status != "available" else "",
        "provider": "fixture",
    }


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace()
        self.addCleanup(self.w.close)
        self.module = self.w.root / "module"
        self.facts = {
            "windows": fact(True),
            "avx2": fact(True),
            "avx512f": fact(True),
            "cpuIntel": fact(None, status="denied"),
            "memory.bytes": fact("9007199254740993", type="integer", unit="bytes"),
        }

    def source(self, path):
        self.w.write(f"module/{path}", "// Selection fixture, not compiled.\n")

    def select(self, aliases=None, groups=None, ok=True):
        rules = {"schema_version": 1, "aliases": aliases or {}, "groups": groups or []}
        self.w.write("module/source_rules.json", json.dumps(rules))
        facts = self.w.write(
            "facts.json",
            json.dumps({"schema_version": 1, "modules": {"define/fixture": self.facts}}),
        )
        output = self.w.root / "selection.json"
        result = self.w.run(
            "cmake",
            f"-DDESTINY_MODULE_ROOT={self.module.as_posix()}",
            f"-DDESTINY_FACTS={facts.as_posix()}",
            f"-DDESTINY_OUTPUT={output.as_posix()}",
            "-P",
            str(ROOT / "cmake/scripts/SelectSources.cmake"),
            ok=ok,
        )
        return json.loads(output.read_text()) if ok else result

    def test_ordered_multifile_group_and_independent_source(self):
        for name in (
            "base.cpp",
            "a_while_wide.cpp",
            "b_while_wide.cpp",
            "c_while_narrow.cpp",
            "fallback.cpp",
        ):
            self.source("src/" + name)
        result = self.select(
            aliases={
                "wide": {"all": [{"ref": "windows"}, {"ref": "avx512f"}]},
                "narrow": {"ref": "avx2"},
            },
            groups=[
                {
                    "name": "cpu",
                    "candidates": [
                        {
                            "name": "wide",
                            "when": {"ref": "wide"},
                            "sources": ["src/a_while_wide.cpp", "src/b_while_wide.cpp"],
                        },
                        {
                            "name": "narrow",
                            "when": {"ref": "narrow"},
                            "sources": ["src/c_while_narrow.cpp"],
                        },
                        {"name": "scalar", "when": True, "sources": ["src/fallback.cpp"]},
                    ],
                }
            ],
        )
        self.assertEqual(result["groups"], {"cpu": "wide"})
        self.assertTrue(result["sources"]["src/base.cpp"]["selected"])
        self.assertTrue(result["sources"]["src/b_while_wide.cpp"]["selected"])
        self.assertFalse(result["sources"]["src/c_while_narrow.cpp"]["selected"])
        self.assertIn("Lower preference", result["sources"]["src/fallback.cpp"]["reason"])

    def test_strict_binary_not_and_exact_numeric_comparison(self):
        self.source("src/a_while_notIntel.cpp")
        self.source("src/b_while_large.cpp")
        aliases = {
            "notIntel": {"not": {"ref": "cpuIntel"}},
            "large": {
                "compare": {
                    "field": "memory.bytes",
                    "op": "gt",
                    "value": "9007199254740992",
                    "unit": "bytes",
                }
            },
        }
        result = self.select(aliases=aliases)
        self.assertTrue(all(item["selected"] for item in result["sources"].values()))

    def test_fallback_is_explicit(self):
        self.source("src/fast_while_never.cpp")
        self.source("src/slow.cpp")
        result = self.select(
            aliases={"never": False},
            groups=[
                {
                    "name": "cpu",
                    "candidates": [
                        {"name": "fast", "when": True, "sources": ["src/fast_while_never.cpp"]},
                        {"name": "slow", "when": True, "sources": ["src/slow.cpp"]},
                    ],
                }
            ],
        )
        self.assertEqual(result["groups"]["cpu"], "slow")

    def test_no_platform_is_a_configuration_error(self):
        self.source("src/process.cpp")
        result = self.select(
            groups=[
                {
                    "name": "process",
                    "candidates": [
                        {"name": "platform", "when": False, "sources": ["src/process.cpp"]}
                    ],
                }
            ],
            ok=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No eligible implementation", result.stderr)

    def test_cycles_and_hidden_unknown_references_are_errors(self):
        for aliases, fragment in [
            ({"a": {"ref": "b"}, "b": {"ref": "a"}}, "alias cycle"),
            ({"a": {"any": [True, {"ref": "typo"}]}}, "Unknown condition field"),
        ]:
            with self.subTest(aliases=aliases):
                result = self.select(aliases=aliases, ok=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(fragment, result.stderr)

    def test_duplicate_file_ownership_is_an_error_even_for_inactive_candidate(self):
        self.source("src/shared.cpp")
        result = self.select(
            groups=[
                {
                    "name": "g",
                    "candidates": [
                        {"name": "a", "when": True, "sources": ["src/shared.cpp"]},
                        {"name": "b", "when": False, "sources": ["src/shared.cpp"]},
                    ],
                }
            ],
            ok=False,
        )
        self.assertIn("multiply owned source", result.stderr)

    def test_comparison_type_and_unit_are_checked(self):
        for comparison in [
            {"field": "memory.bytes", "op": "gt", "value": "1"},
            {"field": "windows", "op": "eq", "value": "true"},
            {"field": "memory.bytes", "op": "gt", "value": "9223372036854775808", "unit": "bytes"},
        ]:
            result = self.select(aliases={"check": {"compare": comparison}}, ok=False)
            self.assertNotEqual(result.returncode, 0)

    def test_literal_not_and_unknown_suffix(self):
        self.source("src/a_while_yes.cpp")
        result = self.select(aliases={"yes": {"not": False}})
        self.assertTrue(result["sources"]["src/a_while_yes.cpp"]["selected"])
        result = self.select(ok=False)
        self.assertIn("Unknown condition field", result.stderr)

    def test_negative_integer_boundaries_and_unavailable_negation(self):
        self.source("src/result_while_check.cpp")
        self.facts["number"] = fact("-9223372036854775808", type="integer")
        self.facts["unknown"] = fact(None, type="integer", status="denied")
        result = self.select(
            aliases={
                "check": {
                    "all": [
                        {
                            "compare": {
                                "field": "number",
                                "op": "lt",
                                "value": "-9223372036854775807",
                            }
                        },
                        {"not": {"compare": {"field": "unknown", "op": "ne", "value": "0"}}},
                    ]
                }
            }
        )
        self.assertTrue(result["sources"]["src/result_while_check.cpp"]["selected"])

    def test_string_equality_is_case_sensitive(self):
        self.source("src/result_while_check.cpp")
        self.facts["vendor"] = fact("Intel", type="string")
        result = self.select(
            aliases={"check": {"compare": {"field": "vendor", "op": "eq", "value": "intel"}}}
        )
        self.assertFalse(result["sources"]["src/result_while_check.cpp"]["selected"])
