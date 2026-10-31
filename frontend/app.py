"""Main window and page navigation for Campus Manager."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from frontend.views.dashboard_view import DashboardView
from frontend.views.enrollments_view import EnrollmentsView
from frontend.views.student_form import StudentFormView
from frontend.views.students_view import StudentsView
from frontend.widgets.navigation import NavigationSidebar


class StudentManagementApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Campus Manager | Student Management")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.configure(bg="#f3f6fa")
        self._configure_style()

        self.sidebar = NavigationSidebar(self, self.navigate)
        self.sidebar.pack(side="left", fill="y")
        self.content = ttk.Frame(self, style="App.TFrame", padding=(32, 28))
        self.content.pack(side="left", fill="both", expand=True)

        self.pages = {
            "dashboard": DashboardView(self.content, self.navigate),
            "students": StudentsView(
                self.content, self.navigate, self.edit_student, self.manage_enrollments
            ),
            "registration": StudentFormView(self.content, self.navigate),
            "enrollments": EnrollmentsView(self.content, self.navigate),
        }
        self.current_page = "dashboard"
        self.navigate("dashboard")

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#f3f6fa")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("PageTitle.TLabel", background="#f3f6fa", foreground="#172235",
                        font=("Segoe UI", 24, "bold"))
        style.configure("Subtitle.TLabel", background="#f3f6fa", foreground="#66758a",
                        font=("Segoe UI", 10))
        style.configure("CardLabel.TLabel", background="#ffffff", foreground="#66758a",
                        font=("Segoe UI", 10))
        style.configure("CardValue.TLabel", background="#ffffff", foreground="#172235",
                        font=("Segoe UI", 25, "bold"))
        style.configure("TLabel", background="#f3f6fa", foreground="#25344a",
                        font=("Segoe UI", 10))
        style.configure("TEntry", padding=9, fieldbackground="#ffffff")
        style.configure("TCombobox", padding=8)
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 9),
                        background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=9)
        style.configure("Primary.TButton", padding=(16, 10), font=("Segoe UI", 9, "bold"))
        style.configure("Secondary.TButton", padding=(14, 9), font=("Segoe UI", 9))

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
