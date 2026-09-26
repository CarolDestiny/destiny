"""Tk compiler discovery front end; all probe/storage logic lives in headless services."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tool.build_support.errors import BuildError
from tool.build_support.tk_tasks import TaskRunner
from .discovery import discover
from .model import Candidate, Toolchain, combination_summary
from .presets import write_presets
from .validation import validate


class CompilerWindow:
    def __init__(self, root: tk.Tk, project: Path):
        self.root = root
        root.title("Destiny - Find Compiler")
        root.geometry("1120x720")
        root.minsize(800, 560)
        self.project = tk.StringVar(value=str(project))
        self.c = tk.StringVar()
        self.cxx = tk.StringVar()
        self.arch = tk.StringVar(value="x64")
        self.status = tk.StringVar(
            value="Scan installed GCC/Clang compilers or enter a compiler pair manually."
        )
        self.summary = tk.StringVar(
            value="GCC x86: unchecked    GCC x64: unchecked    Clang x86: unchecked    Clang x64: unchecked"
        )
        self.results: dict[str, Toolchain] = {}
        self.scan_complete = False
        pane = ttk.Frame(root, padding=12)
        pane.pack(fill="both", expand=True)
        pane.columnconfigure(1, weight=1)
        ttk.Label(pane, text="Project root").grid(row=0, column=0, sticky="w")
        ttk.Entry(pane, textvariable=self.project).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(pane, text="Browse", command=self._browse_project).grid(row=0, column=2)
        ttk.Label(pane, text="Additional search roots (one per line)").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(12, 2)
        )
        self.roots = tk.Text(pane, height=3, wrap="none")
        self.roots.grid(row=2, column=0, columnspan=3, sticky="ew")
        buttons = ttk.Frame(pane)
        buttons.grid(row=3, column=0, columnspan=3, sticky="ew", pady=8)
        ttk.Button(buttons, text="Scan and validate", command=self.scan).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=lambda: self.tasks.cancel.set()).pack(
            side="left", padx=8
        )
        ttk.Button(buttons, text="Write selected presets", command=self.export).pack(side="right")
        ttk.Label(pane, textvariable=self.summary).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=4
        )
        columns = ("family", "architecture", "version", "status", "compiler")
        self.table = ttk.Treeview(
            pane, columns=columns, show="headings", selectmode="extended", height=12
        )
        for column in columns:
            self.table.heading(column, text=column.title())
            self.table.column(
                column, width=100 if column != "compiler" else 580, stretch=column == "compiler"
            )
        self.table.grid(row=5, column=0, columnspan=3, sticky="nsew")
        pane.rowconfigure(5, weight=1)
        self.table.bind("<<TreeviewSelect>>", self._details)
        manual = ttk.LabelFrame(pane, text="Manual compiler pair", padding=8)
        manual.grid(row=6, column=0, columnspan=3, sticky="ew", pady=8)
        manual.columnconfigure(1, weight=1)
        for row, label, var in ((0, "C compiler", self.c), (1, "C++ compiler", self.cxx)):
            ttk.Label(manual, text=label).grid(row=row, column=0, sticky="w")
            ttk.Entry(manual, textvariable=var).grid(row=row, column=1, sticky="ew", padx=8, pady=2)
            ttk.Button(manual, text="Browse", command=lambda v=var: self._browse_compiler(v)).grid(
                row=row, column=2
            )
        ttk.Combobox(
            manual, textvariable=self.arch, values=("x86", "x64"), state="readonly", width=8
        ).grid(row=2, column=0, pady=4)
        ttk.Button(manual, text="Validate manual pair", command=self.manual).grid(
            row=2, column=1, sticky="w", padx=8
        )
        self.detail = tk.Text(pane, height=5, wrap="word", state="disabled")
        self.detail.grid(row=7, column=0, columnspan=3, sticky="ew")
        ttk.Label(pane, textvariable=self.status, wraplength=1000).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )
        self.tasks = TaskRunner(root, status=self.status.set, failure=self._failure)
        root.protocol("WM_DELETE_WINDOW", self.tasks.close)

    def _browse_project(self):
        selected = filedialog.askdirectory(parent=self.root, initialdir=self.project.get())
        if selected:
            self.project.set(selected)

    def _browse_compiler(self, var):
        selected = filedialog.askopenfilename(parent=self.root, title="Select compiler executable")
        if selected:
            var.set(selected)

    def _failure(self, error):
        self.status.set(str(error))
        messagebox.showerror("Operation failed", str(error), parent=self.root)

    def show_results(self, results, *, scanned=False):
        if scanned:
            self.results.clear()
            self.scan_complete = True
        for result in results:
            # Revalidating a changed executable supersedes the old version at that path.
            for identity, previous in tuple(self.results.items()):
                if (previous.c, previous.cxx, previous.architecture) == (
                    result.c,
                    result.cxx,
                    result.architecture,
                ):
                    del self.results[identity]
            self.results[result.identity] = result
        for item in self.table.get_children():
            self.table.delete(item)
        for identity, item in self.results.items():
            self.table.insert(
                "",
                "end",
                iid=identity,
                values=(item.family, item.architecture, item.version, item.status, item.cxx),
            )
        states = [
            f"{item['family'].upper()} {item['architecture']}: {item['status']}"
            for item in combination_summary(self.results.values(), scan_complete=self.scan_complete)
        ]
        self.summary.set("    ".join(states))
        self.status.set(
            f"Validated {len(self.results)} candidates. Only available selections can be exported."
        )

    def scan(self):
        roots = [
            Path(line.strip()) for line in self.roots.get("1.0", "end").splitlines() if line.strip()
        ]

        def work(cancel, progress):
            results = []
            for candidate in discover(roots, cancel=cancel):
                for architecture in ("x86", "x64"):
                    progress(f"Validating {architecture}: {candidate.cxx}")
                    results.append(validate(candidate, architecture, cancel=cancel))
            return results

        self.tasks.start(work, lambda results: self.show_results(results, scanned=True))

    def manual(self):
        c, cxx = Path(self.c.get()), Path(self.cxx.get())
        arch = self.arch.get()
        if not c.is_file() or not cxx.is_file():
            self._failure(BuildError("Choose existing C and C++ compiler executables."))
            return
        self.tasks.start(
            lambda cancel, progress: [validate(Candidate(c, cxx), arch, cancel=cancel)],
            self.show_results,
        )

    def export(self):
        selected = [self.results[item] for item in self.table.selection()]
        project = Path(self.project.get())
        if not selected or any(item.status != "available" for item in selected):
            self._failure(BuildError("Select at least one available compiler combination."))
            return

        def work(cancel, progress):
            refreshed = []
            for item in selected:
                progress(f"Revalidating {item.cxx} before writing presets")
                current = validate(
                    Candidate(Path(item.c), Path(item.cxx)), item.architecture, cancel=cancel
                )
                if current.status != "available" or current.identity != item.identity:
                    raise BuildError(
                        f"Compiler changed or is no longer usable: {item.cxx}: {current.reason}"
                    )
                refreshed.append(current)
            return write_presets(project, refreshed, cancel=cancel)

        self.tasks.start(
            work,
            lambda path: self.status.set(
                f"Wrote {path}. Reload CMake in CLion to import the presets."
            ),
        )

    def _details(self, event=None):
        selected = self.table.selection()
        if not selected:
            return
        item = self.results[selected[0]]
        text = f'C: {item.c}\nC++: {item.cxx}\nTarget: {item.target}; flags: {" ".join(item.flags) or "(default)"}\n'
        text += f"{item.status}: {item.phase} {item.reason}"
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", text)
        self.detail.configure(state="disabled")


def launch(project: Path):
    root = tk.Tk()
    CompilerWindow(root, project)
    root.mainloop()
