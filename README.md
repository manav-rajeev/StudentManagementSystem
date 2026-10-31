# Student Management System

A desktop application for managing student records and course enrolments, built with **Python**, **Tkinter/ttk**, and **MySQL**.

## Features

- **Dashboard:** View summary counts for students, courses, and departments.
- **Student management:** Register, view, search, edit, and manage student records.
- **Programme management in student records:** Associate each student with a department and academic programme.
- **Course enrolments:** Enrol students in courses across programmes, with academic year and semester details.
- **Grade and status management:** Update grades and enrolment statuses, or remove an enrolment.
- **Validation:** Validate student details, dates, academic-year formats, grades, and status values.
- **CSV exports:** Export student records and a student's course-enrolment records for use in spreadsheet applications.
- **MySQL persistence:** Store application data in a relational database with foreign-key constraints.

## Technology stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Desktop UI | Tkinter / ttk |
| Database | MySQL Server 8.0+ |
| Database connector | mysql-connector-python |
| Configuration | python-dotenv |
| Database administration | MySQL Workbench |

## Project structure

```text
StudentManagementSystem/
├── assets/                 # Application assets
├── backend/                # Business logic and validation services
├── config/                 # Application and database settings
├── database/               # Connection, repositories, and schema
├── frontend/
│   ├── views/              # Dashboard, students, forms, and enrolments
│   └── widgets/            # Reusable UI components
├── tests/                  # Automated unit and repository tests
├── .env.example            # Safe configuration template
├── .gitignore
├── README.md
└── requirements.txt
```

## Prerequisites

- Windows, macOS, or Linux
- Python 3.12
- MySQL Server 8.0 or later
- MySQL Workbench (recommended for database setup and administration)
- Git (optional, for cloning the repository)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/manav-rajeev/StudentManagementSystem.git
cd StudentManagementSystem
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Set up the MySQL database

1. Start MySQL Server.
2. Open MySQL Workbench and connect using an administrative account.
3. Open and execute `database/schema.sql`.
4. The script creates the `student_management` database, its five tables, and initial reference data (departments, programmes, and courses).

The application should connect using a dedicated MySQL account with permissions on the `student_management` database. Avoid using the MySQL root account for normal application access.

### 5. Configure database credentials

Copy `.env.example` to a new file named `.env` in the project root.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your local MySQL connection settings:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=student_management
DB_USER=student_app
DB_PASSWORD=your_local_database_password
```

Use the username and password for the dedicated database account you configured. **Never commit your real `.env` file or share database passwords.** The `.env` file is excluded by `.gitignore`; only the placeholder `.env.example` belongs in Git.

### 6. Run the application

From the project root:

```bash
python -m frontend.app
```

On Windows, if you prefer not to activate the virtual environment, you can run:

```powershell
.\.venv\Scripts\python.exe -m frontend.app
```

## Run the tests

The automated tests are designed to check application services, repository behaviour, enrolment rules, and CSV exports.

```bash
python -m unittest discover -s tests -v
```

The project test suite passed **41 tests** during development. Run the command above in your environment to verify the current checkout.

## Database overview

The schema contains five main tables:

- `departments` — academic departments.
- `programs` — degree programmes linked to departments.
- `courses` — courses linked to their owning programmes.
- `students` — student personal, academic, and admission details.
- `student_courses` — student course enrolments, academic terms, grades, and enrolment statuses.

Foreign keys protect related records, and a unique constraint prevents the same student from being enrolled in the same course twice for the same academic year and semester. Students may enrol in courses owned by other programmes.

## CSV exports

The application supports:
- Exporting student records, including programme and department information.
- Exporting course-enrolment records for a selected student, including course, term, grade, and enrolment status.

CSV files are compatible with spreadsheet applications such as Microsoft Excel.

## Security notes

- Keep database credentials in the local `.env` file.
- Do not commit `.env`, virtual environments, or generated exports.
- Use a dedicated database account for the application rather than the MySQL root account.
- The repository includes `.env.example` as a template with no real password.

## Future improvements

Potential enhancements include role-based login, attendance tracking, timetable management, reporting dashboards, and additional export formats.
