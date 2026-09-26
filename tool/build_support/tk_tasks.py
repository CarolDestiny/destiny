"""One cancellable worker per window; Tk is touched only by its owning thread."""

from __future__ import annotations

import queue
import threading
from typing import Callable


class TaskRunner:
    def __init__(
        self, widget, *, status: Callable[[str], None], failure: Callable[[Exception], None]
    ):
        self.widget = widget
        self.status = status
        self.failure = failure
        self.messages = queue.Queue()
        self.cancel = threading.Event()
        self.thread = None
        self.closing = False
        self.finished = None
        self.widget.after(50, self._poll)

    @property
    def busy(self):
        return self.finished is not None or (self.thread is not None and self.thread.is_alive())

    def start(self, work, finished) -> bool:
        if self.busy or self.closing:
            self.status("Another operation is running. Cancel it or wait for completion.")
            return False
        self.cancel = threading.Event()
        self.finished = finished

        def worker():
            try:
                value = work(self.cancel, lambda text: self.messages.put(("status", text)))
                self.messages.put(("done", value))
            except Exception as exc:
                self.messages.put(("error", exc))

        self.thread = threading.Thread(target=worker, name="destiny-gui-worker", daemon=True)
        self.thread.start()
        return True

    def _poll(self):
        while True:
            try:
                kind, value = self.messages.get_nowait()
            except queue.Empty:
                break
            if self.closing:
                if kind in ("done", "error"):
                    self.finished = None
                continue
            if kind == "status":
                self.status(str(value))
            elif kind == "done":
                callback = self.finished
                self.finished = None
                if callback:
                    try:
                        callback(value)
                    except Exception as exc:
                        self.failure(exc)
            else:
                self.finished = None
                self.failure(value)
        if self.closing and not self.busy:
            self.widget.destroy()
            return
        self.widget.after(50, self._poll)

    def close(self):
        self.closing = True
        self.cancel.set()
        self.widget.withdraw()
