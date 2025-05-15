@echo off
REM Run tests for the Rag-Timesheet project
echo Running tests for Rag-Timesheet...

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set environment variables for testing
set PYTHONPATH=%CD%
set ELASTICSEARCH_HOST=localhost
set ELASTICSEARCH_PORT=9200
set DATABASE_URL=mysql+pymysql://root:password@localhost/backup

REM Run tests with pytest
echo.
echo Running unit tests...
pytest tests/ -v

echo.
if %errorlevel% equ 0 (
    echo All tests passed!
) else (
    echo Some tests failed.
)

REM Deactivate virtual environment
deactivate
