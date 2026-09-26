import gc
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.build_system.support import Workspace
from tool.auto_define_config.inventory import load_inventory
from tool.auto_define_config.sync import Synchronizer
from tool.find_compiler.model import Toolchain


class GuiSmokeTests(unittest.TestCase):
    def setUp(self):
        try:
            import tkinter as tk

            self.root = tk.Tk()
            self.root.withdraw()
        except Exception as exc:
            self.skipTest(f"Tk display is unavailable: {exc}")
        self.addCleanup(self.close)
        self.w = Workspace()
        self.addCleanup(self.w.close)
        self.application = None

    def wait_tasks(self):
        deadline = time.monotonic() + 10
        while self.application.tasks.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.01)
        self.assertFalse(self.application.tasks.busy)

    def close(self):
        if self.root is None:
            return
        if self.application is not None:
            self.application.tasks.close()
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    self.root.update()
                    if not self.root.tk.call("winfo", "exists", "."):
                        break
                except Exception:
                    break
                time.sleep(0.01)
        else:
            try:
                self.root.destroy()
            except Exception:
                pass
        self.application = None
        self.root = None
        # Tcl objects must be finalized here, not by a later test's worker-thread GC.
        gc.collect()

    def test_compiler_window_renders_results_and_manual_controls(self):
        from tool.find_compiler.gui import CompilerWindow

        self.application = CompilerWindow(self.root, self.w.root)
        item = Toolchain("c", "cxx", "gcc", "16.2.0", "x86", "windows", "i686", (), "available")
        self.application.show_results([item])
        self.root.update_idletasks()
        self.assertIn("GCC x86: available", self.application.summary.get())
        self.application.table.selection_set(item.identity)
        self.application._details()
        self.assertIn("i686", self.application.detail.get("1.0", "end"))
        self.assertEqual(self.application.arch.get(), "x64")

    def test_project_pages_load_and_save_without_rewriting_probe(self):
        from tool.auto_define_config.gui import ConfigWindow

        self.w.module("define/platform")
        inventory = load_inventory(self.w.root)
        service = Synchronizer(inventory)
        service.apply()
        self.application = ConfigWindow(self.root, self.w.root, autoload=False)
        self.application.loaded((inventory, service.inspect()))
        self.application.modules.selection_set("define/platform")
        self.application.select_module()
        self.root.update_idletasks()
        self.application.rules.data["aliases"]["portable"] = True
        self.assertTrue(self.application.has_changes())
        self.application.rules.save()
        self.wait_tasks()
        self.assertFalse(self.application.has_changes())
        self.assertEqual(
            self.application.editor.rules("define/platform").data["aliases"], {"portable": True}
        )
        self.assertEqual(len(self.application.tabs.tabs()), 2)

    def test_visual_condition_editor_updates_readonly_preview(self):
        from tool.auto_define_config.gui_conditions import ConditionDialog

        dialog = ConditionDialog(self.root, True, {"windows": {"type": "boolean", "unit": None}})
        try:
            self.root.update_idletasks()
            dialog.operation.set("REF")
            dialog.reference.set("windows")
            dialog.apply_node()
            self.assertEqual(dialog.model.root, {"ref": "windows"})
            self.assertEqual(str(dialog.preview.cget("state")), "disabled")
            self.assertIn("windows", dialog.preview.get("1.0", "end"))
        finally:
            dialog.window.destroy()

    def test_worker_completion_is_delivered_before_a_new_task_can_start(self):
        import threading
        from tool.build_support.tk_tasks import TaskRunner

        delivered = []
        failures = []
        runner = TaskRunner(self.root, status=lambda text: None, failure=failures.append)
        finished = threading.Event()
        self.assertTrue(
            runner.start(lambda cancel, progress: (finished.set(), "first")[1], delivered.append)
        )
        self.assertTrue(finished.wait(2))
        runner.thread.join(2)
        self.assertTrue(runner.busy)
        self.assertFalse(runner.start(lambda cancel, progress: "second", delivered.append))
        runner._poll()
        self.assertEqual(delivered, ["first"])
        self.assertEqual(failures, [])
        self.assertFalse(runner.busy)
        runner.closing = True
        runner.finished = None

    def test_rule_summary_refreshes_after_editing_selected_alias(self):
        from tool.auto_define_config.gui import ConfigWindow

        self.w.module("define/platform")
        inventory = load_inventory(self.w.root)
        service = Synchronizer(inventory)
        service.apply()
        self.application = ConfigWindow(self.root, self.w.root, autoload=False)
        self.application.loaded((inventory, service.inspect()))
        self.application.modules.selection_set("define/platform")
        self.application.select_module()
        page = self.application.rules
        page.data["aliases"]["portable"] = False
        page.refresh()
        page.aliases.selection_set(0)
        page.summary.set("FALSE")
        page.data["aliases"]["portable"] = True
        page.refresh()
        self.assertEqual(page.summary.get(), "TRUE")
        self.assertEqual(page.aliases.curselection(), (0,))

    def test_dialog_geometry_is_anchored_to_its_owner(self):
        from tool.build_support.tk_layout import show_dialog
        from unittest.mock import Mock

        owner = Mock()
        owner.winfo_viewable.return_value = True
        owner.winfo_rootx.return_value = 2400
        owner.winfo_rooty.return_value = 200
        owner.winfo_width.return_value = 1200
        owner.winfo_height.return_value = 800
        parent = Mock()
        parent.winfo_toplevel.return_value = owner
        window = Mock()
        window.winfo_screenwidth.return_value = 1920
        window.winfo_screenheight.return_value = 1080
        show_dialog(window, parent, width=800, height=500)
        window.geometry.assert_called_once_with("800x500+2600+350")
        window.transient.assert_called_once_with(owner)
        window.grab_set.assert_called_once()

    def test_new_compiler_scan_replaces_stale_availability(self):
        from dataclasses import replace
        from tool.find_compiler.gui import CompilerWindow

        self.application = CompilerWindow(self.root, self.w.root)
        first = Toolchain("c", "cxx", "gcc", "16.1.0", "x64", "windows", "x86_64", (), "available")
        self.application.show_results([first])
        self.assertIn("GCC x86: unchecked", self.application.summary.get())
        changed = replace(
            first, version="16.2.0", status="unavailable", phase="link", reason="broken"
        )
        self.application.show_results([changed])
        self.assertEqual(len(self.application.results), 1)
        self.assertNotIn(first.identity, self.application.results)
        self.application.show_results([], scanned=True)
        self.assertEqual(self.application.results, {})
        self.assertIn("GCC x64: not-found", self.application.summary.get())

    def test_saving_uses_a_snapshot_and_runs_validation_off_the_tk_thread(self):
        import threading
        from tool.auto_define_config.gui import ConfigWindow

        self.w.module("define/platform")
        inventory = load_inventory(self.w.root)
        service = Synchronizer(inventory)
        service.apply()
        self.application = ConfigWindow(self.root, self.w.root, autoload=False)
        self.application.loaded((inventory, service.inspect()))
        self.application.modules.selection_set("define/platform")
        self.application.select_module()
        page = self.application.rules
        page.data["aliases"]["portable"] = True
        original = self.application.editor.save_rules
        observed = []

        def save(document, data, *, cancel):
            observed.append(threading.get_ident())
            original(document, data, cancel=cancel)

        with patch.object(self.application.editor, "save_rules", side_effect=save):
            page.save()
            self.wait_tasks()
        self.assertNotEqual(observed, [threading.get_ident()])
        self.assertEqual(page.document.data["aliases"], {"portable": True})
        self.assertFalse(self.application.has_changes())

    def test_selected_cmake_reaches_reload_save_selection_and_probe_preview(self):
        import json
        import shutil
        from tool.auto_define_config.gui import ConfigWindow
        from tool.auto_define_config.preview import preview_header, preview_selection
        from tool.build_support.process import run_command

        self.w.module("define/options")
        inventory = load_inventory(self.w.root)
        Synchronizer(inventory).apply()
        cmake = str(Path(shutil.which("cmake")).absolute())
        self.application = ConfigWindow(self.root, self.w.root, cmake=cmake, autoload=False)
        with patch("tool.auto_define_config.gui.load_inventory", wraps=load_inventory) as load:
            self.application.reload(False)
            self.wait_tasks()
        self.assertEqual(load.call_args.kwargs["cmake"], cmake)
        self.assertEqual(self.application.editor.cmake, cmake)
        self.application.modules.selection_set("define/options")
        self.application.select_module()
        facts = self.w.write("facts.json", json.dumps({"schema_version": 1, "modules": {}}))
        with patch(
            "tool.auto_define_config.gui.preview_selection", wraps=preview_selection
        ) as selection:
            self.application.preview_selection(facts, self.application.rules.data)
            self.wait_tasks()
        self.assertEqual(selection.call_args.kwargs["cmake"], cmake)
        with (
            patch("tool.auto_define_config.gui_probes.run_command", wraps=run_command) as run,
            patch(
                "tool.auto_define_config.gui_probes.preview_header", wraps=preview_header
            ) as header,
        ):
            self.application.probes.run()
            self.wait_tasks()
        self.assertEqual(header.call_args.kwargs["cmake"], cmake)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--cmake") + 1], cmake)

    def test_close_releases_tk_variables_on_the_owning_thread(self):
        import gc
        import weakref
        from tool.find_compiler.gui import CompilerWindow

        self.application = CompilerWindow(self.root, self.w.root)
        variable = weakref.ref(self.application.summary)
        self.close()
        gc.collect()
        self.assertIsNone(
            variable(), "Destroyed Tk variables must not await collection by a later worker"
        )
