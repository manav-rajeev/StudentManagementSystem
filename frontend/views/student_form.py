"""Student registration and update form for the programme-based schema."""

from __future__ import annotations

import tkinter as tk
import re
from tkinter import messagebox, ttk
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from backend import lookup_service, student_service
from frontend.widgets.design_system import ScrollableFrame


class StudentFormView(ttk.Frame):
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
        self.pending_student_id: int | None = None
        self.departments: list[dict[str, Any]] = []
        self.programmes: list[dict[str, Any]] = []
        self.department_ids: dict[str, int] = {}
        self.programme_ids: dict[str, int] = {}
        self.palette: dict[str, str] = {}
        self.status_is_error = False
        self.variables = {
            key: tk.StringVar()
            for key in (
                "student_number", "first_name", "last_name", "date_of_birth",
                "gender", "email", "phone", "department", "programme",
                "admission_date", "status",
            )
        }

        self.page_title = ttk.Label(self, text="Add student", style="PageTitle.TLabel")
        self.page_title.pack(anchor="w")
        ttk.Label(
            self,
            text="Enter the student's details and select their department and programme.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 18))

        self.form_viewport = ScrollableFrame(self)
        self.form_viewport.pack(fill="both", expand=True)
        panel = ttk.Frame(self.form_viewport.content, style="Card.TFrame", padding=(22, 16))
        panel.pack(fill="both", expand=True)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)
        self._section(panel, "Personal details", 0)
        self._entry(panel, "First name *", "first_name", 1, 0)
        self._entry(panel, "Last name *", "last_name", 1, 1)
        self._entry(panel, "Date of birth (DD-MM-YYYY)", "date_of_birth", 2, 0)
        self._combo(
            panel, "Gender", "gender", 2, 1,
            values=("", "Female", "Male", "Non-binary", "Prefer not to say"),
        )
        self._section(panel, "Contact details", 6)
        self._entry(panel, "Email", "email", 4, 0)
        self._entry(panel, "Phone", "phone", 4, 1)
        self._label(panel, "Address", 5, 0)
        self.address_text = tk.Text(
            panel, height=2, wrap="word", font=("Segoe UI", 10),
            relief="solid", bd=1, highlightthickness=1,
        )
        self.address_text.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(4, 5))
        self._section(panel, "Academic details", 12)
        self._entry(panel, "Student number *", "student_number", 7, 0)
        self._combo(panel, "Department *", "department", 7, 1, self._department_changed)
        self._combo(panel, "Programme *", "programme", 8, 0)
        self._entry(panel, "Admission date * (DD-MM-YYYY)", "admission_date", 8, 1)
        self._combo(
            panel, "Student status", "status", 9, 0,
            values=("Active", "Inactive", "Graduated"),
        )

        self.status_message = ttk.Label(
            panel, text="", style="FormStatus.TLabel"
        )
        self.status_message.grid(row=20, column=0, columnspan=2, sticky="w", pady=(8, 0))
        actions = ttk.Frame(panel, style="CardInner.TFrame")
        actions.grid(row=21, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.save_button = ttk.Button(actions, text="Add student", style="Primary.TButton", command=self.save)
        self.save_button.pack(side="left")
        ttk.Button(actions, text="Cancel", style="Secondary.TButton",
                   command=lambda: self.on_navigate("students")).pack(side="left", padx=(9, 0))

    def apply_theme(self, palette: dict[str, str]) -> None:
        """Apply the app's active palette to native text and status widgets."""
        self.palette = palette
        if hasattr(self, "form_viewport"):
            self.form_viewport.apply_theme(palette)
        if hasattr(self, "address_text"):
            self.address_text.configure(
                bg=palette["surface"], fg=palette["body_text"],
                insertbackground=palette["text"], selectbackground=palette["sidebar_active"],
                selectforeground=palette["sidebar_text"],
                highlightbackground=palette["border"], highlightcolor=palette["primary"],
            )
        if hasattr(self, "status_message"):
            self.status_message.configure(
                foreground=palette["danger"] if self.status_is_error else palette["muted"]
            )

    def _section(self, parent: ttk.Frame, title: str, row: int) -> None:
        ttk.Label(parent, text=title, style="SectionTitle.TLabel").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(12, 3)
        )
        ttk.Separator(parent).grid(row=row + 1, column=0, columnspan=2, sticky="ew", pady=(0, 3))

    def _set_status(self, text: str, *, error: bool = False) -> None:
        self.status_is_error = error
        color = self.palette.get("danger", "#B83F4B") if error else self.palette.get("muted", "#777187")
        self.status_message.configure(text=text, foreground=color)

    def _notify(self, message: str, kind: str) -> None:
        if self.on_notify is not None:
            self.on_notify(message, kind)

    def _label(self, parent: ttk.Frame, text: str, row: int, column: int) -> None:
        ttk.Label(parent, text=text, style="CardLabel.TLabel").grid(
            row=row * 2, column=column, sticky="w",
            padx=(0, 10) if column == 0 else (10, 0), pady=(6, 0),
        )

    def _entry(self, parent: ttk.Frame, label: str, key: str, row: int, column: int) -> None:
        self._label(parent, label, row, column)
        ttk.Entry(parent, textvariable=self.variables[key]).grid(
            row=row * 2 + 1, column=column, sticky="ew",
            padx=(0, 10) if column == 0 else (10, 0), pady=(3, 5),
        )

    def _combo(
        self,
        parent: ttk.Frame,
        label: str,
        key: str,
        row: int,
        column: int,
        callback: Callable[..., None] | None = None,
        values: tuple[str, ...] = (),
    ) -> None:
        self._label(parent, label, row, column)
        widget = ttk.Combobox(
            parent, textvariable=self.variables[key], state="readonly", values=values
        )
        widget.grid(
            row=row * 2 + 1, column=column, sticky="ew",
            padx=(0, 10) if column == 0 else (10, 0), pady=(3, 5),
        )
        if callback:
            widget.bind("<<ComboboxSelected>>", callback)
        setattr(self, f"{key}_combo", widget)

    def load_student(self, student_id: int) -> None:
        self.pending_student_id = student_id

    def refresh(self) -> None:
        try:
            self.departments = lookup_service.list_departments()
            self.department_ids = {
                self._department_label(row): int(row["department_id"])
                for row in self.departments
            }
            self.department_combo.configure(values=tuple(self.department_ids))
            if self.pending_student_id is None:
                self._reset()
                return
            record = student_service.get_student(self.pending_student_id)
            if record is None:
                raise ValueError("That student record no longer exists.")
            self._populate(record)
            self.pending_student_id = None
        except ValueError as error:
            self._set_status(str(error), error=True)
        except Exception:
            self._set_status(
                "Could not load student form data. Check the database settings and server.", error=True
            )

    @staticmethod
    def _department_label(row: dict[str, Any]) -> str:
        return f"{row['department_code']} — {row['department_name']}"

    @staticmethod
    def _programme_label(row: dict[str, Any]) -> str:
        return f"{row['program_code']} — {row['program_name']} ({row['degree_level']})"

    def _department_changed(self, _event: tk.Event | None = None) -> None:
        department_id = self.department_ids.get(self.variables["department"].get())
        if department_id is None:
            self.programme_ids.clear()
            self.programme_combo.configure(values=())
            self.variables["programme"].set("")
            return
        self._load_programmes(department_id)

    def _load_programmes(self, department_id: int, selected_program_id: int | None = None) -> None:
        try:
            self.programmes = lookup_service.list_programmes_by_department(department_id)
            self.programme_ids = {
                self._programme_label(row): int(row["program_id"])
                for row in self.programmes
            }
            self.programme_combo.configure(values=tuple(self.programme_ids))
            self.variables["programme"].set("")
            if selected_program_id is not None:
                for label, program_id in self.programme_ids.items():
                    if program_id == int(selected_program_id):
                        self.variables["programme"].set(label)
                        break
        except Exception:
            self.programme_ids.clear()
            self.programme_combo.configure(values=())
            self._set_status("Could not load programmes for this department.", error=True)

    def _populate(self, record: dict[str, Any]) -> None:
        self.student_id = int(record["student_id"])
        self.page_title.configure(text="Edit student")
        self.save_button.configure(text="Save changes")
        self._set_status(f"Editing student ID {self.student_id}.")
        for key in ("student_number", "first_name", "last_name", "gender", "email", "phone", "status"):
            self.variables[key].set(record.get(key) or "")
        self.variables["date_of_birth"].set(self._date_text(record.get("date_of_birth")))
        self.variables["admission_date"].set(self._date_text(record.get("admission_date")))

        for label, department_id in self.department_ids.items():
            if department_id == int(record["department_id"]):
                self.variables["department"].set(label)
                self._load_programmes(department_id, int(record["program_id"]))
                break

        self.address_text.delete("1.0", "end")
        self.address_text.insert("1.0", record.get("address") or "")

    @staticmethod
    def _date_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (date, datetime)):
            return value.strftime("%d-%m-%Y")
        text = str(value).strip()
        try:
            return date.fromisoformat(text).strftime("%d-%m-%Y")
        except ValueError:
            return text

    @staticmethod
    def _date_for_backend(value: str, label: str, *, required: bool) -> str | None:
        text = value.strip() if isinstance(value, str) else ""
        if not text:
            if required:
                raise ValueError(f"{label} is required.")
            return None
        if not re.fullmatch(r"\d{2}-\d{2}-\d{4}", text):
            raise ValueError(
                f"{label} must use DD-MM-YYYY format (for example, 15-03-2007)."
            )
        try:
            return datetime.strptime(text, "%d-%m-%Y").date().isoformat()
        except ValueError as error:
            raise ValueError(f"{label} must be a real calendar date.") from error

    def _reset(self) -> None:
        self.student_id = None
        self.page_title.configure(text="Add student")
        self.save_button.configure(text="Add student")
        for variable in self.variables.values():
            variable.set("")
        self.variables["status"].set("Active")
        self.address_text.delete("1.0", "end")
        self.programme_ids.clear()
        self.programme_combo.configure(values=())
        self._set_status("Required fields are marked with *.")

    def _form_data(self) -> dict[str, Any]:
        program_id = self.programme_ids.get(self.variables["programme"].get())
        return {
            "student_number": self.variables["student_number"].get(),
            "program_id": program_id,
            "first_name": self.variables["first_name"].get(),
            "last_name": self.variables["last_name"].get(),
            "date_of_birth": self._date_for_backend(
                self.variables["date_of_birth"].get(), "Date of birth", required=False
            ),
            "gender": self.variables["gender"].get(),
            "email": self.variables["email"].get(),
            "phone": self.variables["phone"].get(),
            "address": self.address_text.get("1.0", "end-1c"),
            "admission_date": self._date_for_backend(
                self.variables["admission_date"].get(), "Admission date", required=True
            ),
            "status": self.variables["status"].get() or "Active",
        }

    def save(self) -> None:
        try:
            data = self._form_data()
            result = student_service.save_student(data, self.student_id)
            if isinstance(result, student_service.ProgramChangeReview):
                if not self._confirm_program_change(result):
                    return
                result = student_service.save_student(
                    data, self.student_id, confirm_program_change=True
                )
            if self.student_id is not None and result is False:
                message = "The student record no longer exists."
                self._set_status(message, error=True)
                self._notify(message, "warning")
                return
        except ValueError as error:
            self._set_status(str(error), error=True)
            self._notify(str(error), "error")
            return
        except Exception:
            message = (
                "The student record could not be saved. Check for a duplicate student number or email "
                "and verify the database connection."
            )
            self._set_status(message, error=True)
            self._notify(message, "error")
            return

        operation = "updated" if self.student_id is not None else "registered"
        self._notify(f"Student {operation} successfully.", "success")
        self.pending_student_id = None
        self.on_navigate("students")

    def _confirm_program_change(self, review: student_service.ProgramChangeReview) -> bool:
        details = []
        for row in review.incompatible_enrollments:
            details.append(
                f"• {row.get('course_code', '')} {row.get('course_name', '')} — "
                f"{row.get('course_program_name', '')} — "
                f"{row.get('academic_year', '')}, {row.get('semester', '')}"
            )
        detail_text = "\n".join(details[:8])
        if len(details) > 8:
            detail_text += f"\n…and {len(details) - 8} more enrolment(s)"
        message = (
            "This student has course enrolments outside the proposed programme.\n\n"
            f"{detail_text}\n\n"
            "Changing the programme will preserve every enrolment record. Continue?"
        )
        return messagebox.askyesno("Review programme change", message, parent=self)
