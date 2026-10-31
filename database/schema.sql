-- Student Management System database schema and repeat-safe reference data.
-- Target: MySQL 8.0+; this script has not been executed.

-- ============================================================================
-- Database
-- ============================================================================

CREATE DATABASE IF NOT EXISTS student_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE student_management;

-- ============================================================================
-- Core tables
-- Parent tables are created before tables that reference them.
-- ============================================================================

CREATE TABLE IF NOT EXISTS departments (
    department_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    department_code VARCHAR(20) NOT NULL,
    department_name VARCHAR(120) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (department_id),
    UNIQUE KEY uq_departments_code (department_code),
    UNIQUE KEY uq_departments_name (department_name)
) ENGINE=InnoDB
  DEFAULT CHARACTER SET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS programs (
    program_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    department_id INT UNSIGNED NOT NULL,
    program_code VARCHAR(20) NOT NULL,
    program_name VARCHAR(160) NOT NULL,
    degree_level ENUM('Associate', 'Bachelor', 'Master', 'Doctorate') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (program_id),
    UNIQUE KEY uq_programs_code (program_code),
    UNIQUE KEY uq_programs_name_department (department_id, program_name),
    KEY ix_programs_department (department_id),
    CONSTRAINT fk_programs_department
        FOREIGN KEY (department_id)
        REFERENCES departments (department_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB
  DEFAULT CHARACTER SET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS courses (
    course_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    program_id INT UNSIGNED NOT NULL,
    course_code VARCHAR(30) NOT NULL,
    course_name VARCHAR(160) NOT NULL,
    credits TINYINT UNSIGNED NOT NULL DEFAULT 3,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (course_id),
    UNIQUE KEY uq_courses_code (course_code),
    UNIQUE KEY uq_courses_name_program (program_id, course_name),
    KEY ix_courses_program (program_id),
    CONSTRAINT fk_courses_program
        FOREIGN KEY (program_id)
        REFERENCES programs (program_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB
  DEFAULT CHARACTER SET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS students (
    student_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    program_id INT UNSIGNED NOT NULL,
    student_number VARCHAR(40) NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    date_of_birth DATE NULL,
    gender VARCHAR(30) NULL,
    email VARCHAR(254) NULL,
    phone VARCHAR(30) NULL,
    address VARCHAR(500) NULL,
    admission_date DATE NOT NULL,
    status ENUM('Active', 'Inactive', 'Graduated') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id),
    UNIQUE KEY uq_students_number (student_number),
    UNIQUE KEY uq_students_email (email),
    KEY ix_students_name (last_name, first_name),
    KEY ix_students_program (program_id),
    KEY ix_students_status (status),
    CONSTRAINT fk_students_program
        FOREIGN KEY (program_id)
        REFERENCES programs (program_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB
  DEFAULT CHARACTER SET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS student_courses (
    student_course_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    student_id INT UNSIGNED NOT NULL,
    course_id INT UNSIGNED NOT NULL,
    academic_year CHAR(9) NOT NULL,
    semester ENUM('Semester 1', 'Semester 2', 'Summer') NOT NULL,
    enrollment_status ENUM('Enrolled', 'Completed', 'Dropped') NOT NULL DEFAULT 'Enrolled',
    grade VARCHAR(5) NULL,
    enrolled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_course_id),
    UNIQUE KEY uq_student_course_term
        (student_id, course_id, academic_year, semester),
    KEY ix_student_courses_course_term (course_id, academic_year, semester),
    CONSTRAINT fk_student_courses_student
        FOREIGN KEY (student_id)
        REFERENCES students (student_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_student_courses_course
        FOREIGN KEY (course_id)
        REFERENCES courses (course_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB
  DEFAULT CHARACTER SET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================================
-- Initial reference data
-- INSERT IGNORE plus unique keys makes these inserts safe to rerun. Existing
-- rows with the same unique codes are preserved and are not overwritten.
-- ============================================================================

-- 5 departments
INSERT IGNORE INTO departments (department_code, department_name) VALUES
    ('SCI',  'Science and Computing'),
    ('ENG',  'Engineering'),
    ('BUS',  'Business and Commerce'),
    ('ART',  'Arts and Humanities'),
    ('HLTH', 'Health Sciences');

-- 6 degree programmes. Each programme is attached to its owning department.
INSERT IGNORE INTO programs
    (department_id, program_code, program_name, degree_level)
SELECT d.department_id, seed.program_code, seed.program_name, seed.degree_level
FROM departments AS d
JOIN (
    SELECT 'BSCS' AS program_code, 'Bachelor of Science in Computer Science' AS program_name,
           'Bachelor' AS degree_level, 'SCI' AS department_code
    UNION ALL
    SELECT 'BSIT', 'Bachelor of Science in Information Technology', 'Bachelor', 'SCI'
    UNION ALL
    SELECT 'BSEE', 'Bachelor of Science in Electrical Engineering', 'Bachelor', 'ENG'
    UNION ALL
    SELECT 'BBA', 'Bachelor of Business Administration', 'Bachelor', 'BUS'
    UNION ALL
    SELECT 'BCOM', 'Bachelor of Commerce', 'Bachelor', 'BUS'
    UNION ALL
    SELECT 'BAENG', 'Bachelor of Arts in English', 'Bachelor', 'ART'
) AS seed
    ON seed.department_code = d.department_code;

-- 9 initial subjects/courses, each attached to its degree programme.
INSERT IGNORE INTO courses (program_id, course_code, course_name, credits)
SELECT p.program_id, seed.course_code, seed.course_name, seed.credits
FROM programs AS p
JOIN (
    SELECT 'CS101' AS course_code, 'Introduction to Programming' AS course_name,
           3 AS credits, 'BSCS' AS program_code
    UNION ALL
    SELECT 'CS102', 'Data Structures', 3, 'BSCS'
    UNION ALL
    SELECT 'IT101', 'Database Systems', 3, 'BSIT'
    UNION ALL
    SELECT 'IT102', 'Networking Fundamentals', 3, 'BSIT'
    UNION ALL
    SELECT 'EE101', 'Engineering Mathematics', 4, 'BSEE'
    UNION ALL
    SELECT 'EE102', 'Circuit Analysis', 4, 'BSEE'
    UNION ALL
    SELECT 'BA101', 'Principles of Management', 3, 'BBA'
    UNION ALL
    SELECT 'BC101', 'Financial Accounting', 3, 'BCOM'
    UNION ALL
    SELECT 'EN101', 'Academic Writing', 3, 'BAENG'
) AS seed
    ON seed.program_code = p.program_code;
