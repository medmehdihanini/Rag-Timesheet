@echo off
REM Clean script for Rag-Timesheet project
echo Cleaning up cached Python files...

REM Delete __pycache__ directories
FOR /D /R . %%d IN (__pycache__) DO (
    IF EXIST "%%d" (
        echo Removing: %%d
        RD /S /Q "%%d"
    )
)

REM Delete .pyc files
FOR /R . %%f IN (*.pyc) DO (
    echo Removing: %%f
    DEL /F /Q "%%f"
)

echo.
echo Cleanup complete!
