"""Read-only lookups for departments, programmes, and courses."""

from __future__ import annotations

from typing import Any

from database.connection import create_connection


LookupRow = dict[str, Any]


def list_departments() -> list[LookupRow]:
    """Return all departments in display order."""
    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT department_id, department_code, department_name "
                "FROM departments ORDER BY department_name"
            )
            return list(cursor.fetchall())
        finally:
            cursor.close()


def list_programmes(department_id: int | None = None) -> list[LookupRow]:
    """Return all programmes, optionally filtered by owning department."""
    sql = """
        SELECT p.program_id, p.program_code, p.program_name, p.degree_level,
               p.department_id, d.department_code, d.department_name
          FROM programs AS p
          JOIN departments AS d ON d.department_id = p.department_id
    """
    params: tuple[int, ...] = ()
    if department_id is not None:
        sql += " WHERE p.department_id = %s"
        params = (department_id,)
    sql += " ORDER BY d.department_name, p.program_name"

    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return list(cursor.fetchall())
        finally:
            cursor.close()


def list_courses(program_id: int | None = None) -> list[LookupRow]:
    """Return courses with their owning programme and department.

    With no programme ID, courses from every programme are returned. This
    supports cross-programme enrolments, as approved by the project rules.
    """
    sql = """
        SELECT c.course_id, c.course_code, c.course_name, c.credits,
               c.program_id, p.program_code, p.program_name, p.degree_level,
               p.department_id, d.department_code, d.department_name
          FROM courses AS c
          JOIN programs AS p ON p.program_id = c.program_id
          JOIN departments AS d ON d.department_id = p.department_id
    """
    params: tuple[int, ...] = ()
    if program_id is not None:
        sql += " WHERE c.program_id = %s"
        params = (program_id,)
    sql += " ORDER BY p.program_name, c.course_name"

    with create_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return list(cursor.fetchall())
        finally:
            cursor.close()


def list_all_courses_for_enrollment() -> list[LookupRow]:
    """Return courses across all programmes for enrolment selection."""
    return list_courses()
