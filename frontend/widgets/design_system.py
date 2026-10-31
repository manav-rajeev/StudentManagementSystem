"""Shared Campus Manager colors, ttk styles, and native-widget theme helpers.

The visual treatment uses layered opaque Tk surfaces, tinted borders, and color
contrast to suggest glass. Tkinter does not provide backdrop blur or true
per-widget transparency, so this design intentionally avoids those claims.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "background": "#F3F0FA",
        "surface": "#FFFFFF",
        "surface_secondary": "#ECE6F7",
        "text": "#252137",
        "body_text": "#373247",
        "muted": "#777187",
        "border": "#DED5EF",
        "border_highlight": "#FDFCFF",
        "primary": "#7651C9",
        "primary_hover": "#6845B5",
        "deep_purple": "#57369D",
        "lavender": "#C6B5F0",
        "heading_text": "#57369D",
        "primary_text": "#FFFFFF",
        "teal": "#187F5C",
        "warning": "#8A5A00",
        "danger": "#B83F4B",
        "danger_text": "#FFFFFF",
        "sidebar": "#29223A",
        "sidebar_hover": "#3B3152",
        "sidebar_active": "#4A3A68",
        "sidebar_text": "#F3EFFB",
        "sidebar_muted": "#B7ACC9",
        "status_active_bg": "#E2F2E9",
        "status_inactive_bg": "#ECE9F1",
        "status_graduated_bg": "#ECE6F7",
        "selection_bg": "#DED2F6",
        "selection_fg": "#252137",
        "notification_success_bg": "#E2F2E9",
        "notification_warning_bg": "#FFF1D1",
        "notification_error_bg": "#FBE8EA",
    },
    "dark": {
        "background": "#151321",
        "surface": "#211D31",
        "surface_secondary": "#2C2640",
        "text": "#F3F0FA",
        "body_text": "#DED9EA",
        "muted": "#B0A9C2",
        "border": "#44385D",
        "border_highlight": "#584A72",
        "primary": "#A78BFA",
        "primary_hover": "#B69EFF",
        "deep_purple": "#7651C9",
        "lavender": "#C4B5FD",
        "heading_text": "#C4B5FD",
        "primary_text": "#211D31",
        "teal": "#63D0A2",
        "warning": "#FFD27A",
        "danger": "#FF929C",
        "danger_text": "#29171D",
        "sidebar": "#100E1A",
        "sidebar_hover": "#282239",
        "sidebar_active": "#382C55",
        "sidebar_text": "#F3F0FA",
        "sidebar_muted": "#AAA1BE",
        "status_active_bg": "#203D35",
        "status_inactive_bg": "#302B3D",
        "status_graduated_bg": "#342B4B",
        "selection_bg": "#49396A",
        "selection_fg": "#F3F0FA",
        "notification_success_bg": "#203D35",
        "notification_warning_bg": "#45371F",
        "notification_error_bg": "#482B35",
    },
}


# Old inline colors are translated when theme switching reaches native Tk widgets.
BACKGROUND_COLOR_ROLES = {
    "#f3f6fa": "background", "#ffffff": "surface", "#fff": "surface",
    "#172235": "sidebar", "#26364f": "sidebar_hover", "#2d405c": "sidebar_active",
    "#f8f9fc": "surface", "#f5f7fa": "background",
    "#0e1726": "background", "#19263b": "surface", "#101b2d": "sidebar",
    "#243650": "sidebar_hover", "#2b527d": "sidebar_active",
    "#f3f0fa": "background", "#ece6f7": "surface_secondary",
    "#151321": "background", "#211d31": "surface", "#2c2640": "surface_secondary",
    "#29223a": "sidebar", "#3b3152": "sidebar_hover", "#4a3a68": "sidebar_active",
    "#100e1a": "sidebar", "#282239": "sidebar_hover", "#382c55": "sidebar_active",
}
FOREGROUND_COLOR_ROLES = {
    "#172235": "text", "#25344a": "body_text", "#66758a": "muted",
    "#8593a8": "sidebar_muted", "#74839a": "muted", "#cbd5e1": "sidebar_text",
    "#a33a3a": "danger", "#ffffff": "primary_text", "#000000": "text",
    "#e8eef8": "text", "#d4deec": "body_text", "#9aabc1": "muted",
    "#93a6bf": "sidebar_muted", "#d6e2f0": "sidebar_text", "#ff9999": "danger",
    "#252137": "text", "#373247": "body_text", "#777187": "muted",
    "#7651c9": "primary", "#57369d": "deep_purple", "#187f5c": "teal",
    "#c4b5fd": "heading_text",
    "#8a5a00": "warning", "#b83f4b": "danger", "#f3f0fa": "sidebar_text",
    "#b7acc9": "sidebar_muted", "#a78bfa": "primary", "#ded9ea": "body_text",
    "#b0a9c2": "muted", "#63d0a2": "teal", "#ffd27a": "warning",
    "#ff929c": "danger", "#aaa1be": "sidebar_muted",
}


def configure_ttk_styles(style: ttk.Style, palette: dict[str, str]) -> None:
    """Configure shared ttk styles from the active application palette."""
    style.theme_use("clam")
    style.configure("TFrame", background=palette["background"])
    style.configure("App.TFrame", background=palette["background"])
    style.configure(
        "Card.TFrame",
        background=palette["surface"],
        foreground=palette["text"],
        relief="solid",
        borderwidth=1,
        bordercolor=palette["border"],
        lightcolor=palette["border_highlight"],
        darkcolor=palette["border"],
    )
    style.configure("CardInner.TFrame", background=palette["surface"])

    style.configure("PageTitle.TLabel", background=palette["background"], foreground=palette["text"],
                    font=("Segoe UI", 24, "bold"))
    style.configure("Subtitle.TLabel", background=palette["background"], foreground=palette["muted"],
                    font=("Segoe UI", 10))
    style.configure("Date.TLabel", background=palette["surface_secondary"], foreground=palette["muted"],
                    font=("Segoe UI", 9, "bold"), padding=(12, 9))
    style.configure("SectionTitle.TLabel", background=palette["surface"], foreground=palette["text"],
                    font=("Segoe UI", 14, "bold"))
    style.configure("CardLabel.TLabel", background=palette["surface"], foreground=palette["muted"],
                    font=("Segoe UI", 10))
    style.configure("FormStatus.TLabel", background=palette["surface"], foreground=palette["muted"],
                    font=("Segoe UI", 9), wraplength=850)
    style.configure("DetailLabel.TLabel", background=palette["surface"], foreground=palette["muted"],
                    font=("Segoe UI", 9))
    style.configure("DetailValue.TLabel", background=palette["surface"], foreground=palette["text"],
                    font=("Segoe UI", 10))
    style.configure("CardValue.TLabel", background=palette["surface"], foreground=palette["text"],
                    font=("Segoe UI", 25, "bold"))
    style.configure("MetricIcon.TLabel", background=palette["surface"], foreground=palette["primary"],
                    font=("Segoe UI Symbol", 15, "bold"))
    style.configure("MetricIcon.Teal.TLabel", background=palette["surface"], foreground=palette["teal"],
                    font=("Segoe UI Symbol", 15, "bold"))
    style.configure("StudentActiveIcon.TLabel", background=palette["surface"], foreground=palette["teal"],
                    font=("Segoe UI", 11, "bold"))
    style.configure("StudentInactiveIcon.TLabel", background=palette["surface"], foreground=palette["muted"],
                    font=("Segoe UI", 11, "bold"))
    style.configure("StudentGraduatedIcon.TLabel", background=palette["surface"], foreground=palette["primary"],
                    font=("Segoe UI", 11, "bold"))
    style.configure("TLabel", background=palette["background"], foreground=palette["body_text"],
                    font=("Segoe UI", 10))

    style.configure("TEntry", padding=9, fieldbackground=palette["surface"], foreground=palette["text"],
                    insertcolor=palette["text"], bordercolor=palette["border"])
    style.map("TEntry", fieldbackground=[("disabled", palette["surface_secondary"])],
              foreground=[("disabled", palette["muted"])])
    style.configure("TCombobox", padding=8, fieldbackground=palette["surface"],
                    foreground=palette["text"], arrowcolor=palette["primary"])
    style.map("TCombobox", fieldbackground=[("readonly", palette["surface"]),
                                             ("disabled", palette["surface_secondary"])],
              foreground=[("readonly", palette["text"]), ("disabled", palette["muted"])])

    style.configure("Treeview", rowheight=34, font=("Segoe UI", 9),
                    background=palette["surface"], fieldbackground=palette["surface"],
                    foreground=palette["body_text"], bordercolor=palette["border"])
    style.map("Treeview", background=[("selected", palette["selection_bg"])],
              foreground=[("selected", palette["selection_fg"])])
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=9,
                    background=palette["surface_secondary"], foreground=palette["heading_text"])
    style.configure("TScrollbar", background=palette["surface_secondary"],
                    troughcolor=palette["background"], arrowcolor=palette["muted"],
                    bordercolor=palette["border"], lightcolor=palette["surface"],
                    darkcolor=palette["border"])
    style.map("TScrollbar", background=[("active", palette["lavender"])])

    style.configure("TButton", padding=(12, 9), font=("Segoe UI", 9),
                    background=palette["surface"], foreground=palette["body_text"],
                    bordercolor=palette["border"])
    style.map("TButton", background=[("disabled", palette["surface_secondary"]),
                                      ("pressed", palette["surface_secondary"]),
                                      ("active", palette["surface_secondary"])],
              foreground=[("disabled", palette["muted"]), ("active", palette["text"])])
    style.configure("Primary.TButton", padding=(16, 10), font=("Segoe UI", 9, "bold"),
                    background=palette["primary"], foreground=palette["primary_text"],
                    bordercolor=palette["primary"])
    style.map("Primary.TButton", background=[("disabled", palette["surface_secondary"]),
                                              ("pressed", palette["deep_purple"]),
                                              ("active", palette["primary_hover"])],
              foreground=[("disabled", palette["muted"]),
                          ("pressed", palette["primary_text"]),
                          ("active", palette["primary_text"])])
    style.configure("Secondary.TButton", padding=(14, 9), font=("Segoe UI", 9),
                    background=palette["surface_secondary"], foreground=palette["body_text"],
                    bordercolor=palette["border"])
    style.map("Secondary.TButton", background=[("disabled", palette["surface_secondary"]),
                                                ("pressed", palette["border"]),
                                                ("active", palette["surface"])],
              foreground=[("disabled", palette["muted"]), ("active", palette["deep_purple"])])
    style.configure("Danger.TButton", padding=(14, 9), font=("Segoe UI", 9, "bold"),
                    background=palette["danger"], foreground=palette["danger_text"],
                    bordercolor=palette["danger"])
    style.map("Danger.TButton", background=[("disabled", palette["surface_secondary"]),
                                             ("pressed", palette["danger"]),
                                             ("active", palette["danger"])],
              foreground=[("disabled", palette["muted"]), ("active", palette["danger_text"])])


class ScrollableFrame(ttk.Frame):
    """A lightweight vertical viewport that keeps its content width responsive."""

    def __init__(self, master: tk.Misc, *, palette: dict[str, str] | None = None) -> None:
        super().__init__(master, style="App.TFrame")
        palette = palette or PALETTES["light"]
        self.canvas = tk.Canvas(
            self,
            background=palette["background"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.content = ttk.Frame(self.canvas, style="App.TFrame")
        self._content_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._resize_content)
        self.canvas.bind("<MouseWheel>", self._scroll_with_mousewheel)

    def apply_theme(self, palette: dict[str, str]) -> None:
        """Update the canvas surface while ttk content follows shared styles."""
        self.canvas.configure(background=palette["background"])

    def _update_scrollregion(self, _event: tk.Event | None = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self._content_window, width=event.width)

    def _scroll_with_mousewheel(self, event: tk.Event) -> str:
        if event.delta:
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"


def recolor_native_widgets(parent: tk.Misc, palette: dict[str, str]) -> None:
    """Update known explicit Tk colors after a theme change, including open dialogs."""
    for widget in parent.winfo_children():
        for option, role_map in (("background", BACKGROUND_COLOR_ROLES),
                                 ("foreground", FOREGROUND_COLOR_ROLES),
                                 ("bg", BACKGROUND_COLOR_ROLES),
                                 ("fg", FOREGROUND_COLOR_ROLES)):
            try:
                value = str(widget.cget(option)).lower()
            except tk.TclError:
                continue
            role = role_map.get(value)
            if role:
                try:
                    widget.configure(**{option: palette[role]})
                except tk.TclError:
                    pass
        recolor_native_widgets(widget, palette)
