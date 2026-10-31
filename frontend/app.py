"""Main window and page navigation for Campus Manager."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from frontend.views.dashboard_view import DashboardView
from frontend.views.enrollments_view import EnrollmentsView
from frontend.views.student_form import StudentFormView
from frontend.views.students_view import StudentsView
from frontend.widgets.design_system import PALETTES, configure_ttk_styles, recolor_native_widgets
from frontend.widgets.navigation import NavigationSidebar
from frontend.widgets.notifications import NotificationCenter


class StudentManagementApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Campus Manager | Student Management")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.theme = "light"
        self.palette = PALETTES[self.theme]
        self.configure(bg=self.palette["background"])
        self._configure_style()

        self.sidebar = NavigationSidebar(
            self, self.navigate, self.toggle_theme, self.theme, self.palette
        )
        self.sidebar.pack(side="left", fill="y")
        self.content = ttk.Frame(self, style="App.TFrame", padding=(32, 28))
        self.content.pack(side="left", fill="both", expand=True)
        self.notification_slot = ttk.Frame(self.content, style="App.TFrame")
        self.notification_slot.pack(fill="x")
        self.notifications = NotificationCenter(self.notification_slot, self.palette)

        self.pages = {
            "dashboard": DashboardView(self.content, self.navigate),
            "students": StudentsView(
                self.content, self.navigate, self.edit_student, self.manage_enrollments,
                self.notify,
            ),
            "registration": StudentFormView(self.content, self.navigate, self.notify),
            "enrollments": EnrollmentsView(self.content, self.navigate, self.notify),
        }
        self._apply_theme_to_views()
        self.current_page = "dashboard"
        self.navigate("dashboard")

    def _configure_style(self) -> None:
        configure_ttk_styles(ttk.Style(self), self.palette)

    def toggle_theme(self) -> None:
        """Switch the application-wide palette without rebuilding any views."""
        self.theme = "dark" if self.theme == "light" else "light"
        self.palette = PALETTES[self.theme]
        self.configure(bg=self.palette["background"])
        self._configure_style()
        recolor_native_widgets(self, self.palette)
        self.notifications.apply_theme(self.palette)
        self._apply_theme_to_views()

    def notify(self, message: str, kind: str = "success") -> None:
        """Show an application-wide, theme-aware operation notification."""
        self.notifications.show(message, kind)

    def _apply_theme_to_views(self) -> None:
        """Push the current central palette to views with native Tk widgets."""
        self.sidebar.apply_theme(self.theme, self.palette)
        for frame in getattr(self, "pages", {}).values():
            apply_theme = getattr(frame, "apply_theme", None)
            if callable(apply_theme):
                apply_theme(self.palette)

    def navigate(self, page: str) -> None:
        if page not in self.pages:
            return
        for frame in self.pages.values():
            frame.pack_forget()
        self.current_page = page
        self.sidebar.set_active(page)
        frame = self.pages[page]
        frame.pack(fill="both", expand=True)
        if hasattr(frame, "refresh"):
            frame.refresh()

    def edit_student(self, student_id: int) -> None:
        form = self.pages["registration"]
        form.load_student(student_id)
        self.navigate("registration")

    def manage_enrollments(self, student_id: int) -> None:
        view = self.pages["enrollments"]
        view.load_student(student_id)
        self.navigate("enrollments")


def main() -> None:
    StudentManagementApp().mainloop()


if __name__ == "__main__":
    main()
