@echo off
echo Setting up Rag-Timesheet Project...

:: Create virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Using existing virtual environment...
)

call .venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install -e .

:: Check if .env file exists, create from example if not
if not exist .env (
    echo Creating .env file from template...
    copy config\.env.example .env
    echo Please update your .env file with appropriate settings.
) else (
    echo .env file already exists.
)

:: Initialize Elasticsearch
echo Initializing Elasticsearch...
python -m scripts.init_elasticsearch

echo Setup complete! Follow these steps to run the application:
echo 1. Make sure Elasticsearch is running
echo 2. Run the application with: python main.py
echo 3. Access the API at http://localhost:8000
