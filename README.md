# Rag-Timesheet: Task Suggestion System

This project implements a Retrieval-Augmented Generation (RAG) system that suggests tasks based on project descriptions.

## Overview

Rag-Timesheet uses Elasticsearch for vector storage, sentence transformers for embeddings, and T5 model for task generation. The system helps with suggesting tasks for new projects based on historical task data.

## Project Structure

The project follows a structured approach with separate directories for:
- `src`: Source code organized by component (API, data, models, utils)
- `scripts`: Utility scripts for initialization and operations
- `docker`: Docker configuration files
- `docs`: Detailed documentation
- `tests`: Test files
- `config`: Configuration templates

## Machine Learning Models

The system uses two main machine learning models:

1. **Sentence Transformer (all-MiniLM-L6-v2)**
   - Used for generating embeddings from text
   - Converts tasks and project descriptions into 384-dimensional vectors
   - Located in `src/models/embedding/generator.py`

2. **Flan-T5-base**
   - Text generation model that creates task suggestions
   - Fine-tuned version of Google's T5 model
   - Located in `src/models/generation/task_generator.py`

You can pre-download these models using:
```bash
python -m scripts.download_models
```

## Quick Start

1. Configure environment variables:
   ```
   cp config/.env.example .env
   # Edit .env with your settings
   ```

2. Initialize Elasticsearch:
   ```
   python scripts/init_elasticsearch.py
   ```

3. Load data:
   ```
   python scripts/simple_load_tasks.py
   ```

4. Start the API:
   ```
   python main.py
   ```

The API will be available at http://localhost:8000.

## Documentation

For detailed documentation, please refer to the files in the `docs` directory:
- Architecture overview
- Implementation details
- API documentation

## Running with Docker

```bash
cd docker
docker-compose up -d
```
