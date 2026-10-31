"""Dashboard cards with live student and lookup totals."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from tkinter import ttk

from backend.student_service import dashboard_statistics


class DashboardView(ttk.Frame):
    def __init__(self, master: tk.Misc, on_navigate: Callable[[str], None]) -> None:
        super().__init__(master, style="App.TFrame")
        self.on_navigate = on_navigate
        self.cards: dict[str, ttk.Label] = {}

        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x", pady=(0, 28))
        titles = ttk.Frame(header, style="App.TFrame")
        titles.pack(side="left", fill="x", expand=True)
        ttk.Label(titles, text="Welcome back", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            titles,
            text="Here's what's happening at your institution.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 0))
        header_actions = ttk.Frame(header, style="App.TFrame")
        header_actions.pack(side="right", anchor="s")
        today = datetime.now().strftime("%A, %B %d, %Y")
        ttk.Label(header_actions, text=today, style="Date.TLabel").pack(side="left", padx=(0, 10))
        ttk.Button(
            header_actions, text="Refresh", style="Secondary.TButton", command=self.refresh
        ).pack(side="left", anchor="s")

        card_row = ttk.Frame(self, style="App.TFrame")
        card_row.pack(fill="x")
        metric_specs = (
            ("total_students", "Total students", "♙", "MetricIcon.TLabel"),
            ("total_courses", "Total courses", "▤", "MetricIcon.Teal.TLabel"),
            ("total_departments", "Total departments", "⌂", "MetricIcon.TLabel"),
        )
        for index, (key, label, icon, icon_style) in enumerate(metric_specs):
            card = ttk.Frame(card_row, style="Card.TFrame", padding=(22, 20))
            card.pack(side="left", fill="both", expand=True, padx=(0, 16 if index < 2 else 0))
            card_header = ttk.Frame(card, style="CardInner.TFrame")
            card_header.pack(fill="x")
            ttk.Label(card_header, text=label, style="CardLabel.TLabel").pack(side="left", anchor="center")
            ttk.Label(card_header, text=icon, style=icon_style).pack(side="right", padx=(8, 0))
            value = ttk.Label(card, text="—", style="CardValue.TLabel")
            value.pack(anchor="w", pady=(15, 0))
            self.cards[key] = value

        panel = ttk.Frame(self, style="Card.TFrame", padding=24)
        panel.pack(fill="x", pady=(24, 0))
        ttk.Label(panel, text="Quick actions", style="SectionTitle.TLabel").pack(anchor="w")
        ttk.Label(
            panel,
            text="Register a student or review current records and course enrolments.",
            style="CardLabel.TLabel",
        ).pack(anchor="w", pady=(7, 16))
        actions = ttk.Frame(panel, style="CardInner.TFrame")
        actions.pack(anchor="w")
        ttk.Button(
            actions, text="Register student", style="Primary.TButton",
            command=lambda: self.on_navigate("registration"),
        ).pack(side="left")
        ttk.Button(
            actions, text="View student records", style="Secondary.TButton",
            command=lambda: self.on_navigate("students"),
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            actions, text="Choose student for course enrolments", style="Secondary.TButton",
            command=lambda: self.on_navigate("students"),
        ).pack(side="left", padx=(10, 0))

        self.status = ttk.Label(self, text="", style="Subtitle.TLabel")
        self.status.pack(anchor="w", pady=(18, 0))

    def refresh(self) -> None:
        """Load the existing dashboard metrics through the existing service."""
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
