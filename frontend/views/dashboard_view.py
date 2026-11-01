"""Vibrant campus overview with live student and lookup totals."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from tkinter import ttk

from backend.student_service import dashboard_statistics
from frontend.widgets.design_system import bind_hover_tree


class DashboardView(ttk.Frame):
    def __init__(self, master: tk.Misc, on_navigate: Callable[[str], None]) -> None:
        super().__init__(master, style="App.TFrame")
        self.on_navigate = on_navigate
        self.cards: dict[str, ttk.Label] = {}
        self.metric_components: dict[str, dict[str, ttk.Widget]] = {}

        header = ttk.Frame(self, style="Hero.TFrame", padding=(23, 17))
        header.pack(fill="x", pady=(0, 24))
        accent_bar = ttk.Frame(header, style="HeroInner.TFrame", height=4)
        accent_bar.pack(fill="x", pady=(0, 15))
        accent_bar.pack_propagate(False)
        for style_name in ("BrandViolet.TFrame", "BrandIndigo.TFrame", "BrandMagenta.TFrame"):
            ttk.Frame(accent_bar, style=style_name).pack(side="left", fill="both", expand=True)

        hero_content = ttk.Frame(header, style="HeroInner.TFrame")
        hero_content.pack(fill="x")
        titles = ttk.Frame(hero_content, style="HeroInner.TFrame")
        titles.pack(side="left", fill="x", expand=True)
        ttk.Label(titles, text="CAMPUS OVERVIEW", style="HeroEyebrow.TLabel").pack(
            anchor="w", pady=(0, 3)
        )
        ttk.Label(titles, text="Welcome back", style="HeroTitle.TLabel").pack(anchor="w")
        ttk.Label(
            titles,
            text="Here's what's happening at your institution.",
            style="HeroSubtitle.TLabel",
        ).pack(anchor="w", pady=(5, 0))

        header_actions = ttk.Frame(hero_content, style="HeroInner.TFrame")
        header_actions.pack(side="right", anchor="s")
        today = datetime.now().strftime("%A, %B %d, %Y")
        ttk.Label(header_actions, text=today, style="HeroDate.TLabel").pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(
            header_actions, text="Refresh data", style="HeroSecondary.TButton",
            command=self.refresh,
        ).pack(side="left", anchor="s")

        card_row = ttk.Frame(self, style="App.TFrame")
        card_row.pack(fill="x")
        metric_specs = (
            ("total_students", "Total students", "ST", "Violet"),
            ("total_courses", "Total courses", "CR", "Indigo"),
            ("total_departments", "Total departments", "DP", "Magenta"),
        )
        for index, (key, label, icon, accent) in enumerate(metric_specs):
            card = ttk.Frame(card_row, style=f"Metric{accent}.TFrame", padding=(21, 16))
            card.pack(side="left", fill="both", expand=True, padx=(0, 14 if index < 2 else 0))
            accent_bar = ttk.Frame(card, style=f"Metric{accent}Accent.TFrame", height=3)
            accent_bar.pack(fill="x", pady=(0, 15))
            accent_bar.pack_propagate(False)
            card_header = ttk.Frame(card, style=f"Metric{accent}Inner.TFrame")
            card_header.pack(fill="x")
            title = ttk.Label(card_header, text=label, style=f"Metric{accent}Label.TLabel")
            title.pack(side="left", anchor="center")
            icon_label = ttk.Label(card_header, text=icon, style=f"Metric{accent}Icon.TLabel")
            icon_label.pack(side="right", padx=(8, 0))
            value = ttk.Label(card, text="—", style=f"Metric{accent}Value.TLabel")
            value.pack(anchor="w", pady=(12, 0))
            self.cards[key] = value
            self.metric_components[key] = {
                "card": card,
                "accent_bar": accent_bar,
                "header": card_header,
                "title": title,
                "icon": icon_label,
                "value": value,
            }
            bind_hover_tree(
                card,
                lambda hovered, metric=key, color=accent: self._set_metric_hover(
                    metric, color, hovered
                ),
            )

        panel = ttk.Frame(self, style="Card.TFrame", padding=(23, 20))
        panel.pack(fill="x", pady=(20, 0))
        quick_header = ttk.Frame(panel, style="CardInner.TFrame")
        quick_header.pack(fill="x")
        ttk.Label(quick_header, text="Quick actions", style="SectionTitle.TLabel").pack(anchor="w")
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

    def _set_metric_hover(self, key: str, accent: str, hovered: bool) -> None:
        """Swap a metric card's surfaces without moving any controls."""
        components = self.metric_components.get(key)
        if not components:
            return
        state = "Hover" if hovered else ""
        components["card"].configure(style=f"Metric{accent}{state}.TFrame")
        components["accent_bar"].configure(style=f"Metric{accent}Accent{state}.TFrame")
        components["header"].configure(style=f"Metric{accent}{state}Inner.TFrame")
        components["title"].configure(style=f"Metric{accent}{state}Label.TLabel")
        components["icon"].configure(style=f"Metric{accent}{state}Icon.TLabel")
        components["value"].configure(style=f"Metric{accent}{state}Value.TLabel")

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
