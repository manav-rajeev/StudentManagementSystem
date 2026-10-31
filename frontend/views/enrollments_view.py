"""Course enrolment workspace for selecting courses and managing records."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, ttk
from typing import Any

from backend import enrollment_service, export_service, lookup_service, student_service


SEMESTERS = ("Semester 1", "Semester 2", "Summer")
ENROLLMENT_STATUSES = ("Enrolled", "Completed", "Dropped")
GRADES = ("", "O", "A+", "A", "B+", "B", "C", "P", "F")


class EnrollmentsView(ttk.Frame):
    """Manage a student's course enrolments through the existing services."""

    def __init__(
        self,
        master: tk.Misc,
        on_navigate: Callable[[str], None],
        on_notify: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__(master, style="App.TFrame")
        self.on_navigate = on_navigate
        self.on_notify = on_notify
        self.student_id: int | None = None
        self.student_record: dict[str, Any] | None = None
        self.student_options: list[dict[str, Any]] = []
        self.student_display_to_id: dict[str, int] = {}
        self.course_options: list[dict[str, Any]] = []
        self.visible_courses: list[dict[str, Any]] = []
        self.selected_course_ids: set[int] = set()
        self._courses_loaded = False
        self._updating_course_list = False
        self.palette: dict[str, str] = {}
        self.confirmation_windows: list[tk.Toplevel] = []
        self.danger_buttons: list[tk.Button] = []
        self.feedback_kind = "muted"

        self._build_header()
        self._build_student_picker()
        self._build_workspace()
        self._build_feedback()

    def _build_header(self) -> None:
        heading = ttk.Frame(self, style="App.TFrame")
        heading.pack(fill="x", pady=(0, 18))
        title_box = ttk.Frame(heading, style="App.TFrame")
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(title_box, text="Course Enrolments", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            title_box,
            text="Select a student, add courses, and review their academic record.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 0))
        actions = ttk.Frame(heading, style="App.TFrame")
        actions.pack(side="right", anchor="s")
        self.export_button = ttk.Button(
            actions,
            text="Export Enrolments CSV",
            style="Secondary.TButton",
            command=self.export_student_enrollments,
            state="disabled",
        )
        self.export_button.pack(side="left", padx=(0, 8))
        ttk.Button(
            actions,
            text="Back to students",
            style="Secondary.TButton",
            command=lambda: self.on_navigate("students"),
        ).pack(side="left")

    def _build_student_picker(self) -> None:
        panel = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        panel.pack(fill="x", pady=(0, 16))
        header = ttk.Frame(panel, style="CardInner.TFrame")
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Student", style="SectionTitle.TLabel").pack(side="left")
        self.student_search_status = ttk.Label(header, text="", style="CardLabel.TLabel")
        self.student_search_status.pack(side="right")

        search_row = ttk.Frame(panel, style="CardInner.TFrame")
        search_row.pack(fill="x")
        ttk.Label(search_row, text="Find by student number or name", style="CardLabel.TLabel").pack(
            side="left", padx=(0, 10)
        )
        self.student_search_var = tk.StringVar()
        self.student_search_entry = ttk.Combobox(
            search_row,
            textvariable=self.student_search_var,
            state="normal",
            width=38,
        )
        self.student_search_entry.pack(side="left", fill="x", expand=True)
        self.student_search_entry.bind("<KeyRelease>", self._filter_student_options)
        self.student_search_entry.bind("<<ComboboxSelected>>", self._select_student_option)

        self.student_summary_label = ttk.Label(
            panel,
            text="Select a student from the Students screen or search above.",
            style="CardLabel.TLabel",
            font=("Segoe UI", 10, "bold"),
        )
        self.student_summary_label.pack(anchor="w", pady=(9, 0))

    def _build_workspace(self) -> None:
        main = ttk.Frame(self, style="App.TFrame")
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1, minsize=300)
        main.columnconfigure(1, weight=2, minsize=460)
        main.rowconfigure(0, weight=1)

        self._build_add_panel(main)
        self._build_records_panel(main)

    def _build_add_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=14)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(3, weight=1)

        ttk.Label(panel, text="Add courses", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            panel,
            text="Search and select one or more courses. Each course shows its owning programme.",
            style="CardLabel.TLabel",
            wraplength=340,
        ).grid(row=1, column=0, sticky="w", pady=(5, 10))

        course_search_row = ttk.Frame(panel, style="CardInner.TFrame")
        course_search_row.grid(row=2, column=0, sticky="ew", pady=(0, 7))
        course_search_row.columnconfigure(0, weight=1)
        self.course_search_var = tk.StringVar()
        self.course_search_entry = ttk.Entry(course_search_row, textvariable=self.course_search_var)
        self.course_search_entry.grid(row=0, column=0, sticky="ew")
        self.course_search_entry.bind("<KeyRelease>", self._filter_courses)

        self.course_search_status = ttk.Label(panel, text="", style="CardLabel.TLabel")
        self.course_search_status.grid(row=3, column=0, sticky="w", pady=(0, 4))

        list_frame = ttk.Frame(panel, style="CardInner.TFrame")
        list_frame.grid(row=4, column=0, sticky="nsew")
        panel.rowconfigure(4, weight=1)
        self.course_list = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            exportselection=False,
            font=("Segoe UI", 9),
            relief="solid",
            bd=1,
            activestyle="dotbox",
            height=8,
        )
        course_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.course_list.yview)
        self.course_list.configure(yscrollcommand=course_scroll.set)
        self.course_list.pack(side="left", fill="both", expand=True)
        course_scroll.pack(side="right", fill="y")
        self.course_list.bind("<<ListboxSelect>>", self._course_selection_changed)

        selection_row = ttk.Frame(panel, style="CardInner.TFrame")
        selection_row.grid(row=5, column=0, sticky="ew", pady=(5, 0))
        self.course_selection_label = ttk.Label(selection_row, text="No courses selected", style="CardLabel.TLabel")
        self.course_selection_label.pack(anchor="w")

        ttk.Separator(panel).grid(row=6, column=0, sticky="ew", pady=(12, 10))
        ttk.Label(panel, text="Academic year (YYYY-YYYY)", style="CardLabel.TLabel").grid(
            row=7, column=0, sticky="w", pady=(0, 4)
        )
        self.academic_year_var = tk.StringVar()
        self.academic_year_entry = ttk.Entry(panel, textvariable=self.academic_year_var)
        self.academic_year_entry.grid(row=8, column=0, sticky="ew")

        term_row = ttk.Frame(panel, style="CardInner.TFrame")
        term_row.grid(row=9, column=0, sticky="ew", pady=(9, 0))
        term_row.columnconfigure(0, weight=1)
        term_row.columnconfigure(1, weight=1)
        ttk.Label(term_row, text="Semester", style="CardLabel.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4)
        )
        ttk.Label(term_row, text="New status", style="CardLabel.TLabel").grid(
            row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 4)
        )
        self.semester_var = tk.StringVar(value=SEMESTERS[0])
        self.semester_combo = ttk.Combobox(
            term_row, textvariable=self.semester_var, state="readonly", values=SEMESTERS
        )
        self.semester_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.new_status_var = tk.StringVar(value=ENROLLMENT_STATUSES[0])
        self.new_status_combo = ttk.Combobox(
            term_row, textvariable=self.new_status_var, state="readonly", values=ENROLLMENT_STATUSES
        )
        self.new_status_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self.add_button = ttk.Button(
            panel,
            text="Enrol selected courses",
            style="Primary.TButton",
            command=self.add_selected_courses,
        )
        self.add_button.grid(row=10, column=0, sticky="ew", pady=(12, 0))

    def _build_records_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Card.TFrame", padding=12)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        title_row = ttk.Frame(panel, style="CardInner.TFrame")
        title_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(title_row, text="Current enrolments", style="SectionTitle.TLabel").pack(side="left")
        self.enrollment_count_label = ttk.Label(title_row, text="0 records", style="CardLabel.TLabel")
        self.enrollment_count_label.pack(side="right")

        columns = (
            "course_code", "course_name", "course_program_name", "academic_year",
            "semester", "grade", "enrollment_status",
        )
        self.enrollment_table = ttk.Treeview(
            panel, columns=columns, show="headings", selectmode="browse", height=8
        )
        labels = {
            "course_code": ("Code", 80),
            "course_name": ("Course", 175),
            "course_program_name": ("Owning programme", 165),
            "academic_year": ("Academic year", 104),
            "semester": ("Semester", 92),
            "grade": ("Grade", 65),
            "enrollment_status": ("Status", 100),
        }
        for column, (label, width) in labels.items():
            self.enrollment_table.heading(column, text=label)
            self.enrollment_table.column(column, width=width, minwidth=55, anchor="w", stretch=True)
        y_scroll = ttk.Scrollbar(panel, orient="vertical", command=self.enrollment_table.yview)
        x_scroll = ttk.Scrollbar(panel, orient="horizontal", command=self.enrollment_table.xview)
        self.enrollment_table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.enrollment_table.grid(row=1, column=0, sticky="nsew")
        y_scroll.grid(row=1, column=1, sticky="ns")
        x_scroll.grid(row=2, column=0, sticky="ew")
        self.enrollment_table.bind("<<TreeviewSelect>>", self._select_enrollment)

        edit_panel = ttk.Frame(panel, style="CardInner.TFrame", padding=(0, 10, 0, 0))
        edit_panel.grid(row=3, column=0, columnspan=2, sticky="ew")
        edit_panel.columnconfigure(1, weight=1)
        edit_panel.columnconfigure(3, weight=1)
        self.selected_enrollment_label = ttk.Label(
            edit_panel, text="Select an enrolment to update its grade or status.", style="CardLabel.TLabel"
        )
        self.selected_enrollment_label.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))
        ttk.Label(edit_panel, text="Grade", style="CardLabel.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 6)
        )
        self.grade_var = tk.StringVar()
        self.grade_combo = ttk.Combobox(
            edit_panel, textvariable=self.grade_var, state="readonly", values=GRADES, width=7
        )
        self.grade_combo.grid(row=1, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(edit_panel, text="Status", style="CardLabel.TLabel").grid(
            row=1, column=2, sticky="w", padx=(0, 6)
        )
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(
            edit_panel, textvariable=self.status_var, state="readonly", values=ENROLLMENT_STATUSES, width=12
        )
        self.status_combo.grid(row=1, column=3, sticky="ew", padx=(0, 12))
        self.update_button = ttk.Button(
            edit_panel, text="Update", style="Primary.TButton", command=self.update_selected, state="disabled"
        )
        self.update_button.grid(row=1, column=4, padx=(0, 8))
        self.remove_button = self._make_danger_button(
            edit_panel, text="Remove", command=self.remove_selected
        )
        self.remove_button.grid(row=1, column=5)
        self.remove_button.configure(state="disabled")

    def _build_feedback(self) -> None:
        self.feedback_label = ttk.Label(self, text="", style="Subtitle.TLabel")
        self.feedback_label.pack(anchor="w", pady=(9, 0))

    def apply_theme(self, palette: dict[str, str]) -> None:
        """Update native controls and status-tag colors from the central palette."""
        self.palette = palette
        self.course_list.configure(
            background=palette["surface"],
            foreground=palette["body_text"],
            selectbackground=palette["sidebar_active"],
            selectforeground=palette["sidebar_text"],
            highlightbackground=palette["border"],
            highlightcolor=palette["primary"],
            selectborderwidth=0,
        )
        self.enrollment_table.tag_configure(
            "enrolled", background=palette["status_active_bg"], foreground=palette["body_text"]
        )
        self.enrollment_table.tag_configure(
            "completed", background=palette["status_graduated_bg"], foreground=palette["body_text"]
        )
        self.enrollment_table.tag_configure(
            "dropped", background=palette["status_inactive_bg"], foreground=palette["body_text"]
        )
        self._set_feedback_color()
        for window in list(self.confirmation_windows):
            try:
                if window.winfo_exists():
                    window.configure(bg=palette["background"])
            except tk.TclError:
                self.confirmation_windows.remove(window)
        for button in self.danger_buttons:
            try:
                if button.winfo_exists():
                    self._style_danger_button(button)
            except tk.TclError:
                self.danger_buttons.remove(button)

    def load_student(self, student_id: int) -> None:
        """Preserve the existing Students-screen callback entry point."""
        student_id = int(student_id)
        if student_id != self.student_id:
            self.selected_course_ids.clear()
            if hasattr(self, "course_list"):
                self._updating_course_list = True
                self.course_list.selection_clear(0, "end")
                self._updating_course_list = False
                self._update_course_selection_label()
        self.student_id = student_id

    def refresh(self) -> None:
        """Reload student options and the selected student's enrolments."""
        self._set_feedback("")
        try:
            self.student_options = list(student_service.list_students())
            self.student_display_to_id = {
                self._student_display(row): int(row["student_id"])
                for row in self.student_options
            }
            self._update_student_combo_values()
        except Exception:
            self.student_search_status.configure(
                text="Student search is unavailable. Check the database connection."
            )

        if self.student_id is None:
            self.student_record = None
            self.student_summary_label.configure(
                text="Select a student from the Students screen or search above."
            )
            self.course_search_status.configure(text="Select a student to load courses.")
            self._load_enrollments([])
            return

        try:
            self.student_record = self._student_from_options(self.student_id)
            if self.student_record is None:
                self.student_record = student_service.get_student(self.student_id)
            if self.student_record is None:
                self.student_summary_label.configure(text="Student record was not found.")
                self._load_enrollments([])
                self.selected_course_ids.clear()
                self._filter_courses()
                self._set_feedback("That student record is no longer available.", "error")
                return

            self._show_student_summary(self.student_record)
            selected_display = self._student_display(self.student_record)
            if selected_display in self.student_display_to_id:
                self.student_search_var.set(selected_display)

            if not self._courses_loaded:
                self._load_courses(lookup_service.list_courses_for_cross_programme_enrolment())
                self._courses_loaded = True
            self._refresh_enrollments()
        except Exception:
            self.export_button.configure(state="disabled")
            self._set_feedback("Could not load enrolment data. Check the database settings and server.", "error")

    @staticmethod
    def _student_display(row: dict[str, Any]) -> str:
        number = str(row.get("student_number") or "").strip()
        name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
        return f"{number}  |  {name}" if number else name

    def _student_from_options(self, student_id: int) -> dict[str, Any] | None:
        for record in self.student_options:
            if int(record.get("student_id", -1)) == student_id:
                return record
        return None

    def _update_student_combo_values(self) -> None:
        query = self.student_search_var.get().strip().casefold()
        matching = []
        for row in self.student_options:
            number = str(row.get("student_number") or "")
            name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
            display = self._student_display(row).casefold()
            if not query or query in number.casefold() or query in name.casefold() or query in display:
                matching.append(self._student_display(row))
        self.student_search_entry.configure(values=matching)
        if query and not matching:
            self.student_search_status.configure(text="No students match that search.")
        elif query:
            self.student_search_status.configure(text=f"{len(matching):,} match(es)")
        else:
            self.student_search_status.configure(text=f"{len(matching):,} student(s)")

    def _filter_student_options(self, _event: tk.Event | None = None) -> None:
        self._update_student_combo_values()

    def _select_student_option(self, _event: tk.Event | None = None) -> None:
        selected_id = self.student_display_to_id.get(self.student_search_var.get())
        if selected_id is None:
            self._set_feedback("Choose a student from the search suggestions.", "error")
            return
        if selected_id == self.student_id:
            return
        self.load_student(selected_id)
        self.refresh()

    def _show_student_summary(self, record: dict[str, Any]) -> None:
        name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
        number = record.get("student_number", "")
        program = record.get("program_name", "")
        self.student_summary_label.configure(
            text=f"Managing enrolments for  {number}  ·  {name}  ·  {program}"
        )

    def _load_courses(self, rows: list[dict[str, Any]]) -> None:
        self.course_options = list(rows)
        self.visible_courses = []
        self.selected_course_ids.clear()
        self._updating_course_list = True
        self.course_list.delete(0, "end")
        self._updating_course_list = False
        self._filter_courses()

    def _filter_courses(self, _event: tk.Event | None = None) -> None:
        self._remember_course_selection()
        query = self.course_search_var.get().strip().casefold()
        self.visible_courses = []
        for row in self.course_options:
            code = str(row.get("course_code") or "")
            name = str(row.get("course_name") or "")
            if not query or query in code.casefold() or query in name.casefold():
                self.visible_courses.append(row)

        self._updating_course_list = True
        self.course_list.delete(0, "end")
        for index, row in enumerate(self.visible_courses):
            text = (
                f"{row.get('course_code', '')}  ·  {row.get('course_name', '')}"
                f"  ·  {row.get('program_name', '')}"
            )
            self.course_list.insert("end", text)
            if int(row["course_id"]) in self.selected_course_ids:
                self.course_list.selection_set(index)
        self._updating_course_list = False

        if not self.course_options:
            self.course_search_status.configure(text="No courses are available.")
        elif query and not self.visible_courses:
            self.course_search_status.configure(text="No courses match that search.")
        else:
            self.course_search_status.configure(
                text=f"{len(self.visible_courses):,} course(s) · {len(self.selected_course_ids):,} selected"
            )
        self._update_course_selection_label()

    def _remember_course_selection(self) -> None:
        if self._updating_course_list or not hasattr(self, "course_list"):
            return
        visible_ids = {int(row["course_id"]) for row in self.visible_courses}
        selected_visible = {
            int(self.visible_courses[index]["course_id"])
            for index in self.course_list.curselection()
            if index < len(self.visible_courses)
        }
        self.selected_course_ids.difference_update(visible_ids)
        self.selected_course_ids.update(selected_visible)

    def _course_selection_changed(self, _event: tk.Event | None = None) -> None:
        if self._updating_course_list:
            return
        self._remember_course_selection()
        self._update_course_selection_label()
        self.course_search_status.configure(
            text=f"{len(self.visible_courses):,} course(s) · {len(self.selected_course_ids):,} selected"
        )

    def _update_course_selection_label(self) -> None:
        count = len(self.selected_course_ids)
        text = "No courses selected" if count == 0 else f"{count:,} course(s) selected"
        self.course_selection_label.configure(text=text)

    def _refresh_enrollments(self) -> None:
        if self.student_id is None:
            self._load_enrollments([])
            return
        rows = enrollment_service.list_student_enrollments(self.student_id)
        self._load_enrollments(rows)

    def _load_enrollments(self, rows: list[dict[str, Any]]) -> None:
        self.enrollment_table.delete(*self.enrollment_table.get_children())
        for row in rows:
            status = str(row.get("enrollment_status") or "")
            status_tag = status.casefold() if status.casefold() in {s.casefold() for s in ENROLLMENT_STATUSES} else ""
            tags = (status_tag,) if status_tag else ()
            enrollment_id = int(row["student_course_id"])
            self.enrollment_table.insert(
                "", "end", iid=str(enrollment_id), tags=tags,
                values=(
                    row.get("course_code") or "",
                    row.get("course_name") or "",
                    row.get("course_program_name") or "",
                    row.get("academic_year") or "",
                    row.get("semester") or "",
                    row.get("grade") or "—",
                    status or "—",
                ),
            )
        count = len(rows)
        self.enrollment_count_label.configure(text=f"{count:,} record{'s' if count != 1 else ''}")
        self.grade_var.set("")
        self.status_var.set("")
        self.selected_enrollment_label.configure(text="Select an enrolment to update its grade or status.")
        self.update_button.configure(state="disabled")
        self.remove_button.configure(state="disabled")
        self._style_danger_button(self.remove_button)
        self.export_button.configure(
            state="normal" if rows and self.student_record is not None else "disabled"
        )

    def _set_feedback(self, text: str, kind: str = "muted") -> None:
        self.feedback_kind = kind
        self.feedback_label.configure(text=text)
        self._set_feedback_color()
        if text and kind in {"success", "warning", "error"} and self.on_notify is not None:
            self.on_notify(text, kind)

    def _set_feedback_color(self) -> None:
        if not hasattr(self, "feedback_label") or not self.palette:
            return
        color_key = {"success": "teal", "error": "danger", "muted": "muted"}.get(
            self.feedback_kind, "muted"
        )
        self.feedback_label.configure(foreground=self.palette[color_key])

    def _make_danger_button(
        self, parent: tk.Misc, *, text: str, command: Callable[[], None]
    ) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            padx=13,
            pady=8,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        self.danger_buttons.append(button)
        self._style_danger_button(button)
        return button

    def _style_danger_button(self, button: tk.Button) -> None:
        if not self.palette:
            return
        disabled = str(button.cget("state")) == "disabled"
        button.configure(
            bg=self.palette["surface"] if disabled else self.palette["danger"],
            fg=self.palette["muted"] if disabled else self.palette["danger_text"],
            activebackground=self.palette["surface"] if disabled else self.palette["danger"],
            activeforeground=self.palette["muted"] if disabled else self.palette["danger_text"],
            disabledforeground=self.palette["muted"],
        )

    def _selected_enrollment_id(self) -> int | None:
        selection = self.enrollment_table.selection()
        return int(selection[0]) if selection else None

    def _select_enrollment(self, _event: tk.Event | None = None) -> None:
        selected = self.enrollment_table.selection()
        if not selected:
            return
        values = self.enrollment_table.item(selected[0], "values")
        self.grade_var.set("" if values[5] == "—" else values[5])
        self.status_var.set(values[6] if values[6] != "—" else "")
        self.selected_enrollment_label.configure(text=f"Selected: {values[0]} · {values[1]}")
        self.update_button.configure(state="normal")
        self.remove_button.configure(state="normal")
        self._style_danger_button(self.remove_button)
        self._set_feedback("")

    def add_selected_courses(self) -> None:
        if self.student_id is None or self.student_record is None:
            self._set_feedback("Select a student before adding courses.", "error")
            return
        course_ids = [
            int(row["course_id"])
            for row in self.course_options
            if int(row["course_id"]) in self.selected_course_ids
        ]
        if not course_ids:
            self._set_feedback("Choose one or more courses to enrol.", "error")
            return
        try:
            created_ids = enrollment_service.enroll_courses(
                self.student_id,
                course_ids,
                self.academic_year_var.get(),
                self.semester_var.get(),
                self.new_status_var.get(),
            )
        except ValueError as error:
            self._set_feedback(str(error), "error")
            return
        except Exception:
            self._set_feedback("The course enrolment could not be saved.", "error")
            return

        self._updating_course_list = True
        self.course_list.selection_clear(0, "end")
        self._updating_course_list = False
        self.selected_course_ids.clear()
        self._filter_courses()
        try:
            self._refresh_enrollments()
        except Exception:
            self._set_feedback("Enrolments were saved, but the table could not be refreshed.", "error")
            return
        count = len(created_ids)
        self._set_feedback(f"Successfully enrolled in {count} course(s).", "success")

    def update_selected(self) -> None:
        enrollment_id = self._selected_enrollment_id()
        if enrollment_id is None:
            self._set_feedback("Select an enrolment before updating its grade or status.", "error")
            return
        try:
            updated = enrollment_service.update_enrollment(
                enrollment_id, self.grade_var.get() or None, self.status_var.get()
            )
        except ValueError as error:
            self._set_feedback(str(error), "error")
            return
        except Exception:
            self._set_feedback("The enrolment could not be updated.", "error")
            return
        if not updated:
            self._set_feedback("No enrolment was updated; it may have been removed.", "error")
            try:
                self._refresh_enrollments()
            except Exception:
                pass
            return
        try:
            self._refresh_enrollments()
        except Exception:
            self._set_feedback("The update was saved, but the table could not be refreshed.", "error")
            return
        self._set_feedback("Enrolment grade and status updated.", "success")

    def _confirm_remove(self, course_text: str) -> bool:
        dialog = tk.Toplevel(self)
        dialog.title("Remove enrolment")
        dialog.transient(self.winfo_toplevel())
        dialog.resizable(False, False)
        dialog.configure(bg=self.palette.get("background", "#F3F0FA"))
        self.confirmation_windows.append(dialog)
        answer = {"confirmed": False}

        body = ttk.Frame(dialog, style="App.TFrame", padding=22)
        body.pack(fill="both", expand=True)
        card = ttk.Frame(body, style="Card.TFrame", padding=18)
        card.pack(fill="both", expand=True)
        ttk.Label(card, text="Remove this enrolment?", style="SectionTitle.TLabel").pack(anchor="w")
        ttk.Label(
            card,
            text=f"This will remove {course_text} from the student's enrolment records.",
            style="CardLabel.TLabel",
            wraplength=380,
        ).pack(anchor="w", pady=(8, 20))
        buttons = ttk.Frame(card, style="CardInner.TFrame")
        buttons.pack(fill="x")
        ttk.Button(
            buttons, text="Cancel", style="Secondary.TButton", command=dialog.destroy
        ).pack(side="right", padx=(8, 0))

        def confirm() -> None:
            answer["confirmed"] = True
            dialog.destroy()

        danger_button = self._make_danger_button(buttons, text="Remove enrolment", command=confirm)
        danger_button.pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Destroy>", lambda event, win=dialog: self._forget_confirmation(event, win))
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.winfo_toplevel().winfo_rootx() + (self.winfo_toplevel().winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_toplevel().winfo_rooty() + (self.winfo_toplevel().winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.wait_window(dialog)
        return answer["confirmed"]

    def _forget_confirmation(self, event: tk.Event, window: tk.Toplevel) -> None:
        if str(event.widget) == str(window) and window in self.confirmation_windows:
            self.confirmation_windows.remove(window)
            for button in list(self.danger_buttons):
                try:
                    if str(button.winfo_toplevel()) == str(window):
                        self.danger_buttons.remove(button)
                except tk.TclError:
                    self.danger_buttons.remove(button)

    def remove_selected(self) -> None:
        enrollment_id = self._selected_enrollment_id()
        if enrollment_id is None:
            self._set_feedback("Select an enrolment before removing it.", "error")
            return
        values = self.enrollment_table.item(str(enrollment_id), "values")
        course_text = f"{values[0]} — {values[1]}"
        if not self._confirm_remove(course_text):
            self._set_feedback("Enrolment removal cancelled.")
            return
        try:
            removed = enrollment_service.remove_enrollment(enrollment_id)
        except Exception:
            self._set_feedback("The enrolment could not be removed.", "error")
            return
        if not removed:
            self._set_feedback("The enrolment was not found and could not be removed.", "error")
            self._refresh_enrollments()
            return
        try:
            self._refresh_enrollments()
        except Exception:
            self._set_feedback("The enrolment was removed, but the table could not be refreshed.", "error")
            return
        self._set_feedback("Enrolment removed.", "success")

    def export_student_enrollments(self) -> None:
        if self.student_id is None or self.student_record is None:
            self._set_feedback("Select a student before exporting enrolments.", "error")
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
            self._set_feedback("The student's enrolments could not be loaded for export.", "error")
            return
        if not records:
            self.export_button.configure(state="disabled")
            self._set_feedback("There are no enrolments to export.", "muted")
            return
        try:
            count = export_service.export_enrollments(records, destination)
        except Exception:
            self._set_feedback("The CSV file could not be written. Check the destination and try again.", "error")
            return
        self._set_feedback(f"Exported {count} enrolment record(s).", "success")
