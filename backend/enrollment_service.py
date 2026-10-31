"""Validation and use cases for student course enrolments."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, NoReturn

from database import enrollment_repository


EnrollmentData = dict[str, Any]
_ACADEMIC_YEAR_RE = re.compile(r"^(\d{4})-(\d{4})$")
_SEMESTERS = frozenset(("Semester 1", "Semester 2", "Summer"))
_GRADES = frozenset(("O", "A+", "A", "B+", "B", "C", "P", "F"))
_ENROLLMENT_STATUSES = frozenset(("Enrolled", "Completed", "Dropped"))


class EnrollmentServiceError(ValueError):
    """Base class for enrolment errors safe to display in the application."""


class DuplicateEnrollmentError(EnrollmentServiceError):
    """Raised when the same course is already enrolled in for the term."""


def validate_academic_year(value: str) -> str:
    """Validate a consecutive four-digit academic-year range."""
    if not isinstance(value, str):
        raise ValueError("Academic year is required in YYYY-YYYY format.")
    value = value.strip()
    match = _ACADEMIC_YEAR_RE.fullmatch(value)
    if not match:
        raise ValueError("Academic year must use YYYY-YYYY format, for example 2026-2027.")
    start_year, end_year = (int(part) for part in match.groups())
    if end_year != start_year + 1:
        raise ValueError("The ending academic year must be exactly one year after the starting year.")
    return value


def validate_semester(value: str) -> str:
    """Validate a semester against the database enum values."""
    if not isinstance(value, str):
        raise ValueError("Select a valid semester.")
    value = value.strip()
    if value not in _SEMESTERS:
        raise ValueError("Semester must be Semester 1, Semester 2, or Summer.")
    return value


def validate_grade(value: str | None) -> str | None:
    """Normalize an optional grade and enforce the approved grade set."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Grade must be text or blank.")
    value = value.strip().upper()
    if not value:
        return None
    if value not in _GRADES:
        raise ValueError("Grade must be one of O, A+, A, B+, B, C, P, or F.")
    return value


def validate_enrollment_status(value: str) -> str:
    """Validate an enrolment status against the database enum values."""
    if not isinstance(value, str):
        raise ValueError("Select a valid enrolment status.")
    value = value.strip()
    if value not in _ENROLLMENT_STATUSES:
        raise ValueError("Enrolment status must be Enrolled, Completed, or Dropped.")
    return value


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


def _term_values(academic_year: str, semester: str) -> tuple[str, str]:
    return validate_academic_year(academic_year), validate_semester(semester)


def _raise_duplicate_as_service_error(error: Exception) -> NoReturn:
    raise DuplicateEnrollmentError(
        "This student is already enrolled in one or more selected courses "
        "for that academic year and semester."
    ) from error


def enroll_course(
    student_id: int,
    course_id: int,
    academic_year: str,
    semester: str,
    enrollment_status: str = "Enrolled",
    grade: str | None = None,
) -> int:
    """Validate and create one enrolment; courses from any programme are allowed."""
    student_id = _positive_id(student_id, "Student ID")
    course_id = _positive_id(course_id, "Course ID")
    academic_year, semester = _term_values(academic_year, semester)
    status = validate_enrollment_status(enrollment_status)
    normalized_grade = validate_grade(grade)
    try:
        return enrollment_repository.enroll_student(
            student_id, course_id, academic_year, semester, status, normalized_grade
        )
    except enrollment_repository.DuplicateEnrollmentError as error:
        _raise_duplicate_as_service_error(error)


def enroll_courses(
    student_id: int,
    course_ids: Iterable[int],
    academic_year: str,
    semester: str,
    enrollment_status: str = "Enrolled",
    grade: str | None = None,
) -> list[int]:
    """Validate and atomically enrol a student in multiple courses for one term."""
    student_id = _positive_id(student_id, "Student ID")
    if isinstance(course_ids, (str, bytes)):
        raise ValueError("Select one or more course IDs.")
    selected_ids = tuple(_positive_id(course_id, "Course ID") for course_id in course_ids)
    if not selected_ids:
        raise ValueError("Select at least one course.")
    academic_year, semester = _term_values(academic_year, semester)
    status = validate_enrollment_status(enrollment_status)
    normalized_grade = validate_grade(grade)
    try:
        return enrollment_repository.enroll_student_in_courses(
            student_id,
            selected_ids,
            academic_year,
            semester,
            status,
            normalized_grade,
        )
    except enrollment_repository.DuplicateEnrollmentError as error:
        _raise_duplicate_as_service_error(error)


def list_student_enrollments(student_id: int) -> list[EnrollmentData]:
    """List all course enrolments for one student."""
    return enrollment_repository.list_enrollments_for_student(
        _positive_id(student_id, "Student ID")
    )


def list_enrollments_by_term(
    academic_year: str, semester: str
) -> list[EnrollmentData]:
    """List all enrolments for a validated academic year and semester."""
    academic_year, semester = _term_values(academic_year, semester)
    return enrollment_repository.list_enrollments_by_term(academic_year, semester)


def update_enrollment(
    student_course_id: int,
    grade: str | None,
    enrollment_status: str,
) -> bool:
    """Update both grade and status while preserving cross-programme choices."""
    return enrollment_repository.update_enrollment(
        _positive_id(student_course_id, "Enrolment ID"),
        validate_grade(grade),
        validate_enrollment_status(enrollment_status),
    )


def update_grade(
    student_course_id: int,
    grade: str | None,
    *,
    current_enrollment_status: str,
) -> bool:
    """Update a grade while retaining the known current status.

    Stage 1 exposes a combined repository update, so callers must provide the
    current status from the displayed enrolment row. The repository writes both
    fields in one statement.
    """
    return update_enrollment(student_course_id, grade, current_enrollment_status)


def update_enrollment_status(
    student_course_id: int,
    enrollment_status: str,
    *,
    current_grade: str | None,
) -> bool:
    """Update status while retaining the known current grade."""
    return update_enrollment(student_course_id, current_grade, enrollment_status)


def remove_enrollment(student_course_id: int) -> bool:
    """Explicitly remove one enrolment by its primary key."""
    return enrollment_repository.remove_enrollment(
        _positive_id(student_course_id, "Enrolment ID")
    )
