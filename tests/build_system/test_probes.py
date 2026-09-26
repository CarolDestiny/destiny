import json
import os
import unittest

from tests.build_system.support import Workspace
from tool.auto_define_config.errors import ConfigError
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.probes import collect_facts
from tool.build_support.storage import json_text
from tool.auto_define_config.sync import Synchronizer


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        self.addCleanup(self.workspace.close)
        self.workspace.module("define/platform")
        self.inventory = load_inventory(self.workspace.root)
        Synchronizer(self.inventory).apply()
        self.counterpart = self.workspace.root / "tool/auto_define_config/define/platform"
        self.field = {
            "id": "platform.windows",
            "type": "boolean",
            "macro": "DESTINY_DEFINE_CMAKE_PLATFORM_WINDOWS",
            "description": "Windows platform",
        }
        self.declare(self.field)

    def declare(self, *fields):
        (self.counterpart / "fields.json").write_text(
            json_text({"schema_version": 1, "module": "define/platform", "fields": list(fields)}),
            encoding="utf-8",
        )

    def probe(self, code):
        (self.counterpart / "probe.py").write_text(code, encoding="utf-8")

    def test_skeleton_explicitly_reports_unimplemented(self):
        fact = collect_facts(self.inventory)["modules"]["define/platform"]["platform.windows"]
        self.assertEqual(fact["status"], "unimplemented")
        self.assertIsNone(fact["value"])

    def test_real_provider_returns_data_and_context(self):
        self.probe(
            "from tool.auto_define_config.contracts import Observation\n"
            "def probe(context):\n"
            '    return {"platform.windows": Observation.available(context.target["system"] == "Windows", provider="fixture")}\n'
        )
        fact = collect_facts(self.inventory, target={"system": "Windows"})["modules"][
            "define/platform"
        ]["platform.windows"]
        self.assertIs(fact["value"], True)

    def test_hardware_cannot_be_overridden_as_an_option(self):
        with self.assertRaisesRegex(ConfigError, "not declared configurable"):
            collect_facts(self.inventory, options={"platform.windows": True})

    def test_options_do_not_need_probe_implementations(self):
        self.declare(dict(self.field, kind="option", default=False))
        self.probe("def probe(context):\n    return {}\n")
        fact = collect_facts(self.inventory, options={"platform.windows": True})["modules"][
            "define/platform"
        ]["platform.windows"]
        self.assertIs(fact["value"], True)
        self.assertEqual(fact["provider"], "user-option")

    def test_wrong_keys_and_exceptions_are_not_unavailable_hardware(self):
        for code, message in [
            ("def probe(context):\n    return {}\n", "must return exactly"),
            ('def probe(context):\n    raise RuntimeError("bug")\n', "implementation failed"),
            ('print("unexpected")\ndef probe(context):\n    return {}\n', "stdout"),
        ]:
            with self.subTest(message=message):
                self.probe(code)
                with self.assertRaisesRegex(ConfigError, message):
                    collect_facts(self.inventory)

    def test_importing_generated_probe_does_not_create_bytecode(self):
        collect_facts(self.inventory)
        self.assertFalse((self.counterpart / "__pycache__").exists())

    def test_probe_execution_does_not_rely_on_python_bytecode_switch(self):
        import sys
        from unittest.mock import patch

        with patch.object(sys, "dont_write_bytecode", False):
            collect_facts(self.inventory)
        self.assertFalse((self.counterpart / "__pycache__").exists())

    def test_cpu_failure_statuses_survive_collection_and_header_generation(self):
        from unittest.mock import patch
        from tool.auto_define_config.preview import preview_header
        from tool.build_support.process import ProcessFailure

        self.declare(dict(self.field, id="avx2", macro="DESTINY_DEFINE_CMAKE_AVX2"))
        self.probe(
            "from tool.auto_define_config.providers.cpu import cpu_facts\n"
            "def probe(context):\n"
            '    return {"avx2": cpu_facts(context)["avx2"]}\n'
        )
        for failure, status in (
            (ProcessFailure("timeout", "CPU helper timed out"), "timeout"),
            (PermissionError("CPU helper denied"), "denied"),
            (OSError("CPU helper unavailable"), "unavailable"),
        ):
            with (
                self.subTest(status=status),
                patch("tool.auto_define_config.providers.cpu._observe", side_effect=failure),
            ):
                facts = collect_facts(self.inventory, target={"compiler": "fixture"})
                fact = facts["modules"]["define/platform"]["avx2"]
                self.assertEqual(fact["status"], status)
                self.assertIsNone(fact["value"])
                self.assertEqual(fact["reason"], str(failure))
                header = preview_header(self.inventory, "define/platform", facts)
                self.assertIn("#define DESTINY_DEFINE_CMAKE_AVX2 0", header)
                self.assertIn("#define DESTINY_DEFINE_CMAKE_AVX2_AVAILABLE 0", header)
        with patch(
            "tool.auto_define_config.providers.cpu._observe",
            side_effect=RuntimeError("provider bug"),
        ):
            with self.assertRaisesRegex(ConfigError, "implementation failed"):
                collect_facts(self.inventory, target={"compiler": "fixture"})

    def test_malformed_native_cpu_json_is_not_an_unavailable_fact(self):
        from unittest.mock import patch
        from tool.auto_define_config.contracts import ProbeContext
        from tool.auto_define_config.providers.cpu import cpu_facts
        from tool.build_support.process import Result

        compiler = self.workspace.write("fake-compiler", "not executed by this fixture")
        context = ProbeContext(
            self.workspace.root,
            "define/platform",
            (),
            {"compiler": str(compiler), "pointer_bytes": "8"},
        )
        with (
            patch(
                "tool.auto_define_config.providers.cpu.run_command",
                side_effect=[Result(0, "", ""), Result(0, "{broken JSON", "")],
            ),
            patch("tool.auto_define_config.providers.cpu.stage_runtime"),
        ):
            with self.assertRaisesRegex(ConfigError, "malformed JSON"):
                cpu_facts(context)

    @unittest.skipUnless(os.name == "nt", "Windows CPU-helper runtime staging")
    def test_missing_cpu_helper_runtime_is_unavailable_not_a_probe_bug(self):
        from unittest.mock import patch
        from tool.auto_define_config.contracts import ProbeContext
        from tool.auto_define_config.providers.cpu import cpu_facts
        from tool.build_support.errors import BuildError
        from tool.build_support.process import Result

        compiler = self.workspace.write("fake-compiler.exe", "not executed by this fixture")
        context = ProbeContext(
            self.workspace.root,
            "define/platform",
            (),
            {"compiler": str(compiler), "pointer_bytes": "8"},
        )
        with (
            patch(
                "tool.auto_define_config.providers.cpu.run_command", return_value=Result(0, "", "")
            ),
            patch(
                "tool.auto_define_config.providers.cpu.stage_runtime",
                side_effect=BuildError("Required CPU-helper DLL is missing"),
            ),
        ):
            result = cpu_facts(context)
        self.assertTrue(all(value.status == "unavailable" for value in result.values()))
        self.assertTrue(
            all(value.reason == "Required CPU-helper DLL is missing" for value in result.values())
        )
