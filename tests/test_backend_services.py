"""Offline tests for student service validation and workflows."""

from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from backend import student_service
from database.student_repository import StudentHasEnrollmentsError


def valid_student(**updates):
    data = {
        "student_number": "ST-1001",
        "program_id": 2,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "date_of_birth": "1815-12-10",
        "gender": "Female",
        "email": "ada@example.edu",
        "phone": "+1 555 0100",
        "address": "1 Analytical Engine Way",
        "admission_date": "2026-08-15",
        "status": "Active",
    }
    data.update(updates)
    return data


class StudentValidationTests(unittest.TestCase):
    def test_registration_validation_normalizes_student_data(self) -> None:
        result = student_service.validate_student(valid_student(
            student_number=" ST-1001 ", first_name=" Ada ", email="", phone="  ",
        ))
        self.assertEqual(result["student_number"], "ST-1001")
        self.assertEqual(result["program_id"], 2)
        self.assertEqual(result["date_of_birth"], date(1815, 12, 10))
        self.assertEqual(result["admission_date"], date(2026, 8, 15))
        self.assertIsNone(result["email"])
        self.assertIsNone(result["phone"])
        self.assertEqual(result["status"], "Active")

    def test_update_validation_accepts_all_student_statuses(self) -> None:
        for status in ("Active", "Inactive", "Graduated"):
            with self.subTest(status=status):
                self.assertEqual(student_service.validate_student(valid_student(status=status))["status"], status)

    def test_missing_required_student_details_are_rejected(self) -> None:
        invalid_cases = (
            ("student_number", ""), ("program_id", None), ("first_name", " "),
            ("last_name", ""), ("admission_date", ""),
        )
        for field, value in invalid_cases:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    student_service.validate_student(valid_student(**{field: value}))

    def test_invalid_email_dates_and_status_are_rejected(self) -> None:
        invalid_data = (
            ("email", "not-an-email"),
            ("date_of_birth", "1815-02-30"),
            ("date_of_birth", "18151210"),
            ("admission_date", "2026/08/15"),
            ("admission_date", "2026-02-30"),
            ("status", "Enrolled"),
        )
        for field, value in invalid_data:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    student_service.validate_student(valid_student(**{field: value}))

    def test_old_student_course_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "legacy field"):
            student_service.validate_student(valid_student(roll_number="OLD", course_id=3))


