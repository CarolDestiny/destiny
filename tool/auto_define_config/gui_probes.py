"""Define-field editing, local options and read-only observation previews."""

from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk

from tool.build_support.process import run_command
from tool.build_support.storage import json_text
from .errors import ConfigError
from .gui_fields import edit_field
from .preview import preview_header


class ProbePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        self.document = None
        self.data = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(
            self,
            columns=("type", "kind", "macro", "unit"),
            show="tree headings",
            selectmode="browse",
        )
        self.table.heading("#0", text="Field")
        self.table.column("#0", width=210)
        for column, width in (("type", 80), ("kind", 100), ("macro", 400), ("unit", 80)):
            self.table.heading(column, text=column.title())
            self.table.column(column, width=width)
        self.table.grid(row=0, column=0, columnspan=3, sticky="nsew")
        buttons = ttk.Frame(self)
        buttons.grid(row=1, column=0, columnspan=3, sticky="ew", pady=8)
        for label, fn in [
            ("Add field", lambda: self.edit(False)),
            ("Edit field", lambda: self.edit(True)),
            ("Remove field", self.remove),
            ("Save declarations", self.save),
            ("Edit local option", self.option),
            ("Open probe.py", self.open_code),
        ]:
            ttk.Button(buttons, text=label, command=lambda f=fn: self.app.guard(f)).pack(
                side="left", padx=3
            )
        ttk.Label(
            self, text="Compiler context JSON (optional; normally from a build directory)"
        ).grid(row=2, column=0, columnspan=3, sticky="w")
        self.context = tk.StringVar()
        ttk.Entry(self, textvariable=self.context).grid(row=3, column=0, sticky="ew", pady=6)
        ttk.Button(self, text="Browse", command=self.browse_context).grid(row=3, column=1, padx=6)
        ttk.Button(
            self, text="Run probe / preview macros", command=lambda: self.app.guard(self.run)
        ).grid(row=3, column=2)
        ttk.Label(
            self,
            text="Hardware observations are read-only. Field defaults apply only to declared user options.",
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=4)

    def load(self, module):
        if module == "define" or module.startswith("define/"):
            self.document = self.app.editor.fields(module)
            self.data = copy.deepcopy(self.document.data)
        else:
            self.document = None
            self.data = None
        self.refresh()

    def refresh(self):
        for item in self.table.get_children():
            self.table.delete(item)
        if self.data:
            for index, field in enumerate(self.data["fields"]):
                self.table.insert(
                    "",
                    "end",
                    iid=str(index),
                    text=field["id"],
                    values=(
                        field["type"],
                        field.get("kind", "observation"),
                        field["macro"],
                        field.get("unit", ""),
                    ),
                )

    def selected(self):
        choice = self.table.selection()
        if not choice:
            raise ConfigError("Select a field")
        return int(choice[0])

    def edit(self, existing):
        if self.document is None:
            raise ConfigError("Select a synchronized define module")
        index = self.selected() if existing else None
        result = edit_field(self, self.data["fields"][index] if index is not None else None)
        if result is not None:
            if index is None:
                self.data["fields"].append(result)
            else:
                self.data["fields"][index] = result
            self.refresh()

    def remove(self):
        del self.data["fields"][self.selected()]
        self.refresh()

    def save(self):
        self.app.save_page(self, "fields")

    def option(self):
        field = self.data["fields"][self.selected()]
        if field.get("kind", "observation") != "option":
            raise ConfigError("Hardware observations cannot be overridden here")
        options = self.app.editor.options()
        previous = options.data.get(field["id"], field["default"])
        text = simpledialog.askstring(
            "Local option override",
            f'{field["id"]}: JSON value (leave empty to use declared default)',
            initialvalue=json.dumps(previous),
            parent=self,
        )
        if text is None:
            return
        data = copy.deepcopy(options.data)
        if text.strip():
            data[field["id"]] = json.loads(text)
        else:
            data.pop(field["id"], None)
        self.app.editor.save_options(options, data)
        self.app.status.set("Saved local options. Reload CMake to apply them.")

    def open_code(self):
        if self.document is None:
            raise ConfigError("Select a define module")
        path = self.document.path.with_name("probe.py")
        if os.name == "nt":
            try:
                os.startfile(path, "edit")
            except OSError:
                subprocess.Popen(
                    [
                        str(
                            Path(os.environ.get("SystemRoot", r"C:\Windows"))
                            / "System32/notepad.exe"
                        ),
                        str(path),
                    ]
                )
        else:
            subprocess.Popen(
                ["open" if sys.platform == "darwin" else "xdg-open", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def browse_context(self):
        path = filedialog.askopenfilename(
            parent=self, title="Select generated probe-context.json", filetypes=[("JSON", "*.json")]
        )
        if path:
            self.context.set(path)

    def run(self):
        if self.document is None:
            raise ConfigError("Select a define module")
        if self.data != self.document.data:
            raise ConfigError("Save declarations before running their maintained probe")
        module = self.app.module
        context = self.context.get().strip()
        inventory = self.app.editor.inventory
        options = self.app.editor.options().path

        def work(cancel, progress):
            command = [
                sys.executable,
                "-B",
                "-m",
                "tool.auto_define_config",
                "--root",
                str(inventory.root),
                "--cmake",
                self.app.cmake,
                "probe",
                "--module",
                module,
            ]
            if context:
                command += ["--context", context]
            if options.exists():
                command += ["--options", str(options)]
            progress(f"Running probe for {module}; generated results will not be saved as source")
            result = run_command(
                command, cwd=Path(__file__).resolve().parents[2], timeout=60, cancel=cancel
            )
            if result.returncode:
                raise ConfigError(result.stderr or result.stdout)
            facts = json.loads(result.stdout)
            header = preview_header(inventory, module, facts, cmake=self.app.cmake, cancel=cancel)
            return (
                "OBSERVATIONS (read-only)\n"
                + json_text(facts)
                + "\nCMAKE HEADER PREVIEW (not installed)\n"
                + header
            )

        self.app.tasks.start(work, self.app.show_output)
