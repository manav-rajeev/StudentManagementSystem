"""Offline tests for enrolment validation and service orchestration."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend import enrollment_service
from database import enrollment_repository


class EnrollmentValidationTests(unittest.TestCase):
    def test_academic_year_must_be_consecutive_four_digit_range(self) -> None:
        self.assertEqual(enrollment_service.validate_academic_year("2026-2027"), "2026-2027")
        for invalid in ("2026-2028", "2026/2027", "2026-27", "", "2027-2026"):
            with self.subTest(value=invalid):
                with self.assertRaises(ValueError):
                    enrollment_service.validate_academic_year(invalid)

    def test_allowed_semesters(self) -> None:
        for semester in ("Semester 1", "Semester 2", "Summer"):
            with self.subTest(semester=semester):
                self.assertEqual(enrollment_service.validate_semester(semester), semester)
        with self.assertRaises(ValueError):
            enrollment_service.validate_semester("Fall")

    def test_allowed_grades_and_blank_grade(self) -> None:
        for grade in ("O", "A+", "A", "B+", "B", "C", "P", "F"):
            with self.subTest(grade=grade):
                self.assertEqual(enrollment_service.validate_grade(grade), grade)
        self.assertEqual(enrollment_service.validate_grade(" a+ "), "A+")
        self.assertIsNone(enrollment_service.validate_grade(None))
        self.assertIsNone(enrollment_service.validate_grade("  "))
        with self.assertRaises(ValueError):
            enrollment_service.validate_grade("D")

    def test_allowed_enrollment_statuses(self) -> None:
        for status in ("Enrolled", "Completed", "Dropped"):
            with self.subTest(status=status):
                self.assertEqual(enrollment_service.validate_enrollment_status(status), status)
        with self.assertRaises(ValueError):
            enrollment_service.validate_enrollment_status("Withdrawn")


class EnrollmentServiceTests(unittest.TestCase):
    @patch("backend.enrollment_service.enrollment_repository.enroll_student", return_value=101)
    @patch("backend.enrollment_service.enrollment_repository.course_belongs_to_program")
    def test_enroll_single_course_allows_cross_programme_course(
        self, course_belongs, enroll_student
    ) -> None:
        result = enrollment_service.enroll_course(
            8, 17, "2026-2027", "Summer", grade="A"
        )
        self.assertEqual(result, 101)
        enroll_student.assert_called_once_with(8, 17, "2026-2027", "Summer", "Enrolled", "A")
        course_belongs.assert_not_called()

    @patch("backend.enrollment_service.enrollment_repository.enroll_student_in_courses",
           return_value=[101, 102])
    def test_enroll_multiple_courses_uses_one_term_and_all_programmes(self, enroll_courses) -> None:
        self.assertEqual(
            enrollment_service.enroll_courses(8, [17, 22], "2026-2027", "Semester 1"),
            [101, 102],
        )
        enroll_courses.assert_called_once_with(
            8, (17, 22), "2026-2027", "Semester 1", "Enrolled", None
        )

    @patch("backend.enrollment_service.enrollment_repository.enroll_student")
    def test_invalid_term_values_do_not_reach_repository(self, enroll_student) -> None:
        invalid_calls = (
            ("2026-2028", "Semester 1"),
            ("2026/2027", "Semester 1"),
            ("2026-27", "Semester 1"),
            ("2026-2027", "Fall"),
        )
        for academic_year, semester in invalid_calls:
            with self.subTest(academic_year=academic_year, semester=semester):
                with self.assertRaises(ValueError):
                    enrollment_service.enroll_course(8, 17, academic_year, semester)
        enroll_student.assert_not_called()

    @patch("backend.enrollment_service.enrollment_repository.enroll_student")
    def test_invalid_grade_and_status_do_not_reach_repository(self, enroll_student) -> None:
        with self.assertRaises(ValueError):
            enrollment_service.enroll_course(8, 17, "2026-2027", "Semester 2", grade="D")
        with self.assertRaises(ValueError):
            enrollment_service.enroll_course(
                8, 17, "2026-2027", "Semester 2", enrollment_status="Withdrawn"
            )
        enroll_student.assert_not_called()

    @patch("backend.enrollment_service.enrollment_repository.enroll_student",
           side_effect=enrollment_repository.DuplicateEnrollmentError("duplicate"))
    def test_duplicate_repository_error_becomes_user_friendly_service_error(self, enroll_student) -> None:
        with self.assertRaisesRegex(enrollment_service.DuplicateEnrollmentError, "already enrolled"):
            enrollment_service.enroll_course(8, 17, "2026-2027", "Semester 1")
        enroll_student.assert_called_once()

    @patch("backend.enrollment_service.enrollment_repository.list_enrollments_for_student",
           return_value=[{"student_course_id": 10}])
    @patch("backend.enrollment_service.enrollment_repository.list_enrollments_by_term",
           return_value=[{"student_course_id": 11}])
    def test_listing_methods_validate_and_delegate(self, by_term, by_student) -> None:
        self.assertEqual(enrollment_service.list_student_enrollments(8), [{"student_course_id": 10}])
        self.assertEqual(
            enrollment_service.list_enrollments_by_term("2026-2027", "Summer"),
            [{"student_course_id": 11}],
        )
        by_student.assert_called_once_with(8)
        by_term.assert_called_once_with("2026-2027", "Summer")

    @patch("backend.enrollment_service.enrollment_repository.update_enrollment", return_value=True)
    def test_grade_and_status_updates_preserve_companion_value(self, update_enrollment) -> None:
        self.assertTrue(enrollment_service.update_grade(
            10, "A+", current_enrollment_status="Completed"
        ))
        update_enrollment.assert_called_with(10, "A+", "Completed")
        self.assertTrue(enrollment_service.update_enrollment_status(
            10, "Dropped", current_grade="A+"
        ))
        update_enrollment.assert_called_with(10, "A+", "Dropped")

    @patch("backend.enrollment_service.enrollment_repository.remove_enrollment", return_value=True)
    def test_explicit_removal_delegates_by_enrolment_id(self, remove_enrollment) -> None:
        self.assertTrue(enrollment_service.remove_enrollment(10))
        remove_enrollment.assert_called_once_with(10)

    @patch("backend.enrollment_service.enrollment_repository.enroll_student_in_courses")
    def test_empty_course_selection_is_rejected(self, enroll_courses) -> None:
        with self.assertRaisesRegex(ValueError, "at least one course"):
            enrollment_service.enroll_courses(8, [], "2026-2027", "Semester 1")
        enroll_courses.assert_not_called()


if __name__ == "__main__":
    unittest.main()
