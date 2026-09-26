"""Project configuration GUI. Maintained source editing and build actions stay separate."""

from __future__ import annotations

import copy
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from tool.build_support.storage import json_text
from tool.build_support.tk_tasks import TaskRunner
from tool.build_support.process import check_cancelled, ProcessFailure
from .editor import Document, ProjectEditor
from .errors import ConfigError
from .gui_probes import ProbePage
from .gui_rules import RulesPage
from .inventory import load_inventory
from .preview import preview_selection
from .sync import Synchronizer


class ConfigWindow:
    def __init__(self, root: tk.Tk, project: Path, *, cmake="cmake", autoload=True):
        self.root = root
        self.cmake = cmake
        self.editor = None
        self.module = None
        self.dirty = False
        root.title("auto_define_config")
        root.geometry("1240x840")
        root.minsize(1000, 660)
        self.project = tk.StringVar(value=str(project))
        self.status = tk.StringVar(value="Choose a project and load its module inventory.")
        pane = ttk.Frame(root, padding=12)
        pane.pack(fill="both", expand=True)
        pane.columnconfigure(1, weight=1)
        pane.rowconfigure(1, weight=2)
        pane.rowconfigure(2, weight=1)
        toolbar = ttk.Frame(pane)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="Project root").grid(row=0, column=0, padx=(0, 8))
        ttk.Entry(toolbar, textvariable=self.project).grid(row=0, column=1, sticky="ew")
        actions = [
            ("Browse", self.browse),
            ("Load / check", lambda: self.reload(False)),
            ("Sync missing", lambda: self.reload(True)),
            ("Migrate counterpart", self.rename),
            ("Cancel", self.cancel_task),
        ]
        for index, (label, fn) in enumerate(actions, 2):
            ttk.Button(
                toolbar,
                text=label,
                command=lambda f=fn: f() if f == self.cancel_task else self.guard(f),
            ).grid(row=0, column=index, padx=3)
        self.modules = ttk.Treeview(pane, show="tree", selectmode="browse", height=16)
        self.modules.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.modules.column("#0", width=245)
        self.modules.bind("<<TreeviewSelect>>", self.select_module)
        self.tabs = ttk.Notebook(pane)
        self.tabs.grid(row=1, column=1, sticky="nsew")
        self.rules = RulesPage(self.tabs, self)
        self.probes = ProbePage(self.tabs, self)
        self.tabs.add(self.rules, text="Source Rules")
        self.tabs.add(self.probes, text="Define / Probes")
        self.output = tk.Text(pane, height=12, wrap="none", state="disabled")
        self.output.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=8)
        ttk.Label(pane, textvariable=self.status, wraplength=1150).grid(
            row=3, column=0, columnspan=2, sticky="w"
        )
        self.tasks = TaskRunner(root, status=self.status.set, failure=self.failure)
        root.protocol("WM_DELETE_WINDOW", self.close)
        if autoload:
            root.after(0, lambda: self.reload(False))

    def guard(self, action):
        if self.tasks.busy:
            self.status.set("An operation is running. Cancel it or wait before editing.")
            return
        try:
            return action()
        except (ConfigError, OSError, ValueError) as exc:
            self.failure(exc)

    def failure(self, exc):
        self.status.set(str(exc))
        if isinstance(exc, ProcessFailure) and exc.phase == "cancelled":
            return
        messagebox.showerror("Configuration error", str(exc), parent=self.root)

    def cancel_task(self):
        self.tasks.cancel.set()
        self.status.set("Cancellation requested; waiting for the current operation to stop.")

    def save_page(self, page, kind):
        if page.document is None:
            raise ConfigError("Select a synchronized module first")
        document = page.document
        staged = Document(document.path, copy.deepcopy(document.data), document.revision)
        proposal = copy.deepcopy(page.data)
        save = self.editor.save_fields if kind == "fields" else self.editor.save_rules

        def work(cancel, progress):
            progress("Validating declarations and source references before saving")
            save(staged, proposal, cancel=cancel)
            return staged

        def finished(saved):
            document.data = copy.deepcopy(saved.data)
            document.revision = saved.revision
            self.status.set(
                "Saved configuration. Handwritten probes were preserved; reload CMake to apply changes."
            )

        self.tasks.start(work, finished)

    def has_changes(self):
        return any(
            page.document is not None and page.data != page.document.data
            for page in (self.rules, self.probes)
        )

    def allow_discard(self):
        return not self.has_changes() or messagebox.askyesno(
            "Unsaved changes", "Discard unsaved editor changes?", parent=self.root
        )

    def close(self):
        if self.allow_discard():
            self.tasks.close()

    def browse(self):
        selected = filedialog.askdirectory(parent=self.root, initialdir=self.project.get())
        if selected:
            self.project.set(selected)

    def reload(self, synchronize):
        if not self.allow_discard():
            return
        project = Path(self.project.get())

        def work(cancel, progress):
            progress("Reading the CMake module inventory")
            inventory = load_inventory(project, cmake=self.cmake, cancel=cancel)
            check_cancelled(cancel)
            service = Synchronizer(inventory)
            states = service.apply() if synchronize else service.inspect()
            return inventory, states

        self.tasks.start(work, self.loaded)

    def loaded(self, value):
        inventory, states = value
        self.editor = ProjectEditor(inventory, cmake=self.cmake)
        self.module = None
        self.rules.document = None
        self.rules.data = None
        self.probes.document = None
        self.probes.data = None
        self.probes.refresh()
        self.rules.aliases.delete(0, "end")
        for item in self.rules.groups.get_children():
            self.rules.groups.delete(item)
        self.rules.summary.set("Select a registered module.")
        for item in self.modules.get_children():
            self.modules.delete(item)
        for module in inventory.modules:
            parts = module.path.split("/")
            prefix = ""
            for part in parts:
                name = prefix + "/" + part if prefix else part
                if not self.modules.exists(name):
                    self.modules.insert(prefix, "end", iid=name, text=part, open=True)
                prefix = name
        self.show_output(json_text({"synchronization": [item.to_data() for item in states]}))
        self.status.set(
            f"Loaded {len(inventory.modules)} modules. Sync missing counterparts explicitly; existing code is preserved."
        )

    def select_module(self, event=None):
        chosen = self.modules.selection()
        if not chosen or self.editor is None:
            return
        module = chosen[0]
        if module == self.module or module not in {
            item.path for item in self.editor.inventory.modules
        }:
            return
        if self.tasks.busy or not self.allow_discard():
            if self.module:
                self.modules.selection_set(self.module)
            return

        def load():
            self.module = module
            self.rules.load(module)
            self.probes.load(module)
            self.dirty = False

        self.guard(load)

    def catalogue(self):
        if self.editor is None:
            raise ConfigError("Load the module inventory first")
        return self.editor.catalogue()

    def show_output(self, text):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")
        self.status.set(
            "Operation completed. Preview output is read-only; reload CMake after saved source changes."
        )

    def preview_selection(self, facts, rules):
        inventory = self.editor.inventory
        module = self.module

        def work(cancel, progress):
            progress("Evaluating unsaved rules with the native CMake selector")
            result = preview_selection(
                inventory, module, facts, rules_override=rules, cmake=self.cmake, cancel=cancel
            )
            return (
                "PREVIEW ONLY - supplied facts may be simulated; no build facts were changed.\n"
                + str(facts.resolve())
                + "\n"
                + json_text(result)
            )

        self.tasks.start(work, self.show_output)

    def rename(self):
        if self.editor is None:
            raise ConfigError("Load the new CMake module inventory before migrating")
        if not self.allow_discard():
            return
        old = simpledialog.askstring(
            "Migrate counterpart",
            "Old define/module path (no longer registered):",
            parent=self.root,
        )
        if not old:
            return
        new = simpledialog.askstring(
            "Migrate counterpart", "New registered define/module path:", parent=self.root
        )
        if not new:
            return
        service = self.editor.sync
        proposal = service.rename(old, new, dry_run=True)
        if messagebox.askyesno(
            "Confirm explicit migration",
            json_text(proposal)
            + "\nMove maintained files and update only the declaration module identity?",
            parent=self.root,
        ):
            self.show_output(json_text(service.rename(old, new, dry_run=False)))
            self.reload(False)


def launch(project: Path, *, cmake="cmake"):
    root = tk.Tk()
    ConfigWindow(root, project, cmake=cmake)
    root.mainloop()
