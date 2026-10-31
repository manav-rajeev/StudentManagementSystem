"""Small, theme-aware application notifications for Tkinter."""

from __future__ import annotations

import tkinter as tk
from typing import Any


class NotificationCenter(tk.Frame):
    """Display one non-blocking notification over the main application window."""

    _STATES = {
        "success": ("notification_success_bg", "teal", "Success"),
        "warning": ("notification_warning_bg", "warning", "Warning"),
        "error": ("notification_error_bg", "danger", "Error"),
    }

    def __init__(self, master: tk.Misc, palette: dict[str, Any]) -> None:
        super().__init__(master, bd=1, relief="solid", padx=14, pady=11)
        self.palette = palette
        self._dismiss_id: str | None = None
        self._kind = "success"
        self.grid_columnconfigure(1, weight=1)

        self.title_label = tk.Label(self, font=("Segoe UI", 9, "bold"), anchor="w")
        self.title_label.grid(row=0, column=0, sticky="nw", padx=(0, 10))
        self.message_label = tk.Label(
            self, font=("Segoe UI", 9), anchor="w", justify="left", wraplength=720
        )
        self.message_label.grid(row=0, column=1, sticky="ew")
        self.close_button = tk.Button(
            self,
            text="×",
            command=self.dismiss,
            relief="flat",
            bd=0,
            padx=5,
            pady=0,
            font=("Segoe UI", 13),
            cursor="hand2",
        )
        self.close_button.grid(row=0, column=2, sticky="ne", padx=(8, 0))
        self.apply_theme(palette)
        self.pack_forget()

    def show(self, message: str, kind: str = "success", duration_ms: int | None = None) -> None:
        """Show a message; successes time out while warnings and errors persist."""
        if not message:
            self.dismiss()
            return
        self._cancel_dismiss()
        self._kind = kind if kind in self._STATES else "success"
        _, _, title = self._STATES[self._kind]
        self.title_label.configure(text=title)
        self.message_label.configure(text=message)
        self._apply_state_colors()
        if not self.winfo_manager():
            self.pack(fill="x", side="top", pady=(0, 12))

        if duration_ms is None and self._kind == "success":
            duration_ms = 5000
        if duration_ms and duration_ms > 0:
            self._dismiss_id = self.after(duration_ms, self.dismiss)

    def dismiss(self) -> None:
        self._cancel_dismiss()
        self.pack_forget()

    def apply_theme(self, palette: dict[str, Any]) -> None:
        """Recolor an existing notification immediately when the app theme changes."""
        self.palette = palette
        self._apply_state_colors()

    def _apply_state_colors(self) -> None:
        if not self.palette:
            return
        background_key, foreground_key, _ = self._STATES[self._kind]
        background = self.palette.get(background_key, self.palette["surface"])
        foreground = self.palette.get(foreground_key, self.palette["body_text"])
        border = self.palette["border"]
        self.configure(bg=background, highlightthickness=1, highlightbackground=border)
        self.title_label.configure(bg=background, fg=foreground)
        self.message_label.configure(bg=background, fg=self.palette["text"])
        self.close_button.configure(
            bg=background,
            fg=self.palette["muted"],
            activebackground=background,
            activeforeground=self.palette["text"],
        )

    def _cancel_dismiss(self) -> None:
        if self._dismiss_id is not None:
            try:
                self.after_cancel(self._dismiss_id)
            except tk.TclError:
                pass
            self._dismiss_id = None
