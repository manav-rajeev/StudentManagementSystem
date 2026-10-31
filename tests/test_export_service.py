"""CSV export tests for student and student-course-term records."""

from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from backend import export_service


class StudentExportTests(unittest.TestCase):
    def test_student_export_has_new_schema_fields_one_row_per_student(self) -> None:
        records = [
            {
                "student_number": "ST-1001", "first_name": "Ada", "last_name": "Lovelace",
                "email": "ada@example.edu", "phone": None,
                "department_name": "Science and Computing",
                "program_name": "Computer Science", "admission_date": date(2026, 8, 15),
                "status": "Active",
            },
            {
                "student_number": "ST-1002", "first_name": "Grace", "last_name": "Hopper",
                "email": None, "phone": "555-0120", "department_name": "Engineering",
                "program_name": "Electrical Engineering", "admission_date": "2026-08-16",
                "status": "Inactive",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "exports" / "students.csv"
            count = export_service.export_students(records, destination)
            with destination.open("r", newline="", encoding="utf-8-sig") as csv_file:
                rows = list(csv.DictReader(csv_file))

        self.assertEqual(count, 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Student Number"], "ST-1001")
        self.assertEqual(rows[0]["Programme"], "Computer Science")
        self.assertEqual(rows[0]["Department"], "Science and Computing")
        self.assertEqual(rows[0]["Admission Date"], "2026-08-15")
        self.assertEqual(rows[0]["Phone"], "")
        self.assertEqual(rows[1]["Email"], "")
        headers = set(rows[0])
        self.assertNotIn("Roll Number", headers)
        self.assertNotIn("Course", headers)
        self.assertNotIn("Course Name", headers)

    def test_empty_student_export_still_writes_expected_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "empty.csv"
            self.assertEqual(export_service.export_students([], destination), 0)
            with destination.open("r", newline="", encoding="utf-8-sig") as csv_file:
                self.assertEqual(
                    next(csv.reader(csv_file)),
                    [
                        "Student Number", "First Name", "Last Name", "Email", "Phone",
                        "Department", "Programme", "Admission Date", "Status",
                    ],
                )


class EnrollmentExportTests(unittest.TestCase):
    def test_enrollment_export_writes_one_row_per_enrollment_and_supports_cross_programme(self) -> None:
        records = [
            {
                "student_number": "ST-1001", "first_name": "Ada", "last_name": "Lovelace",
                "course_code": "IT101", "course_name": "Database Systems",
                "course_program_name": "Information Technology",
                "student_program_name": "Computer Science",
                "academic_year": "2026-2027", "semester": "Semester 1", "grade": "A+",
                "enrollment_status": "Completed",
                "enrolled_at": datetime(2026, 8, 20, 9, 30),
            },
            {
                "student_number": "ST-1001", "student_name": "Ada Lovelace",
                "course_code": "CS102", "course_name": "Data Structures",
                "course_program": "Computer Science", "academic_year": "2026-2027",
                "semester": "Semester 1", "grade": None,
                "enrollment_status": "Enrolled", "enrolled_at": None,
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "enrollments.csv"
            count = export_service.export_enrollments(records, destination)
            with destination.open("r", newline="", encoding="utf-8-sig") as csv_file:
                rows = list(csv.DictReader(csv_file))

        self.assertEqual(count, 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Student Name"], "Ada Lovelace")
        self.assertEqual(rows[0]["Course Programme"], "Information Technology")
        self.assertNotEqual(rows[0]["Course Programme"], records[0]["student_program_name"])
        self.assertEqual(rows[0]["Enrolled At"], "2026-08-20 09:30:00")
        self.assertEqual(rows[1]["Course Programme"], "Computer Science")
        self.assertEqual(rows[1]["Grade"], "")
        self.assertEqual(rows[1]["Enrolled At"], "")

    def test_enrollment_header_uses_enrolment_columns_not_legacy_student_course_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "header.csv"
            export_service.export_enrollments([], destination)
            with destination.open("r", newline="", encoding="utf-8-sig") as csv_file:
                headers = next(csv.reader(csv_file))

        self.assertEqual(headers, [
            "Student Number", "Student Name", "Course Code", "Course Name",
            "Course Programme", "Academic Year", "Semester", "Grade",
            "Enrollment Status", "Enrolled At",
        ])
        self.assertNotIn("Roll Number", headers)
        self.assertNotIn("Course", headers)


if __name__ == "__main__":
    unittest.main()
