#!/bin/bash
# Run tests for the Rag-Timesheet project
echo "Running tests for Rag-Timesheet..."

# Activate virtual environment
source .venv/bin/activate

# Set environment variables for testing
export PYTHONPATH=$(pwd)
export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200
export DATABASE_URL=mysql+pymysql://root:password@localhost/backup

# Run tests with pytest
echo ""
echo "Running unit tests..."
pytest tests/ -v

echo ""
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed."
fi

# Deactivate virtual environment
deactivate
