"""Parameterized persistence operations for student records."""

from __future__ import annotations

from typing import Any

from database.connection import create_connection


StudentData = dict[str, Any]

_STUDENT_SELECT = """
    SELECT s.student_id, s.student_number, s.program_id,
           s.first_name, s.last_name, s.date_of_birth, s.gender,
           s.email, s.phone, s.address, s.admission_date, s.status,
           s.created_at, s.updated_at,
           p.program_code, p.program_name, p.degree_level,
           d.department_id, d.department_code, d.department_name
      FROM students AS s
      JOIN programs AS p ON p.program_id = s.program_id
      JOIN departments AS d ON d.department_id = p.department_id
"""

_STUDENT_WRITE_FIELDS = (
    "student_number", "program_id", "first_name", "last_name", "date_of_birth",
    "gender", "email", "phone", "address", "admission_date", "status",
)


class StudentHasEnrollmentsError(ValueError):
    """Raised when a student with course enrolments is being deleted."""


def _student_values(student: StudentData) -> tuple[Any, ...]:
    """Build values in the schema's student column order with nullable defaults."""
    return (
        student["student_number"],
        student["program_id"],
        student["first_name"],
        student["last_name"],
        student.get("date_of_birth"),
        student.get("gender"),
        student.get("email"),
        student.get("phone"),
        student.get("address"),
        student["admission_date"],
        student.get("status", "Active"),
    )


def list_students() -> list[StudentData]:
    """Return students with their programme and department details."""
    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(_STUDENT_SELECT + " ORDER BY s.student_id DESC")
            return list(cursor.fetchall())
        finally:
            cursor.close()


def get_student_by_id(student_id: int) -> StudentData | None:
    """Return one student by primary key with programme/department details."""
    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(_STUDENT_SELECT + " WHERE s.student_id = %s", (student_id,))
            return cursor.fetchone()
        finally:
            cursor.close()


def search_students_by_name(name: str) -> list[StudentData]:
    """Find students by first name, last name, or full name."""
    pattern = f"%{name.strip()}%"
    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                _STUDENT_SELECT
                + " WHERE s.first_name LIKE %s OR s.last_name LIKE %s"
                + " OR CONCAT(s.first_name, ' ', s.last_name) LIKE %s"
                + " ORDER BY s.last_name, s.first_name",
                (pattern, pattern, pattern),
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()


def search_students_by_number(student_number: str) -> list[StudentData]:
    """Find a student by an exact student number."""
    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                _STUDENT_SELECT + " WHERE s.student_number = %s",
                (student_number.strip(),),
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()


def create_student(student: StudentData) -> int:
    """Insert a student using the approved schema and return its generated ID."""
    columns = ", ".join(_STUDENT_WRITE_FIELDS)
    placeholders = ", ".join("%s" for _ in _STUDENT_WRITE_FIELDS)
    sql = f"INSERT INTO students ({columns}) VALUES ({placeholders})"
    with create_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql, _student_values(student))
            connection.commit()
            return int(cursor.lastrowid)
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def update_student(student_id: int, student: StudentData) -> bool:
    """Update student and programme fields; return whether a row was matched."""
    assignments = ", ".join(f"{field} = %s" for field in _STUDENT_WRITE_FIELDS)
    sql = f"UPDATE students SET {assignments} WHERE student_id = %s"
    values = _student_values(student) + (student_id,)
    with create_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql, values)
            connection.commit()
            return cursor.rowcount > 0
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def delete_student(student_id: int) -> bool:
    """Delete only students with no enrolments; never remove enrolment rows.

    The student row is locked while checking for enrolments so a concurrent
    enrolment insert cannot race past the guard. Existing enrolments raise
    :class:`StudentHasEnrollmentsError`; a missing student returns ``False``.
    """
    with create_connection() as connection:
        cursor = connection.cursor()
        try:
            connection.start_transaction()
            cursor.execute(
                "SELECT student_id FROM students WHERE student_id = %s FOR UPDATE",
                (student_id,),
            )
            if cursor.fetchone() is None:
                connection.rollback()
                return False

            cursor.execute(
                "SELECT 1 FROM student_courses WHERE student_id = %s LIMIT 1",
                (student_id,),
            )
            if cursor.fetchone() is not None:
                raise StudentHasEnrollmentsError(
                    "Student cannot be deleted while course enrolments exist."
                )

            cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
            deleted = cursor.rowcount > 0
            connection.commit()
            return deleted
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def get_dashboard_statistics() -> dict[str, int]:
    """Return summary counts for students, courses, and departments."""
    sql = """
        SELECT (SELECT COUNT(*) FROM students) AS total_students,
               (SELECT COUNT(*) FROM courses) AS total_courses,
               (SELECT COUNT(*) FROM departments) AS total_departments
    """
    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
            return {key: int(value) for key, value in row.items()}
        finally:
            cursor.close()
