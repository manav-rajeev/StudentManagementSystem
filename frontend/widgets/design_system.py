"""Shared Campus Manager colors, ttk styles, and native-widget theme helpers.

The visual treatment uses layered opaque Tk surfaces, tinted borders, and color
contrast to suggest glass. Tkinter does not provide backdrop blur or true
per-widget transparency, so this design intentionally avoids those claims.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from typing import Any


PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "background": "#F4F1FB",
        "surface": "#FFFFFF",
        "surface_secondary": "#EEE8FA",
        "hero_bg": "#EEE6FF",
        "hero_border": "#CCB9F3",
        "hero_text": "#32175E",
        "hero_muted": "#624B82",
        "hero_date_bg": "#DFD1FF",
        "hero_eyebrow": "#7435C1",
        "text": "#211A32",
        "body_text": "#3B3350",
        "muted": "#786F8E",
        "border": "#DDD3F3",
        "border_highlight": "#FFFFFF",
        "primary": "#7C3AED",
        "primary_hover": "#6D28D9",
        "primary_pressed": "#5B21B6",
        "secondary_hover": "#E5D8FF",
        "secondary_hover_text": "#5425A8",
        "sidebar_active_hover": "#6436A7",
        "deep_purple": "#5425A8",
        "lavender": "#C4B5FD",
        "heading_text": "#5526A8",
        "primary_text": "#FFFFFF",
        "accent_violet": "#7C3AED",
        "accent_indigo": "#4F46E5",
        "accent_magenta": "#C026D3",
        "accent_teal": "#0F9F83",
        "accent_amber": "#B7791F",
        "metric_violet_bg": "#F5EFFF",
        "metric_violet_hover_bg": "#EEE3FF",
        "metric_indigo_bg": "#F0F0FF",
        "metric_indigo_hover_bg": "#E4E5FF",
        "metric_magenta_bg": "#FDF0FC",
        "metric_magenta_hover_bg": "#F9E1F6",
        "metric_teal_bg": "#EAF8F4",
        "metric_teal_hover_bg": "#D9F3EB",
        "metric_amber_bg": "#FFF6E7",
        "metric_amber_hover_bg": "#FFEDCC",
        "teal": "#087A63",
        "warning": "#936000",
        "danger": "#B4233A",
        "danger_hover": "#951B30",
        "danger_text": "#FFFFFF",
        "sidebar": "#1B102E",
        "sidebar_hover": "#321B50",
        "sidebar_active": "#4B2180",
        "sidebar_toggle": "#29153F",
        "sidebar_toggle_hover": "#48206E",
        "sidebar_text": "#F3EFFB",
        "sidebar_muted": "#C5B4DB",
        "status_active_bg": "#DDF5EA",
        "status_inactive_bg": "#FFF0D6",
        "status_graduated_bg": "#EAE4FF",
        "status_active_fg": "#087A55",
        "status_inactive_fg": "#875600",
        "status_graduated_fg": "#5B36B5",
        "selection_bg": "#6D39C7",
        "selection_fg": "#FFFFFF",
        "notification_success_bg": "#DDF5EA",
        "notification_warning_bg": "#FFF0D6",
        "notification_error_bg": "#FCE6EA",
    },
    "dark": {
        "background": "#100B1D",
        "surface": "#1C1530",
        "surface_secondary": "#281F42",
        "hero_bg": "#25143D",
        "hero_border": "#63418D",
        "hero_text": "#F5EFFF",
        "hero_muted": "#C4B2DD",
        "hero_date_bg": "#3C245C",
        "hero_eyebrow": "#D1B7FF",
        "text": "#F5F0FF",
        "body_text": "#DED5F2",
        "muted": "#AA9CBD",
        "border": "#48345F",
        "border_highlight": "#654885",
        "primary": "#A78BFA",
        "primary_hover": "#C2A8FF",
        "primary_pressed": "#B69EFF",
        "secondary_hover": "#3B2A58",
        "secondary_hover_text": "#EDE4FF",
        "sidebar_active_hover": "#673BA3",
        "deep_purple": "#8B5CF6",
        "lavender": "#C4B5FD",
        "heading_text": "#D2C0FF",
        "primary_text": "#1B1230",
        "accent_violet": "#B69AFF",
        "accent_indigo": "#8D9BFF",
        "accent_magenta": "#EE8AF2",
        "accent_teal": "#5BE0BF",
        "accent_amber": "#FFD27A",
        "metric_violet_bg": "#281A3D",
        "metric_violet_hover_bg": "#32204D",
        "metric_indigo_bg": "#1B2140",
        "metric_indigo_hover_bg": "#242B50",
        "metric_magenta_bg": "#301A3A",
        "metric_magenta_hover_bg": "#3C2048",
        "metric_teal_bg": "#16332F",
        "metric_teal_hover_bg": "#1B4039",
        "metric_amber_bg": "#392B1B",
        "metric_amber_hover_bg": "#49351D",
        "teal": "#5BE0BF",
        "warning": "#FFD27A",
        "danger": "#FF8799",
        "danger_hover": "#FF6B83",
        "danger_text": "#32121B",
        "sidebar": "#140B26",
        "sidebar_hover": "#2A1747",
        "sidebar_active": "#4B2180",
        "sidebar_toggle": "#211236",
        "sidebar_toggle_hover": "#492578",
        "sidebar_text": "#F3F0FA",
        "sidebar_muted": "#B4A1D0",
        "status_active_bg": "#173B34",
        "status_inactive_bg": "#46351D",
        "status_graduated_bg": "#30254F",
        "status_active_fg": "#73E3B7",
        "status_inactive_fg": "#FFD27A",
        "status_graduated_fg": "#C5B2FF",
        "selection_bg": "#7142C2",
        "selection_fg": "#FFFFFF",
        "notification_success_bg": "#173B34",
        "notification_warning_bg": "#46351D",
        "notification_error_bg": "#482634",
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
        relief="raised",
        borderwidth=1,
        bordercolor=palette["border"],
        lightcolor=palette["border_highlight"],
        darkcolor=palette["border"],
    )
    style.configure(
        "CardHover.TFrame",
        background=palette["surface"],
        foreground=palette["text"],
        relief="raised",
        borderwidth=1,
        bordercolor=palette["primary"],
        lightcolor=palette["primary_hover"],
        darkcolor=palette["deep_purple"],
    )
    style.configure("CardInner.TFrame", background=palette["surface"])
    style.configure(
        "Hero.TFrame", background=palette["hero_bg"], relief="raised", borderwidth=1,
        bordercolor=palette["hero_border"], lightcolor=palette["border_highlight"],
        darkcolor=palette["primary"],
    )
    style.configure("HeroInner.TFrame", background=palette["hero_bg"])
    style.configure("HeroAccent.TFrame", background=palette["primary"], relief="flat")
    # A low-cost three-tone rule adds a distinct brand signature to dashboard
    # hero areas while keeping every segment theme-aware.
    style.configure("BrandViolet.TFrame", background=palette["accent_violet"], relief="flat")
    style.configure("BrandIndigo.TFrame", background=palette["accent_indigo"], relief="flat")
    style.configure("BrandMagenta.TFrame", background=palette["accent_magenta"], relief="flat")

    metric_specs = {
        "Violet": "violet",
        "Indigo": "indigo",
        "Magenta": "magenta",
        "Teal": "teal",
        "Amber": "amber",
    }
    for name, color in metric_specs.items():
        accent = palette[f"accent_{color}"]
        for hovered in (False, True):
            state = "Hover" if hovered else ""
            bg = palette[f"metric_{color}_{'hover_' if hovered else ''}bg"]
            frame_style = f"Metric{name}{state}.TFrame"
            inner_style = f"Metric{name}{state}Inner.TFrame"
            label_style = f"Metric{name}{state}Label.TLabel"
            value_style = f"Metric{name}{state}Value.TLabel"
            icon_style = f"Metric{name}{state}Icon.TLabel"
            style.configure(
                frame_style, background=bg, relief="raised", borderwidth=1,
                bordercolor=accent if hovered else palette["border"],
                lightcolor=palette["border_highlight"] if not hovered else accent,
                darkcolor=accent if hovered else palette["border"],
            )
            style.configure(inner_style, background=bg)
            style.configure(label_style, background=bg, foreground=palette["muted"],
                            font=("Segoe UI", 10, "bold"))
            style.configure(value_style, background=bg, foreground=palette["text"],
                            font=("Segoe UI", 30, "bold"))
            style.configure(icon_style, background=accent, foreground=palette["primary_text"],
                            font=("Segoe UI Symbol", 13, "bold"), padding=(9, 6))
        style.configure(f"Metric{name}Accent.TFrame", background=accent, relief="flat")
        style.configure(f"Metric{name}AccentHover.TFrame", background=palette["primary_hover"], relief="flat")

    style.configure("PageTitle.TLabel", background=palette["background"], foreground=palette["text"],
                    font=("Segoe UI", 25, "bold"))
    style.configure("HeroTitle.TLabel", background=palette["hero_bg"], foreground=palette["hero_text"],
                    font=("Segoe UI", 25, "bold"))
    style.configure("HeroSubtitle.TLabel", background=palette["hero_bg"], foreground=palette["hero_muted"],
                    font=("Segoe UI", 10))
    style.configure("HeroEyebrow.TLabel", background=palette["hero_bg"], foreground=palette["hero_eyebrow"],
                    font=("Segoe UI", 8, "bold"))
    style.configure("HeroDate.TLabel", background=palette["hero_date_bg"], foreground=palette["hero_text"],
                    font=("Segoe UI", 9, "bold"), padding=(12, 9))
    style.configure("Subtitle.TLabel", background=palette["background"], foreground=palette["muted"],
                    font=("Segoe UI", 10))
    style.configure("Date.TLabel", background=palette["surface_secondary"], foreground=palette["muted"],
                    font=("Segoe UI", 9, "bold"), padding=(12, 9))
    style.configure("SectionTitle.TLabel", background=palette["surface"], foreground=palette["heading_text"],
                    font=("Segoe UI", 14, "bold"))
    style.configure("FormSection.TFrame", background=palette["surface_secondary"],
                    relief="flat", borderwidth=0)
    style.configure("FormSectionAccent.TFrame", background=palette["primary"], relief="flat")
    style.configure("FormSectionTitle.TLabel", background=palette["surface_secondary"],
                    foreground=palette["heading_text"], font=("Segoe UI", 11, "bold"),
                    padding=(10, 7))
    style.configure("CountBadge.TLabel", background=palette["surface_secondary"],
                    foreground=palette["heading_text"], font=("Segoe UI", 9, "bold"),
                    padding=(10, 5))
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

    style.configure("TEntry", padding=10, fieldbackground=palette["surface"], foreground=palette["text"],
                    insertcolor=palette["text"], bordercolor=palette["border"],
                    lightcolor=palette["border"], darkcolor=palette["border"])
    style.map("TEntry", fieldbackground=[("disabled", palette["surface_secondary"])],
              foreground=[("disabled", palette["muted"])],
              bordercolor=[("focus", palette["primary"])],
              lightcolor=[("focus", palette["primary_hover"])],
              darkcolor=[("focus", palette["primary"])])
    style.configure("TCombobox", padding=9, fieldbackground=palette["surface"],
                    foreground=palette["text"], arrowcolor=palette["primary"],
                    bordercolor=palette["border"], lightcolor=palette["border"],
                    darkcolor=palette["border"])
    style.map("TCombobox", fieldbackground=[("readonly", palette["surface"]),
                                             ("disabled", palette["surface_secondary"])],
              foreground=[("readonly", palette["text"]), ("disabled", palette["muted"])],
              bordercolor=[("focus", palette["primary"])],
              lightcolor=[("focus", palette["primary_hover"])],
              darkcolor=[("focus", palette["primary"])])

    style.configure("Treeview", rowheight=40, font=("Segoe UI", 9),
                    background=palette["surface"], fieldbackground=palette["surface"],
                    foreground=palette["body_text"], bordercolor=palette["border"],
                    lightcolor=palette["border_highlight"], darkcolor=palette["border"])
    style.map("Treeview", background=[("selected", palette["selection_bg"]),
                                      ("active", palette["surface_secondary"])],
              foreground=[("selected", palette["selection_fg"])])
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=9,
                    background=palette["surface_secondary"], foreground=palette["heading_text"])
    style.configure("TScrollbar", background=palette["surface_secondary"],
                    troughcolor=palette["background"], arrowcolor=palette["muted"],
                    bordercolor=palette["border"], lightcolor=palette["surface"],
                    darkcolor=palette["border"])
    style.map("TScrollbar", background=[("active", palette["lavender"])])

    style.configure("TButton", padding=(14, 10), font=("Segoe UI", 9, "bold"),
                    background=palette["surface"], foreground=palette["body_text"],
                    bordercolor=palette["border"], focuscolor=palette["primary"],
                    focuswidth=2, relief="raised", borderwidth=1)
    style.map("TButton", background=[("disabled", palette["surface_secondary"]),
                                      ("pressed", palette["surface_secondary"]),
                                      ("active", palette["secondary_hover"])],
              foreground=[("disabled", palette["muted"]),
                          ("pressed", palette["heading_text"]),
                          ("active", palette["heading_text"])],
              bordercolor=[("focus", palette["primary"]),
                           ("active", palette["primary_hover"])],
              relief=[("pressed", "sunken"), ("active", "raised")])
    style.configure("Primary.TButton", padding=(17, 11), font=("Segoe UI", 10, "bold"),
                    background=palette["primary"], foreground=palette["primary_text"],
                    bordercolor=palette["primary"], focuscolor=palette["primary_hover"],
                    focuswidth=2, relief="raised", borderwidth=1)
    style.map("Primary.TButton", background=[("disabled", palette["surface_secondary"]),
                                              ("pressed", palette["primary_pressed"]),
                                              ("active", palette["primary_hover"])],
              foreground=[("disabled", palette["muted"]),
                          ("pressed", palette["primary_text"]),
                          ("active", palette["primary_text"])],
              bordercolor=[("focus", palette["primary_hover"]),
                           ("active", palette["primary_hover"])],
              relief=[("pressed", "sunken"), ("active", "raised")])
    style.configure("Secondary.TButton", padding=(15, 10), font=("Segoe UI", 9, "bold"),
                    background=palette["surface_secondary"], foreground=palette["body_text"],
                    bordercolor=palette["border"], focuscolor=palette["primary"],
                    focuswidth=2, relief="raised", borderwidth=1)
    style.map("Secondary.TButton", background=[("disabled", palette["surface_secondary"]),
                                                ("pressed", palette["border"]),
                                                ("active", palette["secondary_hover"])],
              foreground=[("disabled", palette["muted"]),
                          ("active", palette["secondary_hover_text"])],
              bordercolor=[("focus", palette["primary"]),
                           ("active", palette["primary_hover"])],
              relief=[("pressed", "sunken"), ("active", "raised")])
    style.configure("Danger.TButton", padding=(14, 9), font=("Segoe UI", 9, "bold"),
                    background=palette["danger"], foreground=palette["danger_text"],
                    bordercolor=palette["danger"], focuscolor=palette["danger_hover"],
                    focuswidth=2, relief="raised", borderwidth=1)
    style.map("Danger.TButton", background=[("disabled", palette["surface_secondary"]),
                                             ("pressed", palette["danger"]),
                                             ("active", palette["danger_hover"])],
              foreground=[("disabled", palette["muted"]), ("active", palette["danger_text"])],
              bordercolor=[("focus", palette["danger_hover"]),
                           ("active", palette["danger_hover"])],
              relief=[("pressed", "sunken"), ("active", "raised")])

    style.configure("HeroSecondary.TButton", padding=(14, 9), font=("Segoe UI", 9, "bold"),
                    background=palette["hero_date_bg"], foreground=palette["hero_text"],
                    bordercolor=palette["hero_border"], focuscolor=palette["primary"],
                    focuswidth=2, relief="raised", borderwidth=1)
    style.map("HeroSecondary.TButton", background=[("disabled", palette["surface_secondary"]),
                                                     ("pressed", palette["primary_pressed"]),
                                                     ("active", palette["primary_hover"])],
              foreground=[("disabled", palette["muted"]),
                          ("pressed", palette["primary_text"]),
                          ("active", palette["primary_text"])],
              bordercolor=[("focus", palette["primary"]),
                           ("active", palette["primary_hover"])],
              relief=[("pressed", "sunken"), ("active", "raised")])


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

    def bind_mousewheel_tree(self, widget: tk.Misc) -> None:
        """Route wheel events from nested form controls to this viewport."""
        widget.bind("<MouseWheel>", self._scroll_with_mousewheel, add="+")
        for child in widget.winfo_children():
            self.bind_mousewheel_tree(child)

    def _update_scrollregion(self, _event: tk.Event | None = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self._content_window, width=event.width)

    def _scroll_with_mousewheel(self, event: tk.Event) -> str:
        if event.delta:
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"


def bind_hover_tree(widget: tk.Misc, callback: Callable[[bool], None]) -> None:
    """Track hover across a widget and its children without layout animation.

    Tk sends enter/leave events as the pointer crosses nested labels and frames.
    Deferring leave handling until idle avoids a visible flicker between children.
    """
    pending_leave: str | None = None

    def on_enter(_event: tk.Event) -> None:
        nonlocal pending_leave
        if pending_leave is not None:
            try:
                widget.after_cancel(pending_leave)
            except tk.TclError:
                pass
            pending_leave = None
        callback(True)

    def on_leave(_event: tk.Event) -> None:
        nonlocal pending_leave

        def check_pointer() -> None:
            nonlocal pending_leave
            pending_leave = None
            try:
                pointer_x, pointer_y = widget.winfo_pointerxy()
                left, top = widget.winfo_rootx(), widget.winfo_rooty()
                inside = (
                    left <= pointer_x < left + widget.winfo_width()
                    and top <= pointer_y < top + widget.winfo_height()
                )
            except tk.TclError:
                inside = False
            if not inside:
                callback(False)

        if pending_leave is not None:
            try:
                widget.after_cancel(pending_leave)
            except tk.TclError:
                pass
        pending_leave = widget.after_idle(check_pointer)

    def bind_descendants(current: tk.Misc) -> None:
        current.bind("<Enter>", on_enter, add="+")
        current.bind("<Leave>", on_leave, add="+")
        for child in current.winfo_children():
            bind_descendants(child)

    bind_descendants(widget)


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
