#!/bin/bash
# Cleanup script for removing unused, empty, and meaningless files
echo "Starting cleanup of unused files in Rag-Timesheet project..."

# Delete empty __init__.py files that serve no purpose
echo "Removing empty __init__.py files..."
files_to_remove=(
    "src/__init__.py"
    "src/api/__init__.py"
    "src/data/__init__.py"
    "src/data/database/__init__.py"
    "src/data/elasticsearch/__init__.py"
    "src/models/__init__.py"
    "src/models/embedding/__init__.py"
    "src/models/generation/__init__.py"
    "src/utils/__init__.py"
    "tests/__init__.py"
)

for file in "${files_to_remove[@]}"; do
    if [ -f "$file" ]; then
        echo "  - Removing $file"
        rm -f "$file"
    fi
done

# Delete unused scripts that are not referenced anywhere
echo "Removing unused scripts..."
unused_scripts=(
    "scripts/run.py"
    "scripts/verify_system.py"
    "make_executable.sh"
)

for script in "${unused_scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "  - Removing $script"
        rm -f "$script"
    fi
done

# Clean up any __pycache__ directories (same as clean.sh but integrated)
echo "Cleaning up Python cache files..."

# Find and delete __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Find and delete .pyc files
find . -type f -name "*.pyc" -delete 2>/dev/null

# Find and delete .pytest_cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

echo ""
echo "==================================================="
echo "Cleanup completed successfully!"
echo ""
echo "Files removed:"
echo "  - Empty __init__.py files (10 files)"
echo "  - Unused scripts: run.py, verify_system.py, make_executable.sh"
echo "  - Python cache files (__pycache__ directories and .pyc files)"
echo ""
echo "Files preserved:"
echo "  - All documentation files (valuable for developers)"
echo "  - All configuration and setup files"
echo "  - All test files"
echo "  - All main application code"
echo "  - Docker files"
echo "  - Build/utility scripts (clean, setup, run_tests)"
echo "  - download_models.py (used in Dockerfile)"
echo "==================================================="
