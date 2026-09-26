"""Structured condition editor with a read-only expression preview."""

from __future__ import annotations
from tool.build_support.tk_layout import show_dialog
import tkinter as tk
from tkinter import messagebox, ttk
from .expression_tree import ExpressionTree, children, expression_text
from .errors import ConfigError


class ConditionDialog:
    def __init__(self, parent, expression, catalogue: dict, aliases=()):
        self.window = tk.Toplevel(parent)
        self.window.title("Edit condition tree")
        self.window.withdraw()
        self.model = ExpressionTree(expression)
        self.catalogue = catalogue
        self.result = None
        self.references = tuple(sorted(set(catalogue) | set(aliases)))
        pane = ttk.Frame(self.window, padding=12)
        pane.pack(fill="both", expand=True)
        pane.columnconfigure(0, weight=1)
        pane.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(pane, show="tree", selectmode="browse")
        self.tree.grid(row=0, column=0, columnspan=4, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.selected)
        self.operation = tk.StringVar(value="TRUE")
        self.reference = tk.StringVar()
        self.compare = tk.StringVar(value="eq")
        self.value = tk.StringVar()
        ttk.Combobox(
            pane,
            textvariable=self.operation,
            values=("TRUE", "FALSE", "REF", "ALL", "ANY", "NOT", "COMPARE"),
            state="readonly",
            width=12,
        ).grid(row=1, column=0, sticky="w", pady=8)
        self.field = ttk.Combobox(
            pane, textvariable=self.reference, values=self.references, width=36
        )
        self.field.grid(row=1, column=1, columnspan=2, sticky="ew")
        ttk.Button(pane, text="Replace selected node", command=self.apply_node).grid(
            row=1, column=3, padx=6
        )
        ttk.Combobox(
            pane,
            textvariable=self.compare,
            values=("eq", "ne", "lt", "le", "gt", "ge"),
            state="readonly",
            width=8,
        ).grid(row=2, column=0, sticky="w")
        ttk.Entry(pane, textvariable=self.value).grid(row=2, column=1, columnspan=2, sticky="ew")
        self.unit = tk.StringVar()
        ttk.Label(pane, textvariable=self.unit).grid(row=2, column=3)
        buttons = ttk.Frame(pane)
        buttons.grid(row=3, column=0, columnspan=4, sticky="ew", pady=8)
        for label, callback in [
            ("Add child", self.add),
            ("Remove", self.remove),
            ("Move up", lambda: self.move(-1)),
            ("Move down", lambda: self.move(1)),
        ]:
            ttk.Button(buttons, text=label, command=callback).pack(side="left", padx=(0, 5))
        self.preview = tk.Text(pane, height=4, wrap="word", state="disabled")
        self.preview.grid(row=4, column=0, columnspan=4, sticky="ew")
        footer = ttk.Frame(pane)
        footer.grid(row=5, column=0, columnspan=4, sticky="e", pady=(10, 0))
        ttk.Button(footer, text="Cancel", command=self.window.destroy).pack(side="right")
        ttk.Button(footer, text="Use condition", command=self.accept).pack(side="right", padx=8)
        self.reference.trace_add(
            "write",
            lambda *_: self.unit.set(
                str(self.catalogue.get(self.reference.get(), {}).get("unit") or "")
            ),
        )
        self.refresh()
        show_dialog(self.window, parent, width=850, height=570)

    def path(self):
        selected = self.tree.selection()
        return tuple(int(x) for x in selected[0].split("/")[1:]) if selected else ()

    def refresh(self, path=()):
        for item in self.tree.get_children():
            self.tree.delete(item)

        def add(parent, expression, indices):
            identifier = "root" + "".join("/" + str(index) for index in indices)
            self.tree.insert(
                parent, "end", iid=identifier, text=expression_text(expression), open=True
            )
            for index, child in enumerate(children(expression)):
                add(identifier, child, (*indices, index))

        add("", self.model.root, ())
        identifier = "root" + "".join("/" + str(index) for index in path)
        if self.tree.exists(identifier):
            self.tree.selection_set(identifier)
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", expression_text(self.model.root))
        self.preview.configure(state="disabled")

    def selected(self, event=None):
        expression = self.model.get(self.path())
        if type(expression) is bool:
            self.operation.set("TRUE" if expression else "FALSE")
            return
        operation, value = next(iter(expression.items()))
        self.operation.set(operation.upper())
        if operation == "ref":
            self.reference.set(value)
        elif operation == "compare":
            self.reference.set(value["field"])
            self.compare.set(value["op"])
            self.value.set(value["value"])

    def safely(self, action):
        try:
            action()
        except (ConfigError, KeyError, ValueError) as exc:
            messagebox.showerror("Invalid condition", str(exc), parent=self.window)

    def apply_node(self):
        def action():
            operation = self.operation.get()
            current = self.model.get(self.path())
            if operation in ("TRUE", "FALSE"):
                expression = operation == "TRUE"
            elif operation == "REF":
                name = self.reference.get()
                if name not in self.references:
                    raise ConfigError("Choose a registered boolean field or local alias")
                if name in self.catalogue and self.catalogue[name]["type"] != "boolean":
                    raise ConfigError("Use COMPARE for integer or string fields")
                expression = {"ref": name}
            elif operation in ("ALL", "ANY"):
                expression = {operation.lower(): [True]}
            elif operation == "NOT":
                expression = {"not": True}
            else:
                name = self.reference.get()
                definition = self.catalogue.get(name)
                if not definition or definition["type"] == "boolean":
                    raise ConfigError("Choose a registered integer or string field")
                comparison = {"field": name, "op": self.compare.get(), "value": self.value.get()}
                if definition.get("unit"):
                    comparison["unit"] = definition["unit"]
                if definition["type"] == "integer":
                    value = int(comparison["value"])
                    comparison["value"] = str(value)
                    if not -(2**63) <= value < 2**63:
                        raise ConfigError("Integer exceeds signed 64-bit range")
                elif comparison["op"] not in ("eq", "ne"):
                    raise ConfigError("String fields support eq or ne")
                expression = {"compare": comparison}
            self.model.replace(self.path(), expression)
            self.refresh(self.path())

        self.safely(action)

    def add(self):
        self.safely(lambda: (self.model.append(self.path()), self.refresh(self.path())))

    def remove(self):
        self.safely(lambda: (self.model.remove(self.path()), self.refresh()))

    def move(self, delta):
        self.safely(lambda: (self.model.move(self.path(), delta), self.refresh()))

    def accept(self):
        self.result = self.model.root
        self.window.destroy()


def edit_condition(parent, expression, catalogue, aliases=()):
    dialog = ConditionDialog(parent, expression, catalogue, aliases)
    parent.wait_window(dialog.window)
    return dialog.result
