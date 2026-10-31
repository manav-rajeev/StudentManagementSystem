"""Repository unit tests with fake MySQL connections; no live server needed."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from mysql.connector import IntegrityError, errorcode

from database import enrollment_repository, lookup_repository, student_repository


class FakeCursor:
    def __init__(self, connection) -> None:
        self.connection = connection
        self.calls: list[tuple[str, object]] = []
        self.lastrowid = 100
        self.rowcount = 1

    def execute(self, sql, params=None) -> None:
        self.calls.append((sql, params))
        call_number = len(self.calls)
        if call_number in self.connection.execute_errors:
            raise self.connection.execute_errors[call_number]
        if sql.lstrip().upper().startswith("INSERT"):
            self.lastrowid += 1

    def fetchone(self):
        if self.connection.fetchone_results:
            return self.connection.fetchone_results.pop(0)
        return self.connection.fetchone_result

    def fetchall(self):
        return list(self.connection.fetchall_result)

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self, *, fetchone=None, fetchone_results=None, fetchall=None,
                 execute_errors=None) -> None:
        self.fetchone_result = fetchone
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_result = list(fetchall or [])
        self.execute_errors = dict(execute_errors or {})
        self.last_cursor = FakeCursor(self)
        self.commit_count = 0
        self.rollback_count = 0
        self.start_transaction_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        pass

    def cursor(self, **_kwargs):
        return self.last_cursor

    def start_transaction(self) -> None:
        self.start_transaction_count += 1

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def student_record(**updates):
    record = {
        "student_number": "ST-17", "program_id": 3,
        "first_name": "Ada", "last_name": "Lovelace",
        "date_of_birth": None, "gender": None, "email": None,
        "phone": None, "address": None,
        "admission_date": "2026-08-01", "status": "Active",
    }
    record.update(updates)
    return record


class StudentRepositoryTests(unittest.TestCase):
    @patch("database.student_repository.create_connection")
    def test_insert_and_update_use_new_student_columns(self, create_connection) -> None:
        connection = FakeConnection()
        create_connection.return_value = connection
        self.assertEqual(student_repository.create_student(student_record()), 101)
        insert_sql, insert_values = connection.last_cursor.calls[0]
        self.assertIn("student_number", insert_sql)
        self.assertIn("program_id", insert_sql)
        self.assertIn("admission_date", insert_sql)
        self.assertIn("status", insert_sql)
        self.assertNotIn("roll_number", insert_sql)
        self.assertNotIn("course_id", insert_sql)
        self.assertEqual(insert_values[0:4], ("ST-17", 3, "Ada", "Lovelace"))

        self.assertTrue(student_repository.update_student(17, student_record(status="Graduated")))
        update_sql, update_values = connection.last_cursor.calls[1]
        self.assertIn("UPDATE students SET", update_sql)
        self.assertIn("program_id = %s", update_sql)
        self.assertIn("admission_date = %s", update_sql)
        self.assertEqual(update_values[-1], 17)
        self.assertEqual(connection.commit_count, 2)

    @patch("database.student_repository.create_connection")
    def test_list_and_name_search_join_programmes_and_departments(self, create_connection) -> None:
        row = {"student_number": "ST-17", "program_name": "Computer Science"}
        connection = FakeConnection(fetchall=[row])
        create_connection.return_value = connection
        self.assertEqual(student_repository.list_students(), [row])
        list_sql, _ = connection.last_cursor.calls[-1]
        self.assertIn("JOIN programs AS p ON p.program_id = s.program_id", list_sql)
        self.assertIn("JOIN departments AS d ON d.department_id = p.department_id", list_sql)

        self.assertEqual(student_repository.search_students_by_name("Ada"), [row])
        search_sql, params = connection.last_cursor.calls[-1]
        self.assertIn("CONCAT(s.first_name, ' ', s.last_name)", search_sql)
        self.assertEqual(params, ("%Ada%", "%Ada%", "%Ada%"))

    @patch("database.student_repository.create_connection")
    def test_search_student_number_is_parameterized(self, create_connection) -> None:
        connection = FakeConnection(fetchall=[{"student_number": "ST-17"}])
        create_connection.return_value = connection
        self.assertEqual(student_repository.search_students_by_number(" ST-17 "), [{"student_number": "ST-17"}])
        sql, params = connection.last_cursor.calls[-1]
        self.assertIn("s.student_number = %s", sql)
        self.assertEqual(params, ("ST-17",))

    @patch("database.student_repository.create_connection")
    def test_student_delete_is_blocked_when_enrolments_exist(self, create_connection) -> None:
        connection = FakeConnection(fetchone_results=[(8,), (1,)])
        create_connection.return_value = connection
        with self.assertRaises(student_repository.StudentHasEnrollmentsError):
            student_repository.delete_student(8)
        sql_statements = [sql for sql, _ in connection.last_cursor.calls]
        self.assertTrue(any("FROM student_courses" in sql for sql in sql_statements))
        self.assertFalse(any(sql.lstrip().upper().startswith("DELETE") for sql in sql_statements))
        self.assertEqual(connection.rollback_count, 1)
        self.assertEqual(connection.commit_count, 0)


class LookupRepositoryTests(unittest.TestCase):
    @patch("database.lookup_repository.create_connection")
    def test_programme_and_course_lookups_support_filters_and_all_programmes(self, create_connection) -> None:
        connection = FakeConnection(fetchall=[{"course_id": 1, "program_name": "Physics"}])
        create_connection.return_value = connection

        lookup_repository.list_departments()
        lookup_repository.list_programmes()
        lookup_repository.list_programmes(4)
        lookup_repository.list_courses()
        lookup_repository.list_courses(9)
        lookup_repository.list_all_courses_for_enrollment()

        calls = connection.last_cursor.calls
        self.assertIn("FROM departments", calls[0][0])
        self.assertIn("FROM programs AS p", calls[1][0])
        self.assertNotIn("WHERE p.department_id", calls[1][0])
        self.assertIn("WHERE p.department_id = %s", calls[2][0])
        self.assertEqual(calls[2][1], (4,))
        self.assertIn("JOIN programs AS p ON p.program_id = c.program_id", calls[3][0])
        self.assertIn("JOIN departments AS d", calls[3][0])
        self.assertNotIn("WHERE c.program_id", calls[3][0])
        self.assertIn("WHERE c.program_id = %s", calls[4][0])
        self.assertEqual(calls[4][1], (9,))
        self.assertNotIn("WHERE c.program_id", calls[5][0])


class EnrollmentRepositoryTests(unittest.TestCase):
    @patch("database.enrollment_repository.create_connection")
    def test_single_enrolment_uses_schema_columns_and_commits(self, create_connection) -> None:
        connection = FakeConnection()
        create_connection.return_value = connection
        enrollment_id = enrollment_repository.enroll_student(
            8, 12, "2026-2027", "Summer", "Enrolled", None
        )
        self.assertEqual(enrollment_id, 101)
        sql, params = connection.last_cursor.calls[0]
        for column in ("student_id", "course_id", "academic_year", "semester", "enrollment_status", "grade"):
            self.assertIn(column, sql)
        self.assertEqual(params, (8, 12, "2026-2027", "Summer", "Enrolled", None))
        self.assertEqual(connection.start_transaction_count, 1)
        self.assertEqual(connection.commit_count, 1)

    @patch("database.enrollment_repository.create_connection")
    def test_batch_enrolment_is_atomic(self, create_connection) -> None:
        connection = FakeConnection()
        create_connection.return_value = connection
        ids = enrollment_repository.enroll_student_in_courses(
            8, [12, 13], "2026-2027", "Semester 1"
        )
        self.assertEqual(ids, [101, 102])
        self.assertEqual(len(connection.last_cursor.calls), 2)
        self.assertEqual(connection.start_transaction_count, 1)
        self.assertEqual(connection.commit_count, 1)
        self.assertEqual(connection.rollback_count, 0)

    @patch("database.enrollment_repository.create_connection")
    def test_duplicate_enrolment_rolls_back_and_raises_friendly_error(self, create_connection) -> None:
        duplicate_error = IntegrityError("duplicate", errno=errorcode.ER_DUP_ENTRY)
        connection = FakeConnection(execute_errors={2: duplicate_error})
        create_connection.return_value = connection
        with self.assertRaisesRegex(enrollment_repository.DuplicateEnrollmentError, "already enrolled"):
            enrollment_repository.enroll_student_in_courses(
                8, [12, 13], "2026-2027", "Semester 1"
            )
        self.assertEqual(connection.rollback_count, 1)
        self.assertEqual(connection.commit_count, 0)

    @patch("database.enrollment_repository.create_connection")
    def test_enrolment_listing_uses_course_programme_and_term(self, create_connection) -> None:
        rows = [{"course_program_name": "Engineering", "enrollment_status": "Enrolled"}]
        connection = FakeConnection(fetchall=rows)
        create_connection.return_value = connection
        self.assertEqual(enrollment_repository.list_enrollments_for_student(8), rows)
        student_sql, student_params = connection.last_cursor.calls[-1]
        self.assertIn("sc.student_course_id", student_sql)
        self.assertIn("sc.enrolled_at", student_sql)
        self.assertIn("cp.program_name AS course_program_name", student_sql)
        self.assertEqual(student_params, (8,))
        self.assertEqual(enrollment_repository.list_enrollments_by_term("2026-2027", "Summer"), rows)
        term_sql, term_params = connection.last_cursor.calls[-1]
        self.assertIn("sc.academic_year = %s AND sc.semester = %s", term_sql)
        self.assertEqual(term_params, ("2026-2027", "Summer"))

    @patch("database.enrollment_repository.create_connection")
    def test_grade_status_update_and_explicit_removal(self, create_connection) -> None:
        connection = FakeConnection()
        create_connection.return_value = connection
        self.assertTrue(enrollment_repository.update_enrollment(5, "A+", "Completed"))
        update_sql, update_params = connection.last_cursor.calls[-1]
        self.assertIn("SET grade = %s, enrollment_status = %s", update_sql)
        self.assertEqual(update_params, ("A+", "Completed", 5))
        self.assertTrue(enrollment_repository.remove_enrollment(5))
        delete_sql, delete_params = connection.last_cursor.calls[-1]
        self.assertEqual(delete_sql, "DELETE FROM student_courses WHERE student_course_id = %s")
        self.assertEqual(delete_params, (5,))
        self.assertEqual(connection.commit_count, 2)

    @patch("database.enrollment_repository.create_connection")
    def test_enrolment_and_programme_checks_are_parameterized(self, create_connection) -> None:
        connection = FakeConnection(fetchone_results=[(1,), (1,)])
        create_connection.return_value = connection
        self.assertTrue(enrollment_repository.has_student_enrollments(8))
        sql, params = connection.last_cursor.calls[-1]
        self.assertIn("FROM student_courses WHERE student_id = %s", sql)
        self.assertEqual(params, (8,))
        self.assertTrue(enrollment_repository.course_belongs_to_program(12, 3))
        sql, params = connection.last_cursor.calls[-1]
        self.assertEqual(params, (12, 3))
        self.assertIn("course_id = %s AND program_id = %s", sql)


if __name__ == "__main__":
    unittest.main()
