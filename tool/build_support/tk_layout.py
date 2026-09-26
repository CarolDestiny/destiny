"""Small Tk layout helpers shared by the project's modal editors."""

from __future__ import annotations


def _offset(coordinate: int, extent: int, screen_extent: int) -> str:
    # A negative wm offset measures from the right/bottom edge, not the desktop origin.
    return f"+{coordinate}" if coordinate >= 0 else f"-{screen_extent - extent - coordinate}"


def show_dialog(window, parent, *, width: int, height: int) -> None:
    """Keep a modal next to its owner, including an owner on a secondary monitor."""
    owner = parent.winfo_toplevel()
    owner.update_idletasks()
    window.update_idletasks()
    if owner.winfo_viewable():
        x = owner.winfo_rootx() + max(0, (owner.winfo_width() - width) // 2)
        y = owner.winfo_rooty() + max(0, (owner.winfo_height() - height) // 2)
    else:
        x = max(0, (window.winfo_screenwidth() - width) // 2)
        y = max(0, (window.winfo_screenheight() - height) // 2)
    geometry = (
        f"{width}x{height}"
        f"{_offset(x, width, window.winfo_screenwidth())}"
        f"{_offset(y, height, window.winfo_screenheight())}"
    )
    window.transient(owner)
    window.geometry(geometry)
    window.minsize(min(width, 650), min(height, 400))
    window.deiconify()
    window.grab_set()
    window.focus_set()
