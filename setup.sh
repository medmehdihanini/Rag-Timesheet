#!/bin/bash
# Setup script for Rag-Timesheet project on Linux/Unix/Mac
echo "Setting up Rag-Timesheet development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -e .

# Check if .env file exists, create from example if not
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp config/.env.example .env
    echo "Please update your .env file with appropriate settings."
else
    echo ".env file already exists."
fi

# Initialize Elasticsearch
echo "Initializing Elasticsearch..."
python -m scripts.init_elasticsearch

echo -e "\nSetup complete!"
echo "To activate the environment: source .venv/bin/activate"
echo "To run the API: python main.py"
echo "Access the API at http://localhost:8000"
