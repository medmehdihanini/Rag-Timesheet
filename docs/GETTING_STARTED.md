# Getting Started with Rag-Timesheet

This guide will help you quickly get started with the Rag-Timesheet project.

## Prerequisites

- Python 3.8+
- MySQL database
- Elasticsearch 7.x+
- Git

## Setup Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Rag-Timesheet
```

### 2. Set Up Development Environment

#### Windows

```bash
# Run the setup script
setup.bat
```

#### Unix/Linux/Mac

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Create .env file
cp config/.env.example .env
```

### 3. Configure Environment

Edit the `.env` file with your database and Elasticsearch settings.

### 4. Initialize Elasticsearch

```bash
python -m scripts.init_elasticsearch
```

### 5. Load Test Data

```bash
python -m scripts.simple_load_tasks
```

### 6. Run the Application

```bash
python main.py
```

The API will be available at [http://localhost:8000](http://localhost:8000)

## Project Structure

- `src/`: Main source code
  - `api/`: API endpoints
  - `data/`: Data access layer (database, Elasticsearch)
  - `models/`: ML models (embedding, generation)
  - `utils/`: Utility functions
- `scripts/`: Utility scripts
- `docker/`: Docker configuration
- `docs/`: Documentation
- `tests/`: Test files
- `config/`: Configuration templates

## Development Workflow

1. Activate your virtual environment
2. Make changes in the appropriate modules
3. Run the application with `python main.py`
4. Test your changes through the API or test HTTP files

## Running Tests

```bash
pytest
```

## Documentation

See the `docs/` directory for detailed documentation:
- [README.md](docs/README.md): Detailed project documentation
- [IMPLEMENTATION.md](docs/IMPLEMENTATION.md): Implementation details
- [TASK_BASED_RAG_SYSTEM.md](docs/TASK_BASED_RAG_SYSTEM.md): System architecture
