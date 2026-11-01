"""Student directory with local filtering and existing service operations."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from backend import export_service, student_service
from frontend.widgets.design_system import bind_hover_tree


STATUSES = ("Active", "Inactive", "Graduated")
ALL_STATUSES = "All statuses"


class StudentsView(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_navigate: Callable[[str], None],
        on_edit: Callable[[int], None],
        on_manage_enrollments: Callable[[int], None],
        on_notify: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__(master, style="App.TFrame")
        self.on_navigate = on_navigate
        self.on_edit = on_edit
        self.on_manage_enrollments = on_manage_enrollments
        self.on_notify = on_notify
        self.records: list[dict[str, Any]] = []
        self.records_by_id: dict[int, dict[str, Any]] = {}
        self.filtered_records: list[dict[str, Any]] = []
        self.detail_windows: list[tk.Toplevel] = []
        self.confirmation_windows: list[tk.Toplevel] = []
        self.palette: dict[str, str] = {}
        self.load_failed = False

        heading = ttk.Frame(self, style="App.TFrame")
        heading.pack(fill="x", pady=(0, 20))
        title_box = ttk.Frame(heading, style="App.TFrame")
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(title_box, text="Students", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            title_box,
            text="Search, review, and manage student records.",
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
            text="＋  Add Student",
            style="Primary.TButton",
            command=lambda: self.on_navigate("registration"),
        ).pack(side="left")

        self.summary_labels: dict[str, ttk.Label] = {}
        self.summary_components: dict[str, dict[str, ttk.Widget]] = {}
        summary_row = ttk.Frame(self, style="App.TFrame")
        summary_row.pack(fill="x", pady=(0, 16))
        summaries = (
            ("total", "Total students", "ALL", "Violet"),
            ("active", "Active", "ON", "Teal"),
            ("inactive", "Inactive", "OFF", "Amber"),
            ("graduated", "Graduated", "ALUM", "Indigo"),
        )
        for index, (key, title, icon, accent) in enumerate(summaries):
            card = ttk.Frame(summary_row, style=f"Metric{accent}.TFrame", padding=(16, 12))
            card.pack(side="left", fill="both", expand=True, padx=(0, 10 if index < 3 else 0))
            accent_bar = ttk.Frame(card, style=f"Metric{accent}Accent.TFrame", height=3)
            accent_bar.pack(fill="x", pady=(0, 10))
            accent_bar.pack_propagate(False)
            top = ttk.Frame(card, style=f"Metric{accent}Inner.TFrame")
            top.pack(fill="x")
            title_label = ttk.Label(top, text=title, style=f"Metric{accent}Label.TLabel")
            title_label.pack(side="left")
            icon_label = ttk.Label(top, text=icon, style=f"Metric{accent}Icon.TLabel")
            icon_label.pack(side="right")
            value = ttk.Label(card, text="—", style=f"Metric{accent}Value.TLabel")
            value.configure(font=("Segoe UI", 23, "bold"))
            value.pack(anchor="w", pady=(7, 0))
            self.summary_labels[key] = value
            self.summary_components[key] = {
                "card": card, "accent_bar": accent_bar, "top": top,
                "title": title_label, "icon": icon_label, "value": value,
            }
            bind_hover_tree(
                card,
                lambda hovered, item=key, color=accent: self._set_summary_hover(
                    item, color, hovered
                ),
            )

        toolbar = ttk.Frame(self, style="Card.TFrame", padding=12)
        toolbar.pack(fill="x", pady=(0, 14))
        filter_row = ttk.Frame(toolbar, style="CardInner.TFrame")
        filter_row.pack(fill="x")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_row, textvariable=self.search_var, width=35)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.insert(0, "Search name, student number, or email")
        self.search_entry.configure(foreground="#777187")
        self.search_entry.bind("<FocusIn>", self._clear_search_hint)
        self.search_entry.bind("<FocusOut>", self._restore_search_hint)
        self.search_var.trace_add("write", lambda *_args: self.apply_filters())

        ttk.Label(filter_row, text="Status", style="CardLabel.TLabel").pack(side="left", padx=(4, 7))
        self.status_filter_var = tk.StringVar(value=ALL_STATUSES)
        self.status_filter = ttk.Combobox(
            filter_row, textvariable=self.status_filter_var, state="readonly",
            values=(ALL_STATUSES, *STATUSES), width=15,
        )
        self.status_filter.pack(side="left", padx=(0, 8))
        self.status_filter.bind("<<ComboboxSelected>>", lambda _event: self.apply_filters())
        ttk.Button(filter_row, text="Reset filters", style="Secondary.TButton",
                   command=self.clear_search).pack(side="left", padx=(8, 0))

        record_actions = ttk.Frame(toolbar, style="CardInner.TFrame")
        record_actions.pack(fill="x", pady=(10, 0))
        ttk.Button(record_actions, text="Delete", style="Secondary.TButton",
                   command=self.delete_selected).pack(side="right")
        ttk.Button(record_actions, text="Edit", style="Secondary.TButton",
                   command=self.edit_selected).pack(side="right", padx=(0, 8))
        ttk.Button(record_actions, text="View", style="Secondary.TButton",
                   command=self.view_selected).pack(side="right", padx=(0, 8))
        ttk.Button(record_actions, text="Manage Courses", style="Secondary.TButton",
                   command=self.manage_selected).pack(side="right", padx=(0, 8))

        self.results_area = ttk.Frame(self, style="App.TFrame")
        self.results_area.pack(fill="both", expand=True)
        self.table_panel = ttk.Frame(self.results_area, style="Card.TFrame", padding=10)
        self.table_panel.pack(fill="both", expand=True)
        columns = (
            "student_number", "name", "email", "department", "program",
            "admission_date", "status",
        )
        self.table = ttk.Treeview(self.table_panel, columns=columns, show="headings", selectmode="browse")
        labels = {
            "student_number": ("Student number", 130),
            "name": ("Student name", 175),
            "email": ("Email", 200),
            "department": ("Department", 170),
            "program": ("Programme", 225),
            "admission_date": ("Admission date", 125),
            "status": ("Status", 110),
        }
        for column, (label, width) in labels.items():
            self.table.heading(column, text=label)
            anchor = "center" if column in {"student_number", "admission_date", "status"} else "w"
            self.table.column(column, width=width, minwidth=85, anchor=anchor, stretch=True)
        y_scroll = ttk.Scrollbar(self.table_panel, orient="vertical", command=self.table.yview)
        x_scroll = ttk.Scrollbar(self.table_panel, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.table_panel.rowconfigure(0, weight=1)
        self.table_panel.columnconfigure(0, weight=1)
        # Keep the existing double-click-to-edit behavior. The separate View
        # button below is strictly read-only.
        self.table.bind("<Double-1>", lambda _event: self.edit_selected())

        self.empty_panel = ttk.Frame(self.results_area, style="Card.TFrame", padding=(28, 42))
        empty_content = ttk.Frame(self.empty_panel, style="CardInner.TFrame")
        empty_content.pack(expand=True)
        self.empty_title = ttk.Label(empty_content, text="", style="SectionTitle.TLabel")
        self.empty_title.pack(pady=(0, 7))
        self.empty_message = ttk.Label(empty_content, text="", style="CardLabel.TLabel")
        self.empty_message.pack(pady=(0, 16))
        self.empty_action = ttk.Button(empty_content, text="", style="Primary.TButton")
        self.empty_action.pack()
        self.empty_panel.pack_forget()

        footer = ttk.Frame(self, style="App.TFrame")
        footer.pack(fill="x", pady=(9, 0))
        self.status = ttk.Label(footer, text="", style="Subtitle.TLabel")
        self.status.pack(side="left")

    def apply_theme(self, palette: dict[str, str]) -> None:
        """Update status tags and any currently open read-only detail windows."""
        self.palette = palette
        if hasattr(self, "table"):
            self._configure_status_tags()
        if hasattr(self, "search_entry"):
            is_hint = self.search_var.get() == "Search name, student number, or email"
            self.search_entry.configure(foreground=palette["muted"] if is_hint else palette["text"])
        for window in [*self.detail_windows, *self.confirmation_windows]:
            try:
                if window.winfo_exists():
                    window.configure(bg=palette["background"])
            except tk.TclError:
                self.detail_windows.remove(window)

    def _set_summary_hover(self, key: str, accent: str, hovered: bool) -> None:
        """Apply card hover styles while keeping all summary values in place."""
        components = self.summary_components.get(key)
        if not components:
            return
        state = "Hover" if hovered else ""
        components["card"].configure(style=f"Metric{accent}{state}.TFrame")
        components["accent_bar"].configure(style=f"Metric{accent}Accent{state}.TFrame")
        components["top"].configure(style=f"Metric{accent}{state}Inner.TFrame")
        components["title"].configure(style=f"Metric{accent}{state}Label.TLabel")
        components["icon"].configure(style=f"Metric{accent}{state}Icon.TLabel")
        components["value"].configure(style=f"Metric{accent}{state}Value.TLabel")
        components["value"].configure(font=("Segoe UI", 23, "bold"))

    def _configure_status_tags(self) -> None:
        palette = self.palette
        self.table.tag_configure(
            "status_active", background=palette["status_active_bg"], foreground=palette["status_active_fg"]
        )
        self.table.tag_configure(
            "status_inactive", background=palette["status_inactive_bg"], foreground=palette["status_inactive_fg"]
        )
        self.table.tag_configure(
            "status_graduated", background=palette["status_graduated_bg"], foreground=palette["status_graduated_fg"]
        )

    def refresh(self) -> None:
        """Reload the full dataset, then update summary cards and visible rows."""
        try:
            self.records = list(student_service.list_students())
            self.records_by_id = {int(row["student_id"]): row for row in self.records}
            self.load_failed = False
            self._update_summary_cards()
            self.apply_filters()
        except Exception:
            self.load_failed = True
            self.table_panel.pack_forget()
            for label in self.summary_labels.values():
                label.configure(text="—")
            self._show_empty_state(
                "Student records unavailable",
                "Could not load student records. Check the database settings and server.",
                "Retry",
                self.refresh,
            )
            self.status.configure(text="Student data could not be loaded.")

    def _update_summary_cards(self) -> None:
        """Count all students, independent of the active search and status filters."""
        counts = {status.casefold(): 0 for status in STATUSES}
        for record in self.records:
            status = str(record.get("status") or "").casefold()
            if status in counts:
                counts[status] += 1
        self.summary_labels["total"].configure(text=f"{len(self.records):,}")
        for status in STATUSES:
            self.summary_labels[status.casefold()].configure(text=f"{counts[status.casefold()]:,}")

    def _clear_search_hint(self, _event: tk.Event | None = None) -> None:
        if self.search_var.get() == "Search name, student number, or email":
            self.search_var.set("")
            self.search_entry.configure(foreground=self.palette.get("text", "#252137"))

    def _restore_search_hint(self, _event: tk.Event | None = None) -> None:
        if not self.search_var.get().strip():
            self.search_var.set("Search name, student number, or email")
            self.search_entry.configure(foreground=self.palette.get("muted", "#777187"))

    def _search_text(self) -> str:
        query = self.search_var.get().strip()
        if query == "Search name, student number, or email":
            return ""
        return query.casefold()

    def apply_filters(self) -> None:
        if not hasattr(self, "table") or self.load_failed:
            return
        query = self._search_text()
        selected_status = self.status_filter_var.get()
        selected_status = "" if selected_status == ALL_STATUSES else selected_status.casefold()
        filtered = []
        for record in self.records:
            full_name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
            searchable = " ".join((
                str(record.get("student_number") or ""),
                str(record.get("first_name") or ""),
                str(record.get("last_name") or ""),
                full_name,
                str(record.get("email") or ""),
            )).casefold()
            if query and query not in searchable:
                continue
            if selected_status and str(record.get("status") or "").casefold() != selected_status:
                continue
            filtered.append(record)
        self.filtered_records = filtered
        self._render_records()

    def _render_records(self) -> None:
        self.table.delete(*self.table.get_children())
        for row in self.filtered_records:
            status = str(row.get("status") or "")
            status_key = status.casefold()
            tags = (f"status_{status_key}",) if status_key in {s.casefold() for s in STATUSES} else ()
            self.table.insert(
                "", "end", iid=str(row.get("student_id")), tags=tags,
                values=(
                    row.get("student_number") or "",
                    f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                    row.get("email") or "",
                    row.get("department_name") or "",
                    row.get("program_name") or "",
                    self._format_admission_date(row.get("admission_date")),
                    f"●  {status}" if status else "—",
                ),
            )
        count = len(self.filtered_records)
        self.status.configure(text=f"Showing {count:,} of {len(self.records):,} student(s)")
        if count:
            self.empty_panel.pack_forget()
            self.table_panel.pack(fill="both", expand=True)
        else:
            self.table_panel.pack_forget()
            if not self.records:
                self._show_empty_state(
                    "No students yet",
                    "Register a student to start building your student directory.",
                    "Add Student",
                    lambda: self.on_navigate("registration"),
                )
            else:
                self._show_empty_state(
                    "No matching students",
                    "Try another search term or status filter.",
                    "Reset filters",
                    self.clear_search,
                )

    def _show_empty_state(
        self, title: str, message: str, action_text: str, command: Callable[[], None]
    ) -> None:
        self.empty_title.configure(text=title)
        self.empty_message.configure(text=message)
        self.empty_action.configure(text=action_text, command=command)
        self.empty_panel.pack(fill="both", expand=True)

    def clear_search(self) -> None:
        self.search_var.set("")
        self.status_filter_var.set(ALL_STATUSES)
        self.apply_filters()

    @staticmethod
    def _format_admission_date(value: Any) -> str:
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
            return date.fromisoformat(text).strftime("%d-%m-%Y")
        except ValueError:
            return text

    def _selected_record(self) -> dict[str, Any] | None:
        selected = self.table.selection()
        if not selected:
            self._notify("Choose a student record first.", "warning")
            return None
        return self.records_by_id.get(int(selected[0]))

    def _notify(self, message: str, kind: str) -> None:
        if self.on_notify is not None:
            self.on_notify(message, kind)

    def _center_window(self, window: tk.Toplevel) -> None:
        window.update_idletasks()
        parent = self.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() - window.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window.winfo_height()) // 2
        window.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def view_selected(self) -> None:
        """Open the selected student's details in a read-only window."""
        record = self._selected_record()
        if record is None:
            return
        window = tk.Toplevel(self)
        window.title("Student details")
        window.transient(self.winfo_toplevel())
        window.configure(bg=self.palette["background"])
        window.minsize(460, 420)
        window.geometry("560x580")
        window.resizable(True, True)
        window.bind("<Escape>", lambda _event: window.destroy())
        window.bind("<Destroy>", lambda event, w=window: self._forget_detail_window(event, w))
        self.detail_windows.append(window)

        content = ttk.Frame(window, style="App.TFrame", padding=24)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text="Student details", style="PageTitle.TLabel").pack(anchor="w")
        full_name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
        ttk.Label(content, text=full_name, style="Subtitle.TLabel").pack(anchor="w", pady=(4, 18))
        details = ttk.Frame(content, style="Card.TFrame", padding=18)
        details.pack(fill="both", expand=True)
        fields = (
            ("Student number", record.get("student_number")),
            ("Email", record.get("email")),
            ("Phone", record.get("phone")),
            ("Department", record.get("department_name")),
            ("Programme", record.get("program_name")),
            ("Date of birth", self._format_admission_date(record.get("date_of_birth"))),
            ("Admission date", self._format_admission_date(record.get("admission_date"))),
            ("Status", record.get("status")),
            ("Address", record.get("address")),
        )
        for index, (label, value) in enumerate(fields):
            ttk.Label(details, text=label, style="DetailLabel.TLabel").grid(
                row=index, column=0, sticky="nw", padx=(0, 16), pady=5
            )
            ttk.Label(
                details, text=str(value or "—"), style="DetailValue.TLabel", wraplength=320
            ).grid(row=index, column=1, sticky="nw", pady=5)
        details.columnconfigure(1, weight=1)
        ttk.Button(content, text="Close", style="Secondary.TButton",
                   command=window.destroy).pack(anchor="e", pady=(14, 0))
        self._center_window(window)

    def _forget_detail_window(self, event: tk.Event, window: tk.Toplevel) -> None:
        if str(event.widget) == str(window) and window in self.detail_windows:
            self.detail_windows.remove(window)

    def edit_selected(self) -> None:
        record = self._selected_record()
        if record is not None:
            self.on_edit(int(record["student_id"]))

    def manage_selected(self) -> None:
        record = self._selected_record()
        if record is not None:
            self.on_manage_enrollments(int(record["student_id"]))

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
            self._notify("Student records could not be loaded for export.", "error")
            return
        if not records:
            self._notify("There are no student records to export.", "warning")
            return
        try:
            count = export_service.export_students(records, destination)
        except Exception:
            self._notify("The CSV file could not be written. Check the destination and try again.", "error")
            return
        self._notify(f"Exported {count} student record(s).", "success")

    def _confirm_delete_student(self, record: dict[str, Any]) -> bool:
        window = tk.Toplevel(self)
        window.title("Delete student")
        window.transient(self.winfo_toplevel())
        window.configure(bg=self.palette["background"])
        window.resizable(False, False)
        self.confirmation_windows.append(window)
        answer = {"confirmed": False}

        content = ttk.Frame(window, style="App.TFrame", padding=22)
        content.pack(fill="both", expand=True)
        card = ttk.Frame(content, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)
        ttk.Label(card, text="Delete this student?", style="SectionTitle.TLabel").pack(anchor="w")
        name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip()
        number = str(record.get("student_number") or "")
        ttk.Label(
            card,
            text=f"{name}  ·  {number}\nThis action cannot be undone.",
            style="CardLabel.TLabel",
            wraplength=390,
            justify="left",
        ).pack(anchor="w", pady=(9, 20))
        actions = ttk.Frame(card, style="CardInner.TFrame")
        actions.pack(fill="x")

        def confirm() -> None:
            answer["confirmed"] = True
            window.destroy()

        cancel_button = ttk.Button(actions, text="Cancel", style="Secondary.TButton", command=window.destroy)
        cancel_button.pack(side="right", padx=(8, 0))
        ttk.Button(actions, text="Delete student", style="Danger.TButton", command=confirm).pack(side="right")
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.bind("<Escape>", lambda _event: window.destroy())
        window.bind("<Destroy>", lambda event, popup=window: self._forget_confirmation(event, popup))
        window.grab_set()
        self._center_window(window)
        cancel_button.focus_set()
        self.wait_window(window)
        return answer["confirmed"]

    def _forget_confirmation(self, event: tk.Event, window: tk.Toplevel) -> None:
        if str(event.widget) == str(window) and window in self.confirmation_windows:
            self.confirmation_windows.remove(window)

    def delete_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        student_id = int(record["student_id"])
        if not self._confirm_delete_student(record):
            return
        try:
            deleted = student_service.remove_student(student_id)
        except ValueError:
            self._notify(
                "This student has academic enrolments and cannot be deleted. Manage the enrolments explicitly first.",
                "warning",
            )
            return
        except Exception:
            self._notify("The student record could not be deleted.", "error")
            return
        if not deleted:
            self._notify("The student record no longer exists.", "warning")
            self.refresh()
            return
        self.refresh()
        self._notify("Student deleted successfully.", "success")
