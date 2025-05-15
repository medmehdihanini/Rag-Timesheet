# Task Suggestion RAG System

This project implements a Retrieval-Augmented Generation (RAG) system that suggests tasks based on project descriptions. It uses a combination of embedding models, vector search, and generative AI to provide contextually relevant task suggestions.

## Architecture

The system has the following components:

1. **Database Layer**: SQLAlchemy models mapping to MySQL tables (Project, ProjectProfile, Task)
2. **Embedding Layer**: Uses sentence-transformers/all-MiniLM-L6-v2 to embed project descriptions
3. **Storage Layer**: Elasticsearch for storing and retrieving vector embeddings
4. **Generation Layer**: T5-flan-base model for generating task suggestions
5. **API Layer**: FastAPI endpoints for interacting with the system

## Flow

1. Project descriptions and tasks are loaded from MySQL database
2. Descriptions are embedded using sentence-transformers
3. Embeddings and task information are stored in Elasticsearch
4. When a new project description is provided:
   - It is cleaned, preprocessed, and embedded using the same model
   - Similar project descriptions are retrieved from Elasticsearch using vector or hybrid search
   - The context (similar projects and their tasks) is sent to T5-flan-base
   - The model generates task suggestions based on the project description and retrieved context

## Setup and Installation

### Prerequisites

- Python 3.8+
- MySQL database with timesheet data
- Elasticsearch 7.x+

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env` and update the configuration:
   ```
   cp .env.example .env
   # Edit .env with your database and Elasticsearch credentials
   ```

### Initial Setup

1. Initialize Elasticsearch index:
   ```
   python init_elasticsearch.py
   ```

2. Load data from MySQL to Elasticsearch:
   ```
   # Standard loading
   python load_data.py
   
   # Parallel loading (faster)
   python load_data.py --parallel --workers 4
   ```

### Running the API

Start the FastAPI application:

```
uvicorn main:app --reload
```

Or use the provided utility script:

```
python run.py --start-api
```

The API will be available at http://127.0.0.1:8000

## API Endpoints

### GET /

Root endpoint to check if the API is running.

### GET /api/status

Get system status, including Elasticsearch statistics.

**Response:**
```json
{
  "status": "ok",
  "elasticsearch": {
    "available": true,
    "doc_count": 42,
    "index_size_bytes": 1234567,
    "index_name": "projects_embeddings"
  },
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "generation_model": "google/flan-t5-base"
}
```

### POST /api/suggest-tasks

Suggests tasks based on a project description using RAG.

**Request:**
```json
{
  "project_description": "Build a web application for timesheet management with user authentication",
  "num_suggestions": 3,
  "use_hybrid_search": true
}
```

**Response:**
```json
{
  "suggestions": [
    {"task_text": "Implement user authentication system"},
    {"task_text": "Create timesheet entry form with date and hour tracking"},
    {"task_text": "Build reporting dashboard for timesheet data"}
  ],
  "similar_projects": [
    {
      "project_id": "1",
      "project_name": "Timesheet Management System",
      "description": "A web-based timesheet management application",
      "tasks": [
        {"task_id": "1", "task_text": "Design database schema"}
      ],
      "score": 0.92
    }
  ],
  "processing_time": 1.234
}
```

### POST /api/reload-data

Admin endpoint to reload data from MySQL to Elasticsearch. This is useful when the database has been updated.

**Response:**
```json
{
  "message": "Data reload started in background",
  "status": "success"
}
```

## How It Works

### Database Structure

The system works with three main tables:
- `_project`: Contains project information including description
- `project_profile`: Links projects and profiles
- `_task`: Contains tasks with text descriptions

The relationship between these tables is:

```
Project (1) --< ProjectProfile (*)--< Task (*)
```

When a project description is provided, the system:
1. Retrieves project profiles associated with the project
2. For each profile, retrieves associated tasks
3. Uses these tasks as examples for generating new task suggestions

### RAG Process

1. **Retrieval**: 
   - Project description is embedded and used to search for similar descriptions in Elasticsearch
   - Similar projects and their associated tasks are retrieved

2. **Augmentation**:
   - The input description and retrieved similar projects/tasks are combined as context

3. **Generation**:
   - The T5-flan-base model uses this context to generate relevant task suggestions
   - Results are filtered and deduplicated for quality

### Search Methods

The system supports two search methods:

1. **Vector Search**: Uses pure vector similarity to find matching projects
   - Fast and works well for semantic matching
   - May miss lexical matches (exact word matches)

2. **Hybrid Search**: Combines vector search with text-based search
   - More comprehensive matching
   - Slightly slower but often yields better results

## Advanced Features

### Parallel Data Loading

For faster data loading, the system supports parallel processing:

```
python load_data.py --parallel --workers 4
```

This uses multiple threads to generate embeddings and load data more efficiently.

### Text Preprocessing

The system includes robust text preprocessing:
- Cleaning and normalizing text
- Handling edge cases (empty descriptions, etc.)
- Extracting meaningful tasks from generated text

## Extending the System

### Adding More Models

You can modify the `embedding.py` and `task_generator.py` files to use different models:

- For embeddings: Replace "sentence-transformers/all-MiniLM-L6-v2" with another sentence-transformer model
- For generation: Replace "google/flan-t5-base" with another text generation model

### Customizing Elasticsearch

You can modify the `elastic_search.py` file to adjust the vector search parameters or change the index structure.

### Adding New Features

Some ideas for extending the system:
- Add task prioritization
- Implement task time estimation
- Add support for task dependencies
- Create a web UI for easier interaction

## Troubleshooting

### Common Issues

1. **Connection issues with MySQL**:
   - Verify the DATABASE_URL in the .env file
   - Make sure the MySQL server is running and accessible

2. **Connection issues with Elasticsearch**:
   - Verify the ELASTICSEARCH_HOST and ELASTICSEARCH_PORT in the .env file
   - Make sure Elasticsearch is running and accessible

3. **Out of memory errors**:
   - The embedding and generation models require significant memory
   - Consider using smaller models or increasing the available memory

4. **Slow performance**:
   - Use parallel data loading
   - Consider using a more efficient embedding model
   - Optimize Elasticsearch settings

## License

This project is licensed under the MIT License - see the LICENSE file for details.
