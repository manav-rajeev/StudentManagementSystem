"""Parameterized persistence operations for student course enrolments."""

from __future__ import annotations

from typing import Any, Iterable

from mysql.connector import IntegrityError, errorcode

from database.connection import create_connection


EnrollmentData = dict[str, Any]


class DuplicateEnrollmentError(ValueError):
    """Raised when the schema's student/course/term unique key is violated."""


_ENROLLMENT_SELECT = """
    SELECT sc.student_course_id, sc.student_id, sc.course_id,
           sc.academic_year, sc.semester, sc.enrollment_status, sc.grade,
           sc.enrolled_at,
           s.student_number, s.first_name, s.last_name,
           s.program_id AS student_program_id,
           sp.program_code AS student_program_code,
           sp.program_name AS student_program_name,
           c.course_code, c.course_name, c.credits,
           c.program_id AS course_program_id,
           cp.program_code AS course_program_code,
           cp.program_name AS course_program_name
      FROM student_courses AS sc
      JOIN students AS s ON s.student_id = sc.student_id
      JOIN programs AS sp ON sp.program_id = s.program_id
      JOIN courses AS c ON c.course_id = sc.course_id
      JOIN programs AS cp ON cp.program_id = c.program_id
"""


def enroll_student(
    student_id: int,
    course_id: int,
    academic_year: str,
    semester: str,
    enrollment_status: str = "Enrolled",
    grade: str | None = None,
) -> int:
    """Create one enrolment and return its generated student_course_id."""
    enrolled_ids = enroll_student_in_courses(
        student_id,
        (course_id,),
        academic_year,
        semester,
        enrollment_status,
        grade,
    )
    return enrolled_ids[0]


def enroll_student_in_courses(
    student_id: int,
    course_ids: Iterable[int],
    academic_year: str,
    semester: str,
    enrollment_status: str = "Enrolled",
    grade: str | None = None,
) -> list[int]:
    """Insert multiple course enrolments atomically for one academic term.

    A duplicate student/course/year/semester rolls back the entire batch and
    raises :class:`DuplicateEnrollmentError`. Courses from any programme are
    accepted; this repository does not impose a programme-match restriction.
    """
    selected_course_ids = tuple(course_ids)
    if not selected_course_ids:
        return []

    sql = """
        INSERT INTO student_courses
            (student_id, course_id, academic_year, semester,
             enrollment_status, grade)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    created_ids: list[int] = []
    with create_connection() as connection:
        cursor = connection.cursor()
        try:
            connection.start_transaction()
            for course_id in selected_course_ids:
                cursor.execute(
                    sql,
                    (student_id, course_id, academic_year, semester,
                     enrollment_status, grade),
                )
                created_ids.append(int(cursor.lastrowid))
            connection.commit()
            return created_ids
        except IntegrityError as error:
            connection.rollback()
            if error.errno == errorcode.ER_DUP_ENTRY:
                raise DuplicateEnrollmentError(
                    "This student is already enrolled in a selected course "
                    "for that academic year and semester."
                ) from error
            raise
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def list_enrollments_for_student(student_id: int) -> list[EnrollmentData]:
    """Return a student's enrolments with student, course, and programme data."""
    sql = (
        _ENROLLMENT_SELECT
        + " WHERE sc.student_id = %s"
        + " ORDER BY sc.academic_year DESC, sc.semester, c.course_name"
    )
    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (student_id,))
            return list(cursor.fetchall())
        finally:
            cursor.close()


def list_enrollments_by_term(
    academic_year: str, semester: str
) -> list[EnrollmentData]:
    """Return all student enrolments for one academic year and semester."""
    sql = (
        _ENROLLMENT_SELECT
        + " WHERE sc.academic_year = %s AND sc.semester = %s"
        + " ORDER BY s.last_name, s.first_name, c.course_name"
    )
    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (academic_year, semester))
            return list(cursor.fetchall())
        finally:
            cursor.close()


def update_enrollment(
    student_course_id: int,
    grade: str | None,
    enrollment_status: str,
) -> bool:
    """Update the grade and status for one enrolment."""
    with create_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE student_courses "
                "SET grade = %s, enrollment_status = %s "
                "WHERE student_course_id = %s",
                (grade, enrollment_status, student_course_id),
            )
            connection.commit()
            return cursor.rowcount > 0
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def remove_enrollment(student_course_id: int) -> bool:
    """Explicitly remove one enrolment row by its primary key."""
    with create_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM student_courses WHERE student_course_id = %s",
                (student_course_id,),
            )
            connection.commit()
            return cursor.rowcount > 0
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def has_student_enrollments(student_id: int) -> bool:
    """Return whether a student currently has one or more enrolment rows."""
    with create_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM student_courses WHERE student_id = %s LIMIT 1",
                (student_id,),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()


def course_belongs_to_program(course_id: int, program_id: int) -> bool:
    """Check course ownership for programme-change review workflows."""
    with create_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM courses WHERE course_id = %s AND program_id = %s",
                (course_id, program_id),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
