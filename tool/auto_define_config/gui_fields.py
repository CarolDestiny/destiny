from __future__ import annotations
import json
from tool.build_support.tk_layout import show_dialog
import tkinter as tk
from tkinter import messagebox, ttk
from .contracts import Field
from .errors import ConfigError


class FieldDialog:
    def __init__(self, parent, data=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Field declaration")
        self.window.withdraw()
        self.result = None
        data = data or {}
        self.values = {
            name: tk.StringVar(value=str(data.get(name, "")))
            for name in ("id", "macro", "alias", "description", "unit")
        }
        self.values["type"] = tk.StringVar(value=data.get("type", "boolean"))
        self.values["kind"] = tk.StringVar(value=data.get("kind", "observation"))
        self.values["default"] = tk.StringVar(
            value=json.dumps(data["default"]) if "default" in data else ""
        )
        pane = ttk.Frame(self.window, padding=12)
        pane.pack(fill="both", expand=True)
        pane.columnconfigure(1, weight=1)
        for row, name in enumerate(
            ("id", "type", "kind", "macro", "alias", "unit", "default", "description")
        ):
            ttk.Label(pane, text=name.replace("_", " ").title()).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=5
            )
            if name in ("type", "kind"):
                options = (
                    ("boolean", "integer", "string")
                    if name == "type"
                    else ("observation", "option")
                )
                widget = ttk.Combobox(
                    pane, textvariable=self.values[name], values=options, state="readonly"
                )
            else:
                widget = ttk.Entry(pane, textvariable=self.values[name])
            widget.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(
            pane,
            text="Default is only for configurable options: JSON true/false, integer, or quoted string.\nDetected hardware values remain read-only.",
            wraplength=640,
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=8)
        controls = ttk.Frame(pane)
        controls.grid(row=9, column=0, columnspan=2, sticky="e")
        ttk.Button(controls, text="Cancel", command=self.window.destroy).pack(side="right")
        ttk.Button(controls, text="Use field", command=self.accept).pack(side="right", padx=8)

        show_dialog(self.window, parent, width=690, height=440)

    def accept(self):
        try:
            data = {
                name: self.values[name].get().strip()
                for name in ("id", "type", "kind", "macro", "description")
            }
            if not data["macro"] and data["id"]:
                data["macro"] = "DESTINY_DEFINE_CMAKE_" + data["id"].upper().replace(".", "_")
            for name in ("alias", "unit"):
                if self.values[name].get().strip():
                    data[name] = self.values[name].get().strip()
            if data["kind"] == "option":
                data["default"] = json.loads(self.values["default"].get())
            elif self.values["default"].get().strip():
                raise ConfigError("Hardware observations cannot have a configurable default")
            Field.from_data(data)
            self.result = data
            self.window.destroy()
        except (ConfigError, ValueError) as exc:
            messagebox.showerror("Invalid field", str(exc), parent=self.window)


def edit_field(parent, data=None):
    dialog = FieldDialog(parent, data)
    parent.wait_window(dialog.window)
    return dialog.result
