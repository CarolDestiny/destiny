"""Module-local aliases and ordered candidate files, without editable expression text."""

from __future__ import annotations
from tool.build_support.tk_layout import show_dialog
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from pathlib import Path
import copy

from .errors import ConfigError
from .expression_tree import expression_text
from .gui_conditions import edit_condition
from .rules import validate_rules


class CandidateDialog:
    def __init__(self, parent, catalogue, aliases, sources, candidate=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Implementation candidate")
        self.window.withdraw()
        self.result = None
        candidate = candidate or {"name": "", "when": True, "sources": []}
        self.condition = copy.deepcopy(candidate["when"])
        self.name = tk.StringVar(value=candidate["name"])
        self.preview = tk.StringVar(value=expression_text(self.condition))
        self.catalogue = catalogue
        self.aliases = aliases
        pane = ttk.Frame(self.window, padding=12)
        pane.pack(fill="both", expand=True)
        pane.columnconfigure(1, weight=1)
        pane.rowconfigure(3, weight=1)
        ttk.Label(pane, text="Candidate name").grid(row=0, column=0, sticky="w")
        ttk.Entry(pane, textvariable=self.name).grid(row=0, column=1, sticky="ew")
        ttk.Label(pane, textvariable=self.preview, wraplength=670).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=8
        )
        ttk.Button(pane, text="Edit condition tree", command=self.edit).grid(
            row=2, column=0, columnspan=2, sticky="w"
        )
        self.sources = tk.Listbox(pane, selectmode="extended", exportselection=False)
        self.sources.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=8)
        for index, source in enumerate(sources):
            self.sources.insert("end", source)
            if source in candidate["sources"]:
                self.sources.selection_set(index)
        ttk.Label(
            pane,
            text="Select every source that belongs to this candidate. Order is set in the group list.",
        ).grid(row=4, column=0, columnspan=2, sticky="w")
        controls = ttk.Frame(pane)
        controls.grid(row=5, column=0, columnspan=2, sticky="e", pady=8)
        ttk.Button(controls, text="Cancel", command=self.window.destroy).pack(side="right")
        ttk.Button(controls, text="Use candidate", command=self.accept).pack(side="right", padx=8)

        show_dialog(self.window, parent, width=730, height=530)

    def edit(self):
        result = edit_condition(self.window, self.condition, self.catalogue, self.aliases)
        if result is not None:
            self.condition = result
            self.preview.set(expression_text(result))

    def accept(self):
        result = {
            "name": self.name.get().strip(),
            "when": self.condition,
            "sources": [self.sources.get(index) for index in self.sources.curselection()],
        }
        try:
            validate_rules(
                {
                    "schema_version": 1,
                    "aliases": {},
                    "groups": [{"name": "validation", "candidates": [result]}],
                }
            )
        except ConfigError as exc:
            messagebox.showerror("Invalid candidate", str(exc), parent=self.window)
            return
        self.result = result
        self.window.destroy()


class RulesPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        self.document = None
        self.data = None
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text="Module-local condition aliases").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Implementation groups (candidate order = priority)").grid(
            row=0, column=1, sticky="w"
        )
        self.aliases = tk.Listbox(self, exportselection=False)
        self.aliases.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self.groups = ttk.Treeview(self, show="tree", selectmode="browse")
        self.groups.grid(row=1, column=1, sticky="nsew")
        left = ttk.Frame(self)
        left.grid(row=2, column=0, sticky="ew", pady=8)
        for label, fn in [
            ("Add", lambda: self.alias(False)),
            ("Edit", lambda: self.alias(True)),
            ("Remove", self.remove_alias),
        ]:
            ttk.Button(left, text=label, command=lambda f=fn: self.app.guard(f)).pack(
                side="left", padx=2
            )
        right = ttk.Frame(self)
        right.grid(row=2, column=1, sticky="ew", pady=8)
        for label, fn in [
            ("Group", self.add_group),
            ("Candidate", lambda: self.candidate(False)),
            ("Edit", lambda: self.candidate(True)),
            ("Remove", self.remove),
            ("Up", lambda: self.move(-1)),
            ("Down", lambda: self.move(1)),
        ]:
            ttk.Button(right, text=label, command=lambda f=fn: self.app.guard(f)).pack(
                side="left", padx=2
            )
        self.summary = tk.StringVar(value="Select a registered module.")
        ttk.Label(self, textvariable=self.summary, wraplength=950).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=6
        )
        controls = ttk.Frame(self)
        controls.grid(row=4, column=0, columnspan=2, sticky="e")
        ttk.Button(controls, text="Save rules", command=lambda: self.app.guard(self.save)).pack(
            side="left", padx=4
        )
        ttk.Button(
            controls,
            text="Preview with selected facts file",
            command=lambda: self.app.guard(self.preview),
        ).pack(side="left")
        self.aliases.bind("<<ListboxSelect>>", self.describe)
        self.groups.bind("<<TreeviewSelect>>", self.describe)

    def load(self, module):
        self.document = self.app.editor.rules(module)
        self.data = copy.deepcopy(self.document.data)
        self.refresh()

    def refresh(self):
        selected = self.aliases.curselection()
        alias = self.aliases.get(selected[0]) if selected else None
        group_selection = self.groups.selection()
        self.aliases.delete(0, "end")
        for name in self.data["aliases"]:
            self.aliases.insert("end", name)
        for item in self.groups.get_children():
            self.groups.delete(item)
        for index, group in enumerate(self.data["groups"]):
            iid = str(index)
            self.groups.insert("", "end", iid=iid, text=group["name"], open=True)
            for ci, candidate in enumerate(group["candidates"]):
                self.groups.insert(
                    iid,
                    "end",
                    iid=f"{index}/{ci}",
                    text=f'{ci+1}. {candidate["name"]}: {expression_text(candidate["when"])}',
                )
        self.summary.set("Select a condition alias or implementation candidate.")
        if alias in self.data["aliases"]:
            self.aliases.selection_set(list(self.data["aliases"]).index(alias))
            self.summary.set(expression_text(self.data["aliases"][alias]))
        elif group_selection and self.groups.exists(group_selection[0]):
            self.groups.selection_set(group_selection[0])
            self.describe()
        self.app.dirty = True

    def alias(self, edit):
        if self.data is None:
            raise ConfigError("Select a module first")
        selected = self.aliases.curselection()
        name = (
            self.aliases.get(selected[0])
            if edit and selected
            else simpledialog.askstring("Local alias", "Alias name:", parent=self)
        )
        if not name:
            return
        if not edit and name in self.data["aliases"]:
            raise ConfigError("Alias already exists")
        value = edit_condition(
            self, self.data["aliases"].get(name, True), self.app.catalogue(), self.data["aliases"]
        )
        if value is not None:
            proposal = copy.deepcopy(self.data)
            proposal["aliases"][name] = value
            validate_rules(proposal)
            self.data = proposal
            self.refresh()

    def remove_alias(self):
        selected = self.aliases.curselection()
        if selected:
            del self.data["aliases"][self.aliases.get(selected[0])]
            self.refresh()

    def selected(self):
        items = self.groups.selection()
        if not items:
            raise ConfigError("Select an implementation group")
        indices = tuple(int(x) for x in items[0].split("/"))
        return indices

    def add_group(self):
        if self.data is None:
            raise ConfigError("Select a module first")
        name = simpledialog.askstring("Implementation group", "Group name:", parent=self)
        if not name:
            return
        if any(g["name"] == name for g in self.data["groups"]):
            raise ConfigError("Group already exists")
        self.data["groups"].append({"name": name, "candidates": []})
        self.refresh()
        self.groups.selection_set(str(len(self.data["groups"]) - 1))

    def candidate(self, edit):
        indices = self.selected()
        group = self.data["groups"][indices[0]]
        current = group["candidates"][indices[1]] if edit and len(indices) == 2 else None
        dialog = CandidateDialog(
            self,
            self.app.catalogue(),
            self.data["aliases"],
            self.app.editor.sources(self.app.module),
            current,
        )
        self.wait_window(dialog.window)
        if dialog.result is not None:
            if current is None:
                group["candidates"].append(dialog.result)
            else:
                group["candidates"][indices[1]] = dialog.result
            self.refresh()

    def remove(self):
        indices = self.selected()
        if len(indices) == 1:
            del self.data["groups"][indices[0]]
        else:
            del self.data["groups"][indices[0]]["candidates"][indices[1]]
        self.refresh()

    def move(self, delta):
        indices = self.selected()
        if len(indices) != 2:
            raise ConfigError("Select a candidate to change priority")
        entries = self.data["groups"][indices[0]]["candidates"]
        index = indices[1]
        target = index + delta
        if 0 <= target < len(entries):
            entries[index], entries[target] = entries[target], entries[index]
            self.refresh()
            self.groups.selection_set(f"{indices[0]}/{target}")

    def describe(self, event=None):
        if event is not None and event.widget == self.aliases and self.aliases.curselection():
            self.summary.set(
                expression_text(
                    self.data["aliases"][self.aliases.get(self.aliases.curselection()[0])]
                )
            )
        elif self.groups.selection():
            indices = self.selected()
            if len(indices) == 2:
                self.summary.set(
                    "Sources: "
                    + ", ".join(
                        self.data["groups"][indices[0]]["candidates"][indices[1]]["sources"]
                    )
                )

    def save(self):
        self.app.save_page(self, "rules")

    def preview(self):
        if self.document is None:
            raise ConfigError("Select a module first")
        validate_rules(self.data)
        selected = filedialog.askopenfilename(
            parent=self,
            title="Select actual or simulated facts JSON",
            filetypes=[("JSON", "*.json")],
        )
        if not selected:
            return
        self.app.preview_selection(Path(selected), copy.deepcopy(self.data))
