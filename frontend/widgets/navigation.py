"""Vertical navigation sidebar."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable


class NavigationSidebar(tk.Frame):
    """Compact left navigation with active-page indication."""

    def __init__(self, master: tk.Misc, on_navigate: Callable[[str], None]) -> None:
        super().__init__(master, bg="#172235", width=230)
        self.pack_propagate(False)
        self._on_navigate = on_navigate
        self._buttons: dict[str, tk.Button] = {}

        tk.Label(
            self, text="CAMPUS\nMANAGER", bg="#172235", fg="#ffffff",
            font=("Segoe UI", 16, "bold"), justify="left", padx=24, pady=28,
        ).pack(fill="x")
        tk.Label(
            self, text="STUDENT SERVICES", bg="#172235", fg="#8593a8",
            font=("Segoe UI", 8, "bold"), padx=24, pady=8, anchor="w",
        ).pack(fill="x")

        for page, label in (("dashboard", "Dashboard"), ("students", "Students"),
                            ("enrollments", "Course Enrolments")):
            button = tk.Button(
                self, text=label, command=lambda key=page: self._on_navigate(key),
                anchor="w", padx=24, pady=12, bd=0, relief="flat",
                bg="#172235", fg="#cbd5e1", activebackground="#26364f",
                activeforeground="#ffffff", font=("Segoe UI", 10), cursor="hand2",
            )
            button.pack(fill="x", padx=10, pady=2)
            self._buttons[page] = button

        tk.Label(
            self, text="STUDENT MANAGEMENT\nDESKTOP APP", bg="#172235",
            fg="#74839a", font=("Segoe UI", 8), justify="left", padx=24,
        ).pack(side="bottom", anchor="w", pady=22)

    def set_active(self, page: str) -> None:
        if page == "registration":
            page = "students"
        for key, button in self._buttons.items():
            active = key == page
            button.configure(
                bg="#2d405c" if active else "#172235",
                fg="#ffffff" if active else "#cbd5e1",
                font=("Segoe UI", 10, "bold" if active else "normal"),
            )
