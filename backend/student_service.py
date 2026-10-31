"""Student use cases, validation, and programme-change review."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from database import enrollment_repository, student_repository


StudentInput = dict[str, Any]
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_STUDENT_STATUSES = frozenset(("Active", "Inactive", "Graduated"))
_STUDENT_FIELDS = frozenset((
    "student_number", "program_id", "first_name", "last_name", "date_of_birth",
    "gender", "email", "phone", "address", "admission_date", "status",
))


@dataclass(frozen=True, slots=True)
class ProgramChangeReview:
    """Details the frontend needs before confirming a programme change."""

    student_id: int
    current_program_id: int
    proposed_program_id: int
    incompatible_enrollments: tuple[dict[str, Any], ...]
    confirmation_required: bool


def _required_text(data: StudentInput, field: str, label: str, max_length: int) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"{label} must be {max_length} characters or fewer.")
    return value


def _parse_date(value: Any, label: str, required: bool) -> date | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ValueError(f"{label} is required.")
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value.strip()):
        raise ValueError(f"{label} must use YYYY-MM-DD format.")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid date.") from exc


def validate_student(data: StudentInput) -> StudentInput:
    """Normalize student input and reject fields from the old schema."""
    if not isinstance(data, dict):
        raise ValueError("Student data must be supplied as a mapping.")
    legacy_fields = {"roll_number", "course_id"}.intersection(data)
    if legacy_fields:
        names = ", ".join(sorted(legacy_fields))
        raise ValueError(f"Student data cannot include legacy field(s): {names}.")
    unknown_fields = set(data) - _STUDENT_FIELDS
    if unknown_fields:
        names = ", ".join(sorted(unknown_fields))
        raise ValueError(f"Unrecognized student field(s): {names}.")

    student_number = _required_text(data, "student_number", "Student number", 40)
    first_name = _required_text(data, "first_name", "First name", 80)
    last_name = _required_text(data, "last_name", "Last name", 80)
    raw_program_id = data.get("program_id")
    if isinstance(raw_program_id, bool) or not isinstance(raw_program_id, (int, str)):
        raise ValueError("Select a valid programme.")
    if isinstance(raw_program_id, str) and not raw_program_id.strip().isdecimal():
        raise ValueError("Select a valid programme.")
    try:
        program_id = int(raw_program_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("Select a valid programme.") from exc
    if isinstance(raw_program_id, bool) or program_id <= 0:
        raise ValueError("Select a valid programme.")

    admission_date = _parse_date(data.get("admission_date"), "Admission date", required=True)
    date_of_birth = _parse_date(data.get("date_of_birth"), "Date of birth", required=False)

    optional_limits = {"gender": 30, "phone": 30, "address": 500}
    optional_values: dict[str, str | None] = {}
    for field, limit in optional_limits.items():
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            optional_values[field] = None
        elif not isinstance(value, str):
            raise ValueError(f"{field.replace('_', ' ').title()} must be text.")
        else:
            value = value.strip()
            if len(value) > limit:
                raise ValueError(f"{field.replace('_', ' ').title()} must be {limit} characters or fewer.")
            optional_values[field] = value

    email_value = data.get("email")
    email = email_value.strip() if isinstance(email_value, str) else email_value
    if email == "":
        email = None
    if email is not None:
        if not isinstance(email, str) or len(email) > 254 or not _EMAIL_RE.fullmatch(email):
            raise ValueError("Enter a valid email address.")

    status_value = data.get("status", "Active")
    if not isinstance(status_value, str):
        raise ValueError("Student status must be Active, Inactive, or Graduated.")
    status = status_value.strip()
    if status not in _STUDENT_STATUSES:
        raise ValueError("Student status must be Active, Inactive, or Graduated.")

    return {
        "student_number": student_number,
        "program_id": program_id,
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "gender": optional_values["gender"],
        "email": email,
        "phone": optional_values["phone"],
        "address": optional_values["address"],
        "admission_date": admission_date,
        "status": status,
    }


def register_student(data: StudentInput) -> int:
    """Validate and register a student; return the generated student ID."""
    return student_repository.create_student(validate_student(data))


def review_program_change(student_id: int, proposed_program_id: int) -> ProgramChangeReview:
    """List existing enrolments whose courses are outside a proposed programme.

    Enrolments from other programmes are permitted by policy. The returned
    review identifies them for user confirmation but never changes them.
    """
    student_id = _positive_id(student_id, "Student ID")
    proposed_program_id = _positive_id(proposed_program_id, "Programme ID")
    student = student_repository.get_student_by_id(student_id)
    if student is None:
        raise ValueError("Student record was not found.")

    current_program_id = int(student["program_id"])
    enrolments = enrollment_repository.list_enrollments_for_student(student_id)
    incompatible = tuple(
        enrollment for enrollment in enrolments
        if int(enrollment["course_program_id"]) != proposed_program_id
    )
    return ProgramChangeReview(
        student_id=student_id,
        current_program_id=current_program_id,
        proposed_program_id=proposed_program_id,
        incompatible_enrollments=incompatible,
        confirmation_required=bool(incompatible),
    )


def update_student(
    student_id: int,
    data: StudentInput,
    *,
    confirm_program_change: bool = False,
) -> bool | ProgramChangeReview:
    """Update a student, returning a review before incompatible programme changes.

    Confirmation updates only the student's programme and profile. Existing
    enrolment rows are left intact, including courses outside the new programme.
    """
    student_id = _positive_id(student_id, "Student ID")
    clean = validate_student(data)
    current = student_repository.get_student_by_id(student_id)
    if current is None:
        return False

    proposed_program_id = clean["program_id"]
    if int(current["program_id"]) != proposed_program_id:
        review = review_program_change(student_id, proposed_program_id)
        if review.confirmation_required and not confirm_program_change:
            return review

    return student_repository.update_student(student_id, clean)


def save_student(
    data: StudentInput,
    student_id: int | None = None,
    *,
    confirm_program_change: bool = False,
) -> int | bool | ProgramChangeReview:
    """Register a student or update an existing record (legacy service entry point)."""
    if student_id is None:
        return register_student(data)
    return update_student(
        student_id,
        data,
        confirm_program_change=confirm_program_change,
    )


def _positive_id(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{label} must be a positive integer.")
    if isinstance(value, str) and not value.strip().isdecimal():
        raise ValueError(f"{label} must be a positive integer.")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a positive integer.") from exc
    if result <= 0:
        raise ValueError(f"{label} must be a positive integer.")
    return result


def get_student(student_id: int) -> StudentInput | None:
    """Retrieve one student by primary key."""
    return student_repository.get_student_by_id(_positive_id(student_id, "Student ID"))


def list_students() -> list[StudentInput]:
    """List all students with programme and department details."""
    return student_repository.list_students()


def search_students(query: str) -> list[StudentInput]:
    """Search by numeric student ID, exact student number, or name."""
    query = query.strip()
    if not query:
        return list_students()
    if query.isdecimal():
        student = get_student(int(query))
        if student is not None:
            return [student]
        return student_repository.search_students_by_number(query)
    return student_repository.search_students_by_name(query)


def search_students_by_number(student_number: str) -> list[StudentInput]:
    """Search by exact student number."""
    if not student_number.strip():
        return []
    return student_repository.search_students_by_number(student_number)


def remove_student(student_id: int) -> bool:
    """Delete a student only when the repository confirms no enrolments exist."""
    return student_repository.delete_student(_positive_id(student_id, "Student ID"))


def dashboard_statistics() -> dict[str, int]:
    """Return student, course, and department counts for the dashboard."""
    return student_repository.get_dashboard_statistics()
