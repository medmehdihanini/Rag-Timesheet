"""
Main entry point for the Rag-Timesheet application
This script imports and runs the FastAPI app from src/api/app.py
"""
import os
import sys
import uvicorn

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

if __name__ == "__main__":
    # For reload to work properly, we need to pass the app as an import string
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
