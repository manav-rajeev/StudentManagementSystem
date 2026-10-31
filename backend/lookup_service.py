"""Application-facing lookup operations for Tkinter dropdowns."""

from __future__ import annotations

from typing import Any

from database import lookup_repository


LookupData = dict[str, Any]


def list_departments() -> list[LookupData]:
    """List departments as dictionaries containing ID, code, and name."""
    return lookup_repository.list_departments()


def list_all_programmes() -> list[LookupData]:
    """List programmes with their department and degree-level details."""
    return lookup_repository.list_programmes()


def list_programmes_by_department(department_id: int) -> list[LookupData]:
    """List programmes belonging to one department."""
    return lookup_repository.list_programmes(department_id)


def list_all_courses() -> list[LookupData]:
    """List courses and their owning programme/department details."""
    return lookup_repository.list_courses()


def list_courses_by_programme(program_id: int) -> list[LookupData]:
    """List courses belonging to one programme."""
    return lookup_repository.list_courses(program_id)


def list_courses_for_cross_programme_enrolment() -> list[LookupData]:
    """List courses across every programme for unrestricted course selection."""
    return lookup_repository.list_all_courses_for_enrollment()


# Short aliases retained for the existing UI call sites until the frontend
# migration replaces them with the explicit list_* methods above.
def departments() -> list[LookupData]:
    return list_departments()


def programmes(department_id: int | None = None) -> list[LookupData]:
    return lookup_repository.list_programmes(department_id)


def courses(department_id: int | None = None) -> list[LookupData]:
    """Legacy UI helper that filters all-course results by owning department."""
    rows = lookup_repository.list_courses()
    if department_id is None:
        return rows
    return [row for row in rows if int(row["department_id"]) == int(department_id)]
