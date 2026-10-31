# Student Management System

A desktop student management application planned with Python 3.12, Tkinter/ttk,
MySQL Server, and `mysql-connector-python`.

## Project status

The project structure, configuration loader, draft database schema, database
repositories, backend services, and initial Tkinter interface are implemented.
The schema is a reviewable draft and has not been run against a MySQL server.
No database has been created or changed by the application work so far.

## Requirements

- Python 3.12
- MySQL Server (to be configured in a later stage)
- MySQL Workbench (for database administration)

## Local setup

From the project directory, create and activate a virtual environment, then
install the listed dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set the connection values for a dedicated
application database account. Keep `.env` private; it is excluded by
`.gitignore`. Do not use or change the MySQL root password for the application.

Database configuration is read from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`,
and `DB_PASSWORD`. Environment variables take precedence over values in `.env`.

## Launch

After dependencies and database settings are configured, launch the application
from the project directory with:

```powershell
python -m frontend.app
```
