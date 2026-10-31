"""Dashboard cards with live student and lookup totals."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable

from backend.student_service import dashboard_statistics


class DashboardView(ttk.Frame):
    def __init__(self, master: tk.Misc, on_navigate: Callable[[str], None]) -> None:
        super().__init__(master, style="App.TFrame")
        self.on_navigate = on_navigate
        self.cards: dict[str, ttk.Label] = {}
        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", pady=(0, 28))
        titles = ttk.Frame(header, style="App.TFrame")
        titles.pack(side="left")
        ttk.Label(titles, text="Dashboard", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(titles, text="An overview of your student records", style="Subtitle.TLabel").pack(
            anchor="w", pady=(5, 0)
        )
        ttk.Button(header, text="Refresh", style="Secondary.TButton",
                   command=self.refresh).pack(side="right", anchor="s")

        card_row = ttk.Frame(self, style="App.TFrame")
        card_row.pack(fill="x")
        for key, label in (("total_students", "Total students"),
                           ("total_courses", "Courses"),
                           ("total_departments", "Departments")):
            card = ttk.Frame(card_row, style="Card.TFrame", padding=(22, 20))
            card.pack(side="left", fill="both", expand=True, padx=(0, 16))
            ttk.Label(card, text=label, style="CardLabel.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="—", style="CardValue.TLabel")
            value.pack(anchor="w", pady=(12, 0))
            self.cards[key] = value

        panel = ttk.Frame(self, style="Card.TFrame", padding=24)
        panel.pack(fill="x", pady=(24, 0))
        ttk.Label(panel, text="Quick actions", font=("Segoe UI", 14, "bold"),
                  background="#ffffff", foreground="#172235").pack(anchor="w")
        ttk.Label(panel, text="Register a student or review the current records.",
                  background="#ffffff", foreground="#66758a").pack(anchor="w", pady=(7, 16))
        actions = ttk.Frame(panel, style="Card.TFrame")
        actions.pack(anchor="w")
        ttk.Button(actions, text="Register student", style="Primary.TButton",
                   command=lambda: self.on_navigate("registration")).pack(side="left")
        ttk.Button(actions, text="View student records", style="Secondary.TButton",
                   command=lambda: self.on_navigate("students")).pack(side="left", padx=(10, 0))
        ttk.Button(actions, text="Choose student for course enrolments", style="Secondary.TButton",
                   command=lambda: self.on_navigate("students")).pack(side="left", padx=(10, 0))

        self.status = ttk.Label(self, text="", style="Subtitle.TLabel")
        self.status.pack(anchor="w", pady=(18, 0))

    def refresh(self) -> None:
        try:
            stats = dashboard_statistics()
        except Exception:
            self.status.configure(text="Database unavailable. Check the local database settings and server.")
            for card in self.cards.values():
                card.configure(text="—")
            return
        for key, card in self.cards.items():
            card.configure(text=f"{stats.get(key, 0):,}")
        self.status.configure(text="Statistics are up to date.")
