"""Theme-aware vertical navigation sidebar."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable


class NavigationSidebar(tk.Frame):
    """Campus Manager navigation with active, hover, and theme states."""

    def __init__(
        self,
        master: tk.Misc,
        on_navigate: Callable[[str], None],
        on_theme_toggle: Callable[[], None],
        theme: str,
        palette: dict[str, str],
    ) -> None:
        super().__init__(master, width=246)
        self.pack_propagate(False)
        self._on_navigate = on_navigate
        self._on_theme_toggle = on_theme_toggle
        self._buttons: dict[str, tk.Button] = {}
        self._active_page = "dashboard"
        self._hover_page: str | None = None
        self.theme = theme
        self.palette = palette

        self.brand = tk.Frame(self)
        self.brand.pack(fill="x", padx=20, pady=(24, 26))
        self.brand_badge = tk.Label(
            self.brand, text="CM", font=("Segoe UI", 10, "bold"),
            padx=10, pady=9, relief="flat",
        )
        self.brand_badge.pack(side="left", padx=(0, 11))
        brand_copy = tk.Frame(self.brand)
        brand_copy.pack(side="left", fill="x", expand=True)
        self.brand_title = tk.Label(
            brand_copy, text="Campus Manager", font=("Segoe UI", 13, "bold"), anchor="w"
        )
        self.brand_title.pack(anchor="w")
        self.brand_subtitle = tk.Label(
            brand_copy, text="UNIVERSITY ADMIN", font=("Segoe UI", 8, "bold"), anchor="w"
        )
        self.brand_subtitle.pack(anchor="w", pady=(3, 0))

        self.section_label = tk.Label(
            self, text="WORKSPACE", font=("Segoe UI", 8, "bold"), anchor="w", padx=20, pady=8
        )
        self.section_label.pack(fill="x", pady=(0, 5))

        destinations = (
            ("dashboard", "▦", "Dashboard"),
            ("students", "♙", "Students"),
            ("enrollments", "▤", "Course Enrolments"),
        )
        for page, icon, label in destinations:
            button = tk.Button(
                self,
                text=f"{icon}    {label}",
                command=lambda key=page: self._on_navigate(key),
                anchor="w", padx=18, pady=12, bd=0, relief="flat",
                font=("Segoe UI", 10), cursor="hand2",
            )
            button.pack(fill="x", padx=12, pady=3)
            button.bind("<Enter>", lambda _event, key=page: self._on_hover(key))
            button.bind("<Leave>", lambda _event, key=page: self._on_leave(key))
            self._buttons[page] = button

        self.footer = tk.Frame(self)
        self.footer.pack(side="bottom", fill="x", padx=14, pady=(12, 18))
        self.separator = tk.Frame(self.footer, height=1)
        self.separator.pack(fill="x", pady=(0, 12))
        self.theme_button = tk.Button(
            self.footer, command=self._toggle_theme, anchor="w", padx=12, pady=10,
            bd=0, relief="flat", font=("Segoe UI", 9, "bold"), cursor="hand2",
        )
        self.theme_button.pack(fill="x")
        self.theme_button.bind("<Enter>", lambda _event: self.theme_button.configure(
            bg=self.palette["sidebar_hover"]
        ))
        self.theme_button.bind("<Leave>", lambda _event: self._style_theme_button())
        self.footer_label = tk.Label(
            self.footer, text="STUDENT MANAGEMENT DESKTOP APP", font=("Segoe UI", 7, "bold"),
            anchor="w", padx=3,
        )
        self.footer_label.pack(fill="x", pady=(13, 0))
        self.apply_theme(self.theme, self.palette)

    def apply_theme(self, theme: str, palette: dict[str, Any]) -> None:
        """Apply the application-owned theme palette to the sidebar widgets."""
        self.theme = theme
        self.palette = palette
        self.configure(bg=palette["sidebar"])
        for widget in (self.brand, self.brand_title.master, self.footer):
            widget.configure(bg=palette["sidebar"])
        self.brand_badge.configure(bg=palette["primary"], fg=palette["primary_text"])
        self.brand_title.configure(bg=palette["sidebar"], fg=palette["sidebar_text"])
        self.brand_subtitle.configure(bg=palette["sidebar"], fg=palette["sidebar_muted"])
        self.section_label.configure(bg=palette["sidebar"], fg=palette["sidebar_muted"])
        self.separator.configure(bg=palette["sidebar_hover"])
        self.footer_label.configure(bg=palette["sidebar"], fg=palette["sidebar_muted"])
        self.set_active(self._active_page)
        self._style_theme_button()

    def set_active(self, page: str) -> None:
        """Keep the existing navigation API and registration highlight behavior."""
        if page == "registration":
            page = "students"
        self._active_page = page
        for key in self._buttons:
            self._style_navigation_button(key)

    def _style_navigation_button(self, page: str) -> None:
        button = self._buttons[page]
        active = page == self._active_page
        hovered = page == self._hover_page
        background = self.palette["sidebar_active"] if active else (
            self.palette["sidebar_hover"] if hovered else self.palette["sidebar"]
        )
        button.configure(
            bg=background,
            fg=self.palette["sidebar_text"],
            activebackground=self.palette["sidebar_active"] if active else self.palette["sidebar_hover"],
            activeforeground=self.palette["sidebar_text"],
            font=("Segoe UI", 10, "bold" if active else "normal"),
        )

    def _on_hover(self, page: str) -> None:
        self._hover_page = page
        self._style_navigation_button(page)

    def _on_leave(self, page: str) -> None:
        if self._hover_page == page:
            self._hover_page = None
        self._style_navigation_button(page)

    def _toggle_theme(self) -> None:
        self._on_theme_toggle()

    def _style_theme_button(self) -> None:
        mode = "light" if self.theme == "dark" else "dark"
        symbol = "☼" if mode == "light" else "◐"
        self.theme_button.configure(
            text=f"{symbol}   Switch to {mode} theme",
            bg=self.palette["sidebar"], fg=self.palette["sidebar_text"],
            activebackground=self.palette["sidebar_hover"],
            activeforeground=self.palette["sidebar_text"],
        )