class StudentServiceTests(unittest.TestCase):
    @patch("backend.student_service.student_repository.create_student", return_value=42)
    def test_register_student_passes_normalized_schema_fields(self, create_student) -> None:
        self.assertEqual(student_service.register_student(valid_student()), 42)
        payload = create_student.call_args.args[0]
        self.assertEqual(payload["student_number"], "ST-1001")
        self.assertEqual(payload["program_id"], 2)
        self.assertEqual(payload["admission_date"], date(2026, 8, 15))
        self.assertEqual(payload["status"], "Active")
        self.assertNotIn("course_id", payload)
        self.assertNotIn("roll_number", payload)

    @patch("backend.student_service.student_repository.get_student_by_id")
    @patch("backend.student_service.student_repository.update_student", return_value=True)
    def test_update_student_validates_then_updates(self, update_student, get_student) -> None:
        get_student.return_value = {"student_id": 8, "program_id": 2}
        self.assertTrue(student_service.update_student(8, valid_student(status="Inactive")))
        update_student.assert_called_once_with(8, student_service.validate_student(valid_student(status="Inactive")))

    @patch("backend.student_service.student_repository.get_student_by_id")
    @patch("backend.student_service.student_repository.update_student")
    def test_update_rejects_invalid_data_before_repository_write(
        self, update_student, get_student
    ) -> None:
        with self.assertRaisesRegex(ValueError, "Admission date"):
            student_service.update_student(8, valid_student(admission_date=""))
        get_student.assert_not_called()
        update_student.assert_not_called()

    @patch("backend.student_service.student_repository.list_students", return_value=[{"student_id": 1}])
    @patch("backend.student_service.student_repository.search_students_by_name", return_value=[{"student_id": 9}])
    @patch("backend.student_service.student_repository.search_students_by_number", return_value=[{"student_id": 10}])
    @patch("backend.student_service.student_repository.get_student_by_id")
    def test_retrieval_and_search_by_id_name_and_number(
        self, get_student, by_number, by_name, list_students
    ) -> None:
        get_student.return_value = {"student_id": 8}
        self.assertEqual(student_service.get_student(8), {"student_id": 8})
        self.assertEqual(student_service.list_students(), [{"student_id": 1}])
        self.assertEqual(student_service.search_students("8"), [{"student_id": 8}])
        get_student.return_value = None
        self.assertEqual(student_service.search_students("8"), [{"student_id": 10}])
        self.assertEqual(student_service.search_students("Ada"), [{"student_id": 9}])
        by_number.assert_called_once_with("8")
        by_name.assert_called_once_with("Ada")

    @patch("backend.student_service.student_repository.delete_student",
           side_effect=StudentHasEnrollmentsError("Student cannot be deleted while course enrolments exist."))
    def test_protected_student_deletion_propagates_repository_message(self, delete_student) -> None:
        with self.assertRaisesRegex(StudentHasEnrollmentsError, "course enrolments exist"):
            student_service.remove_student(8)
        delete_student.assert_called_once_with(8)

    @patch("backend.student_service.enrollment_repository.list_enrollments_for_student")
    @patch("backend.student_service.student_repository.get_student_by_id")
    def test_programme_change_review_lists_out_of_programme_courses(
        self, get_student, list_enrollments
    ) -> None:
        get_student.return_value = {"student_id": 8, "program_id": 2}
        list_enrollments.return_value = [
            {"course_id": 10, "course_code": "CS101", "course_name": "Programming",
             "course_program_id": 1, "course_program_name": "Computer Science"},
            {"course_id": 11, "course_code": "IT101", "course_name": "Networks",
             "course_program_id": 3, "course_program_name": "Information Technology"},
        ]
        review = student_service.review_program_change(8, 3)
        self.assertTrue(review.confirmation_required)
        self.assertEqual(review.current_program_id, 2)
        self.assertEqual(review.proposed_program_id, 3)
        self.assertEqual([item["course_id"] for item in review.incompatible_enrollments], [10])

    @patch("backend.student_service.student_repository.update_student", return_value=True)
    @patch("backend.student_service.enrollment_repository.list_enrollments_for_student")
    @patch("backend.student_service.student_repository.get_student_by_id")
    @patch("backend.student_service.enrollment_repository.remove_enrollment")
    def test_program_change_confirmation_preserves_enrolment_rows(
        self, remove_enrollment, get_student, list_enrollments, update_student
    ) -> None:
        get_student.return_value = {"student_id": 8, "program_id": 2}
        list_enrollments.return_value = [
            {"student_course_id": 44, "course_id": 10, "course_code": "CS101",
             "course_name": "Programming", "course_program_id": 1,
             "course_program_name": "Computer Science"},
        ]
        result = student_service.update_student(
            8, valid_student(program_id=3), confirm_program_change=True
        )
        self.assertTrue(result)
        update_student.assert_called_once()
        self.assertEqual(update_student.call_args.args[1]["program_id"], 3)
        self.assertEqual(list_enrollments.call_count, 1)
        # Only the student repository is mutated; enrolment records are preserved.
        remove_enrollment.assert_not_called()

    @patch("backend.student_service.student_repository.update_student")
    @patch("backend.student_service.enrollment_repository.list_enrollments_for_student")
    @patch("backend.student_service.student_repository.get_student_by_id")
    def test_programme_change_requires_confirmation_before_update(
        self, get_student, list_enrollments, update_student
    ) -> None:
        get_student.return_value = {"student_id": 8, "program_id": 2}
        list_enrollments.return_value = [{
            "course_id": 10, "course_program_id": 1, "course_code": "CS101",
            "course_name": "Programming", "course_program_name": "Computer Science",
        }]
        result = student_service.update_student(8, valid_student(program_id=3))
        self.assertIsInstance(result, student_service.ProgramChangeReview)
        self.assertFalse(update_student.called)


if __name__ == "__main__":
    unittest.main()
