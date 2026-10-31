"""Export student and course-enrolment records to spreadsheet-friendly CSV."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable


STUDENT_EXPORT_FIELDS = (
    ("student_number", "Student Number"),
    ("first_name", "First Name"),
    ("last_name", "Last Name"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("department_name", "Department"),
    ("program_name", "Programme"),
    ("admission_date", "Admission Date"),
    ("status", "Status"),
)

ENROLLMENT_EXPORT_FIELDS = (
    ("student_number", "Student Number"),
    ("student_name", "Student Name"),
    ("course_code", "Course Code"),
    ("course_name", "Course Name"),
    ("course_program", "Course Programme"),
    ("academic_year", "Academic Year"),
    ("semester", "Semester"),
    ("grade", "Grade"),
    ("enrollment_status", "Enrollment Status"),
    ("enrolled_at", "Enrolled At"),
)


def _write_csv(
    records: Iterable[dict[str, Any]],
    destination: str | Path,
    fields: tuple[tuple[str, str], ...],
    *,
    enrollment_rows: bool = False,
) -> int:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([label for _, label in fields])
        for record in records:
            row: list[Any] = []
            for key, _label in fields:
                if enrollment_rows and key == "student_name":
                    value = record.get("student_name")
                    if not value:
                        value = " ".join(
                            part for part in (
                                str(record.get("first_name") or "").strip(),
                                str(record.get("last_name") or "").strip(),
                            ) if part
                        )
                elif enrollment_rows and key == "course_program":
                    value = record.get("course_program") or record.get("course_program_name")
                else:
                    value = record.get(key)
                row.append("" if value is None else value)
            writer.writerow(row)
            count += 1
    return count


def export_students(records: Iterable[dict[str, Any]], destination: str | Path) -> int:
    """Write one student per row with programme and department details."""
    return _write_csv(records, destination, STUDENT_EXPORT_FIELDS)


def export_enrollments(records: Iterable[dict[str, Any]], destination: str | Path) -> int:
    """Write one row per student-course-term enrolment.

    Each row retains the owning course programme from the supplied repository
    or service result. No programme-match filter is applied, so cross-programme
    enrolments export normally.
    """
    return _write_csv(
        records,
        destination,
        ENROLLMENT_EXPORT_FIELDS,
        enrollment_rows=True,
    )
