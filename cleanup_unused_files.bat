@echo off
REM Cleanup script for removing unused, empty, and meaningless files
echo Starting cleanup of unused files in Rag-Timesheet project...

REM Delete empty __init__.py files that serve no purpose
echo Removing empty __init__.py files...
if exist "src\__init__.py" (
    echo   - Removing src\__init__.py
    del /f /q "src\__init__.py"
)
if exist "src\api\__init__.py" (
    echo   - Removing src\api\__init__.py
    del /f /q "src\api\__init__.py"
)
if exist "src\data\__init__.py" (
    echo   - Removing src\data\__init__.py
    del /f /q "src\data\__init__.py"
)
if exist "src\data\database\__init__.py" (
    echo   - Removing src\data\database\__init__.py
    del /f /q "src\data\database\__init__.py"
)
if exist "src\data\elasticsearch\__init__.py" (
    echo   - Removing src\data\elasticsearch\__init__.py
    del /f /q "src\data\elasticsearch\__init__.py"
)
if exist "src\models\__init__.py" (
    echo   - Removing src\models\__init__.py
    del /f /q "src\models\__init__.py"
)
if exist "src\models\embedding\__init__.py" (
    echo   - Removing src\models\embedding\__init__.py
    del /f /q "src\models\embedding\__init__.py"
)
if exist "src\models\generation\__init__.py" (
    echo   - Removing src\models\generation\__init__.py
    del /f /q "src\models\generation\__init__.py"
)
if exist "src\utils\__init__.py" (
    echo   - Removing src\utils\__init__.py
    del /f /q "src\utils\__init__.py"
)
if exist "tests\__init__.py" (
    echo   - Removing tests\__init__.py
    del /f /q "tests\__init__.py"
)

REM Delete unused scripts that are not referenced anywhere
echo Removing unused scripts...
if exist "scripts\run.py" (
    echo   - Removing scripts\run.py (redundant entry point)
    del /f /q "scripts\run.py"
)
if exist "scripts\verify_system.py" (
    echo   - Removing scripts\verify_system.py (not used in main flow)
    del /f /q "scripts\verify_system.py"
)
if exist "make_executable.sh" (
    echo   - Removing make_executable.sh (not necessary for core functionality)
    del /f /q "make_executable.sh"
)

REM Clean up any __pycache__ directories (same as clean.bat but integrated)
echo Cleaning up Python cache files...
FOR /D /R . %%d IN (__pycache__) DO (
    IF EXIST "%%d" (
        echo   - Removing: %%d
        RD /S /Q "%%d"
    )
)

REM Delete .pyc files
FOR /R . %%f IN (*.pyc) DO (
    echo   - Removing: %%f
    DEL /F /Q "%%f"
)

echo.
echo ===================================================
echo Cleanup completed successfully!
echo.
echo Files removed:
echo   - Empty __init__.py files (10 files)
echo   - Unused scripts: run.py, verify_system.py, make_executable.sh
echo   - Python cache files (__pycache__ directories and .pyc files)
echo.
echo Files preserved:
echo   - All documentation files (valuable for developers)
echo   - All configuration and setup files
echo   - All test files
echo   - All main application code
echo   - Docker files
echo   - Build/utility scripts (clean, setup, run_tests)
echo   - download_models.py (used in Dockerfile)
echo ===================================================
