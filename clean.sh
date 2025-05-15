#!/bin/bash
# Clean script for Rag-Timesheet project
echo "Cleaning up cached Python files..."

# Find and delete __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +

# Find and delete .pyc files
find . -type f -name "*.pyc" -delete

# Find and delete .pytest_cache
find . -type d -name ".pytest_cache" -exec rm -rf {} +

echo ""
echo "Cleanup complete!"
