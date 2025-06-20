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
    # Run without reload to avoid async cancellation issues during development
    try:
        uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=False)
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
