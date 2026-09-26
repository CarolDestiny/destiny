"""Context routing, executable identity and cancellation behind both GUIs."""

from dataclasses import replace
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.build_system.support import Workspace
from tests.build_system.test_compiler_tools import chain
from tool.auto_define_config.__main__ import main
from tool.auto_define_config.editor import ProjectEditor
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.sync import Synchronizer
from tool.build_support.compiler import compiler_fingerprint
from tool.build_support.errors import BuildError
from tool.build_support.process import ProcessFailure
from tool.build_support.tk_tasks import TaskRunner
from tool.find_compiler.discovery import discover
from tool.find_compiler.model import Toolchain
from tool.find_compiler.presets import write_presets


class ToolContextTests(unittest.TestCase):
    def setUp(self):
        self.w = Workspace()
        self.addCleanup(self.w.close)

    def test_cli_gui_entrypoint_keeps_explicit_cmake_without_loading_tk(self):
        launcher = Mock()
        with patch.dict(
            sys.modules, {"tool.auto_define_config.gui": SimpleNamespace(launch=launcher)}
        ):
            result = main(["--root", str(self.w.root), "--cmake", "custom cmake", "gui"])
        self.assertEqual(result, 0)
        launcher.assert_called_once_with(self.w.root, cmake="custom cmake")

    def test_editor_uses_selected_cmake_for_both_semantic_save_paths(self):
        self.w.module("define/options")
        inventory = load_inventory(self.w.root)
        Synchronizer(inventory).apply()
        editor = ProjectEditor(inventory, cmake="custom cmake")
        with patch("tool.auto_define_config.editor.validate_module_rules") as validate:
            fields = editor.fields("define/options")
            editor.save_fields(fields, fields.data)
            rules = editor.rules("define/options")
            editor.save_rules(rules, rules.data)
        self.assertEqual(validate.call_count, 2)
        self.assertTrue(
            all(call.kwargs["cmake"] == "custom cmake" for call in validate.call_args_list)
        )

    def test_same_version_driver_replacement_gets_a_new_preset_directory(self):
        w = self.w
        w.write(
            "CMakePresets.json",
            '{"version":6,"configurePresets":[{"name":"destiny-base","hidden":true}]}',
        )
        c = w.write("compiler/bin/gcc.exe", "c driver 1")
        cxx = w.write("compiler/bin/g++.exe", "cxx driver 1")
        ninja = w.write("ninja.exe", "fixture")
        old = replace(
            chain(), c=str(c), cxx=str(cxx), compiler_fingerprint=compiler_fingerprint((c, cxx))
        )
        output = write_presets(w.root, [old], ninja=ninja)
        initial = output.read_bytes()
        first = json.loads(initial)["configurePresets"][0]["binaryDir"]
        cxx.write_text("cxx driver 2")
        with self.assertRaisesRegex(BuildError, "changed since validation"):
            write_presets(w.root, [old], ninja=ninja)
        self.assertEqual(output.read_bytes(), initial)
        new = replace(old, compiler_fingerprint=compiler_fingerprint((c, cxx)))
        self.assertNotEqual(new.identity, old.identity)
        write_presets(w.root, [new], ninja=ninja)
        entries = json.loads(output.read_text())["configurePresets"]
        self.assertNotEqual(entries[-2]["binaryDir"], first)
        self.assertEqual(Toolchain.from_data(json.loads(json.dumps(new.to_data()))), new)
        with self.assertRaisesRegex(BuildError, "no executable fingerprint"):
            write_presets(w.root, [replace(new, compiler_fingerprint="")], ninja=ninja)

    def test_discovery_and_fingerprinting_respect_cancellation(self):
        event = threading.Event()
        driver = self.w.write("bin/g++.exe", "fixture")
        self.w.write("bin/gcc.exe", "fixture")
        real_iterdir = Path.iterdir

        def entries(path):
            for entry in real_iterdir(path):
                event.set()
                yield entry

        with patch.object(Path, "iterdir", entries):
            with self.assertRaises(ProcessFailure) as caught:
                discover([self.w.root], include_defaults=False, cancel=event)
        self.assertEqual(caught.exception.phase, "cancelled")
        with self.assertRaises(ProcessFailure):
            compiler_fingerprint((driver,), event)

    def test_completion_callback_failure_does_not_stop_worker_polling(self):
        widget = Mock()
        errors = []
        runner = TaskRunner(widget, status=lambda message: None, failure=errors.append)
        failed = Mock(side_effect=ValueError("presentation failure"))
        self.assertTrue(runner.start(lambda cancel, progress: "value", failed))
        runner.thread.join(3)
        runner._poll()
        self.assertEqual(str(errors[0]), "presentation failure")
        self.assertFalse(runner.busy)
        delivered = []
        self.assertTrue(runner.start(lambda cancel, progress: "next", delivered.append))
        runner.thread.join(3)
        runner._poll()
        self.assertEqual(delivered, ["next"])
        self.assertGreaterEqual(widget.after.call_count, 3)

    def test_preset_export_ignores_unselected_failed_candidates_without_fingerprints(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        from tool.find_compiler.__main__ import main as compiler_main, _report

        available = replace(chain(), compiler_fingerprint="a" * 64)
        failed = replace(
            chain(architecture="x86"), status="unavailable", phase="identity", reason="No driver"
        )
        report = self.w.write(
            "scan.json", json.dumps(_report([failed, available], scan_complete=True))
        )
        with (
            patch("tool.find_compiler.__main__.validate", return_value=available),
            patch(
                "tool.find_compiler.__main__.write_presets",
                return_value=self.w.root / "CMakeUserPresets.json",
            ) as write,
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            result = compiler_main(
                [
                    "write-presets",
                    "--input",
                    str(report),
                    "--project",
                    str(self.w.root),
                    "--select",
                    available.identity,
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(write.call_args.args[1], [available])
