"""Student records table with search, editing, deletion, and enrolment access."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from backend import export_service, student_service


class StudentsView(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_navigate: Callable[[str], None],
        on_edit: Callable[[int], None],
        on_manage_enrollments: Callable[[int], None],
    ) -> None:
        super().__init__(master, style="App.TFrame")
        self.on_navigate = on_navigate
        self.on_edit = on_edit
        self.on_manage_enrollments = on_manage_enrollments
        self.records: list[dict[str, Any]] = []

        heading = ttk.Frame(self, style="App.TFrame")
        heading.pack(fill="x", pady=(0, 22))
        title_box = ttk.Frame(heading, style="App.TFrame")
        title_box.pack(side="left")
        ttk.Label(title_box, text="Student records", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            title_box,
            text="Search, review, and manage registered students",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 0))
        heading_actions = ttk.Frame(heading, style="App.TFrame")
        heading_actions.pack(side="right", anchor="s")
        ttk.Button(
            heading_actions,
            text="Export Students CSV",
            style="Secondary.TButton",
            command=self.export_students_csv,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            heading_actions,
            text="+ Register student",
            style="Primary.TButton",
            command=lambda: on_navigate("registration"),
        ).pack(side="left")

        toolbar = ttk.Frame(self, style="Card.TFrame", padding=12)
        toolbar.pack(fill="x", pady=(0, 14))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=36)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda _event: self.search())
        ttk.Button(toolbar, text="Search", style="Primary.TButton", command=self.search).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(toolbar, text="Clear", style="Secondary.TButton", command=self.clear_search).pack(
            side="left"
        )
        ttk.Button(toolbar, text="Refresh", style="Secondary.TButton", command=self.refresh).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(toolbar, text="Delete", style="Secondary.TButton",
                   command=self.delete_selected).pack(side="right")
        ttk.Button(toolbar, text="Edit", style="Secondary.TButton",
                   command=self.edit_selected).pack(side="right", padx=(0, 8))
        ttk.Button(toolbar, text="Manage Courses", style="Secondary.TButton",
                   command=self.manage_selected).pack(side="right", padx=(0, 8))

        table_panel = ttk.Frame(self, style="Card.TFrame", padding=10)
        table_panel.pack(fill="both", expand=True)
        columns = (
            "student_id", "student_number", "name", "program", "department",
            "admission_date", "status",
        )
        self.table = ttk.Treeview(table_panel, columns=columns, show="headings", selectmode="browse")
        labels = {
            "student_id": ("ID", 55),
            "student_number": ("Student number", 135),
            "name": ("Student name", 180),
            "program": ("Programme", 300),
            "department": ("Department", 175),
            "admission_date": ("Admission date", 125),
            "status": ("Status", 100),
        }
        for column, (label, width) in labels.items():
            self.table.heading(column, text=label)
            minwidth = 220 if column == "program" else 55
            self.table.column(column, width=width, minwidth=minwidth, anchor="w")
        y_scroll = ttk.Scrollbar(table_panel, orient="vertical", command=self.table.yview)
        x_scroll = ttk.Scrollbar(table_panel, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_panel.rowconfigure(0, weight=1)
        table_panel.columnconfigure(0, weight=1)
        self.table.bind("<Double-1>", lambda _event: self.edit_selected())

        footer = ttk.Frame(self, style="App.TFrame")
        footer.pack(fill="x", pady=(10, 0))
        self.status = ttk.Label(footer, text="", style="Subtitle.TLabel")
        self.status.pack(side="left")

    def refresh(self) -> None:
        query = self.search_var.get().strip()
        try:
            rows = student_service.search_students(query) if query else student_service.list_students()
            self._load(rows)
        except Exception:
            self._database_error()

    def search(self) -> None:
        try:
            self._load(student_service.search_students(self.search_var.get().strip()))
        except Exception:
            self._database_error()

    def clear_search(self) -> None:
        self.search_var.set("")
        self.refresh()

    def _load(self, records: list[dict[str, Any]]) -> None:
        self.records = records
        self.table.delete(*self.table.get_children())
        for row in records:
            name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            admission_date = self._format_admission_date(row.get("admission_date"))
            self.table.insert("", "end", values=(
                row.get("student_id"),
                row.get("student_number"),
                name,
                row.get("program_name"),
                row.get("department_name"),
                admission_date or "",
                row.get("status"),
            ))
        self.status.configure(text=f"{len(records):,} student record(s)")

    @staticmethod
    def _format_admission_date(value: Any) -> str:
        """Format an ISO date for the table, leaving missing dates blank."""
        if value is None or value == "":
            return ""
        if isinstance(value, datetime):
            return value.strftime("%d-%m-%Y")
        if isinstance(value, date):
            return value.strftime("%d-%m-%Y")

        text = str(value).strip()
        if not text:
            return ""
        try:
            parsed = date.fromisoformat(text)
        except ValueError:
            return text
        return parsed.strftime("%d-%m-%Y")

    def _database_error(self) -> None:
        self.status.configure(text="Could not load student records. Check database settings and server.")

    def _selected_id(self) -> int | None:
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("Select a student", "Choose a student record first.", parent=self)
            return None
        return int(self.table.item(selected[0], "values")[0])

    def edit_selected(self) -> None:
        student_id = self._selected_id()
        if student_id is not None:
            self.on_edit(student_id)

    def manage_selected(self) -> None:
        student_id = self._selected_id()
        if student_id is not None:
            self.on_manage_enrollments(student_id)

    def export_students_csv(self) -> None:
        destination = filedialog.asksaveasfilename(
            parent=self,
            title="Export students to CSV",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            initialfile="students.csv",
        )
        if not destination:
            return

        try:
            records = student_service.list_students()
        except Exception:
            messagebox.showerror(
                "Student export failed",
                "Student records could not be loaded for export.",
                parent=self,
            )
            return

        if not records:
            messagebox.showinfo(
                "No student records",
                "There are no student records to export.",
                parent=self,
            )
            return

        try:
            count = export_service.export_students(records, destination)
        except Exception:
            messagebox.showerror(
                "Student export failed",
                "The CSV file could not be written. Check the destination and try again.",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Student export complete",
            f"Exported {count} student record(s).",
            parent=self,
        )

    def delete_selected(self) -> None:
        student_id = self._selected_id()
        if student_id is None:
            return
        if not messagebox.askyesno("Delete student", "Delete this student record?", parent=self):
            return
        try:
            deleted = student_service.remove_student(student_id)
        except ValueError:
            messagebox.showwarning(
                "Student cannot be deleted",
                "This student cannot be deleted because academic enrolment records exist. "
                "Manage the enrolments explicitly before deleting the student.",
                parent=self,
            )
            return
        except Exception:
            messagebox.showerror(
                "Delete failed", "The student record could not be deleted.", parent=self
            )
            return
        if not deleted:
            messagebox.showinfo("Student not found", "The student record no longer exists.", parent=self)
        self.refresh()
