"""Course enrolment management for one selected student."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections.abc import Callable
from typing import Any

from backend import enrollment_service, export_service, lookup_service, student_service


class EnrollmentsView(ttk.Frame):
    def __init__(self, master: tk.Misc, on_navigate: Callable[[str], None]) -> None:
        super().__init__(master, style="App.TFrame")
        self.on_navigate = on_navigate
        self.student_id: int | None = None
        self.student_record: dict[str, Any] | None = None
        self.course_options: list[dict[str, Any]] = []

        heading = ttk.Frame(self, style="App.TFrame")
        heading.pack(fill="x", pady=(0, 12))
        title_box = ttk.Frame(heading, style="App.TFrame")
        title_box.pack(side="left")
        ttk.Label(title_box, text="Course enrolments", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            title_box, text="Review course history and enrol students for an academic term",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))
        heading_actions = ttk.Frame(heading, style="App.TFrame")
        heading_actions.pack(side="right", anchor="s")
        self.export_button = ttk.Button(
            heading_actions,
            text="Export Enrolments CSV",
            style="Secondary.TButton",
            command=self.export_student_enrollments,
            state="disabled",
        )
        self.export_button.pack(side="left", padx=(0, 8))
        ttk.Button(
            heading_actions, text="Back to students", style="Secondary.TButton",
            command=lambda: self.on_navigate("students"),
        ).pack(side="left")

        self.student_summary = ttk.Frame(self, style="Card.TFrame", padding=(16, 10))
        self.student_summary.pack(fill="x", pady=(0, 12))
        self.student_summary_label = ttk.Label(
            self.student_summary, text="Select a student from the Students screen.",
            background="#ffffff", foreground="#172235", font=("Segoe UI", 10, "bold"),
        )
        self.student_summary_label.pack(anchor="w")

        main = ttk.Frame(self, style="App.TFrame")
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1, minsize=300)
        main.columnconfigure(1, weight=2, minsize=460)
        main.rowconfigure(0, weight=1)

        add_panel = ttk.Frame(main, style="Card.TFrame", padding=14)
        add_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        add_panel.columnconfigure(0, weight=1)
        ttk.Label(add_panel, text="Add courses", background="#ffffff",
                  foreground="#172235", font=("Segoe UI", 12, "bold")).grid(
                      row=0, column=0, sticky="w", pady=(0, 6)
                  )
        ttk.Label(
            add_panel,
            text="Choose one or more courses. Each option shows its owning programme.",
            background="#ffffff", foreground="#66758a", wraplength=320,
        ).grid(row=1, column=0, sticky="w", pady=(0, 7))

        list_frame = ttk.Frame(add_panel, style="Card.TFrame")
        list_frame.grid(row=2, column=0, sticky="nsew")
        add_panel.rowconfigure(2, weight=1)
        self.course_list = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED, exportselection=False,
            font=("Segoe UI", 9), relief="solid", bd=1, activestyle="dotbox",
            height=8,
        )
        course_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.course_list.yview)
        self.course_list.configure(yscrollcommand=course_scroll.set)
        self.course_list.pack(side="left", fill="both", expand=True)
        course_scroll.pack(side="right", fill="y")

        ttk.Label(add_panel, text="Academic year (YYYY-YYYY)", background="#ffffff").grid(
            row=3, column=0, sticky="w", pady=(9, 2)
        )
        self.academic_year_var = tk.StringVar()
        ttk.Entry(add_panel, textvariable=self.academic_year_var).grid(
            row=4, column=0, sticky="ew"
        )
        term_row = ttk.Frame(add_panel, style="Card.TFrame")
        term_row.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        term_row.columnconfigure(0, weight=1)
        term_row.columnconfigure(1, weight=1)
        ttk.Label(term_row, text="Semester", background="#ffffff").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Label(term_row, text="New status", background="#ffffff").grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        self.semester_var = tk.StringVar(value="Semester 1")
        self.semester_combo = ttk.Combobox(
            term_row, textvariable=self.semester_var, state="readonly",
            values=("Semester 1", "Semester 2", "Summer"),
        )
        self.semester_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(2, 0))
        self.new_status_var = tk.StringVar(value="Enrolled")
        self.new_status_combo = ttk.Combobox(
            term_row, textvariable=self.new_status_var, state="readonly",
            values=("Enrolled", "Completed", "Dropped"),
        )
        self.new_status_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(2, 0))
        ttk.Button(add_panel, text="Enrol selected courses", style="Primary.TButton",
                   command=self.add_selected_courses).grid(
                       row=6, column=0, sticky="w", pady=(10, 0)
                   )

        records_panel = ttk.Frame(main, style="Card.TFrame", padding=12)
        records_panel.grid(row=0, column=1, sticky="nsew")
        records_panel.rowconfigure(1, weight=1)
        records_panel.columnconfigure(0, weight=1)
        ttk.Label(records_panel, text="Current enrolments", background="#ffffff",
                  foreground="#172235", font=("Segoe UI", 12, "bold")).grid(
                      row=0, column=0, sticky="w", pady=(0, 6)
                  )
        columns = (
            "student_course_id", "course_name", "course_code", "course_program_name",
            "academic_year", "semester", "grade", "enrollment_status",
        )
        self.enrollment_table = ttk.Treeview(
            records_panel, columns=columns, show="headings", selectmode="browse", height=8
        )
        labels = {
            "student_course_id": ("ID", 42),
            "course_name": ("Course", 150),
            "course_code": ("Code", 65),
            "course_program_name": ("Owning programme", 155),
            "academic_year": ("Year", 78),
            "semester": ("Semester", 90),
            "grade": ("Grade", 55),
            "enrollment_status": ("Status", 85),
        }
        for column, (label, width) in labels.items():
            self.enrollment_table.heading(column, text=label)
            self.enrollment_table.column(column, width=width, minwidth=45, anchor="w")
        y_scroll = ttk.Scrollbar(records_panel, orient="vertical", command=self.enrollment_table.yview)
        x_scroll = ttk.Scrollbar(records_panel, orient="horizontal", command=self.enrollment_table.xview)
        self.enrollment_table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.enrollment_table.grid(row=1, column=0, sticky="nsew")
        y_scroll.grid(row=1, column=1, sticky="ns")
        x_scroll.grid(row=2, column=0, sticky="ew")
        self.enrollment_table.bind("<<TreeviewSelect>>", self._select_enrollment)

        edit_row = ttk.Frame(records_panel, style="Card.TFrame")
        edit_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        edit_row.columnconfigure(1, weight=1)
        edit_row.columnconfigure(3, weight=1)
        ttk.Label(edit_row, text="Grade", background="#ffffff").grid(row=0, column=0, sticky="w")
        self.grade_var = tk.StringVar()
        ttk.Combobox(
            edit_row, textvariable=self.grade_var, state="readonly",
            values=("", "O", "A+", "A", "B+", "B", "C", "P", "F"), width=7,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 12))
        ttk.Label(edit_row, text="Status", background="#ffffff").grid(row=0, column=2, sticky="w")
        self.status_var = tk.StringVar()
        ttk.Combobox(
            edit_row, textvariable=self.status_var, state="readonly",
            values=("Enrolled", "Completed", "Dropped"), width=12,
        ).grid(row=0, column=3, sticky="ew", padx=(6, 12))
        ttk.Button(edit_row, text="Update", style="Secondary.TButton",
                   command=self.update_selected).grid(row=0, column=4, padx=(0, 7))
        ttk.Button(edit_row, text="Remove", style="Secondary.TButton",
                   command=self.remove_selected).grid(row=0, column=5)

        self.status_message = ttk.Label(self, text="", style="Subtitle.TLabel")
        self.status_message.pack(anchor="w", pady=(8, 0))

    def load_student(self, student_id: int) -> None:
        self.student_id = int(student_id)

    def refresh(self) -> None:
        if self.student_id is None:
            self.student_record = None
            self.student_summary_label.configure(
                text="Select a student from the Students screen to manage course enrolments."
            )
            self._load_enrollments([])
            self._load_courses([])
            self.status_message.configure(text="")
            return
        try:
            self.student_record = student_service.get_student(self.student_id)
            if self.student_record is None:
                self.student_summary_label.configure(text="Student record was not found.")
                self._load_enrollments([])
                self._load_courses([])
                return
            record = self.student_record
            name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
            self.student_summary_label.configure(
                text=(
                    f"{record.get('student_number', '')}   |   {name}   |   "
                    f"{record.get('program_name', '')}"
                )
            )
            self._load_courses(lookup_service.list_courses_for_cross_programme_enrolment())
            self._load_enrollments(enrollment_service.list_student_enrollments(self.student_id))
            self.status_message.configure(text="")
        except Exception:
            self.export_button.configure(state="disabled")
            self.status_message.configure(
                text="Could not load enrolment data. Check the database settings and server."
            )

    def _load_courses(self, rows: list[dict[str, Any]]) -> None:
        self.course_options = rows
        self.course_list.delete(0, "end")
        for row in rows:
            self.course_list.insert(
                "end",
                f"{row.get('course_code', '')} | {row.get('course_name', '')} | "
                f"{row.get('program_name', '')}",
            )

    def _load_enrollments(self, rows: list[dict[str, Any]]) -> None:
        self.enrollment_table.delete(*self.enrollment_table.get_children())
        for row in rows:
            self.enrollment_table.insert("", "end", values=(
                row.get("student_course_id"),
                row.get("course_name"),
                row.get("course_code"),
                row.get("course_program_name"),
                row.get("academic_year"),
                row.get("semester"),
                row.get("grade") or "",
                row.get("enrollment_status"),
            ))
        self.grade_var.set("")
        self.status_var.set("")
        self.export_button.configure(
            state="normal" if rows and self.student_record is not None else "disabled"
        )

    def export_student_enrollments(self) -> None:
        if self.student_id is None or self.student_record is None:
            messagebox.showinfo(
                "Select a student",
                "Open this screen from a student record before exporting enrolments.",
                parent=self,
            )
            return

        destination = filedialog.asksaveasfilename(
            parent=self,
            title="Export student enrolments to CSV",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            initialfile="student_enrolments.csv",
        )
        if not destination:
            return

        try:
            records = enrollment_service.list_student_enrollments(self.student_id)
        except Exception:
            messagebox.showerror(
                "Enrolment export failed",
                "The student's enrolments could not be loaded for export.",
                parent=self,
            )
            return

        if not records:
            self.export_button.configure(state="disabled")
            messagebox.showinfo(
                "No enrolments",
                "There are no course enrolments for this student to export.",
                parent=self,
            )
            return

        try:
            count = export_service.export_enrollments(records, destination)
        except Exception:
            messagebox.showerror(
                "Enrolment export failed",
                "The CSV file could not be written. Check the destination and try again.",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Enrolment export complete",
            f"Exported {count} enrolment record(s).",
            parent=self,
        )

    def add_selected_courses(self) -> None:
        if self.student_id is None or self.student_record is None:
            messagebox.showinfo("Select a student", "Open this screen from a student record.", parent=self)
            return
        selected = self.course_list.curselection()
        if not selected:
            messagebox.showinfo("Select courses", "Choose one or more courses to enrol.", parent=self)
            return
        course_ids = [int(self.course_options[index]["course_id"]) for index in selected]
        try:
            enrollment_service.enroll_courses(
                self.student_id,
                course_ids,
                self.academic_year_var.get(),
                self.semester_var.get(),
                self.new_status_var.get(),
            )
        except ValueError as error:
            messagebox.showwarning("Could not enrol courses", str(error), parent=self)
            return
        except Exception:
            messagebox.showerror(
                "Could not enrol courses", "The course enrolment could not be saved.", parent=self
            )
            return
        self.refresh()

    def _select_enrollment(self, _event: tk.Event | None = None) -> None:
        selected = self.enrollment_table.selection()
        if not selected:
            return
        values = self.enrollment_table.item(selected[0], "values")
        self.grade_var.set(values[6] or "")
        self.status_var.set(values[7] or "Enrolled")

    def update_selected(self) -> None:
        selected = self.enrollment_table.selection()
        if not selected:
            messagebox.showinfo("Select an enrolment", "Choose an enrolment row first.", parent=self)
            return
        values = self.enrollment_table.item(selected[0], "values")
        enrollment_id = int(values[0])
        try:
            updated = enrollment_service.update_enrollment(
                enrollment_id, self.grade_var.get() or None, self.status_var.get()
            )
        except ValueError as error:
            messagebox.showwarning("Could not update enrolment", str(error), parent=self)
            return
        except Exception:
            messagebox.showerror(
                "Could not update enrolment", "The enrolment could not be updated.", parent=self
            )
            return
        if not updated:
            messagebox.showinfo("Enrolment not found", "The enrolment no longer exists.", parent=self)
        self.refresh()

    def remove_selected(self) -> None:
        selected = self.enrollment_table.selection()
        if not selected:
            messagebox.showinfo("Select an enrolment", "Choose an enrolment row first.", parent=self)
            return
        values = self.enrollment_table.item(selected[0], "values")
        enrollment_id = int(values[0])
        course_text = f"{values[2]} — {values[1]}"
        if not messagebox.askyesno(
            "Remove enrolment",
            f"Remove {course_text} from this student's enrolment records?",
            parent=self,
        ):
            return
        try:
            removed = enrollment_service.remove_enrollment(enrollment_id)
        except Exception:
            messagebox.showerror(
                "Could not remove enrolment", "The enrolment could not be removed.", parent=self
            )
            return
        if not removed:
            messagebox.showinfo("Enrolment not found", "The enrolment no longer exists.", parent=self)
        self.refresh()
