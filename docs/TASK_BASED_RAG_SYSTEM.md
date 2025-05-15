# Task-Based RAG System Documentation

## Overview

This document outlines the updated Retrieval-Augmented Generation (RAG) system that directly embeds tasks instead of project descriptions. The new approach simplifies the architecture and improves relevance by retrieving tasks based on semantic similarity to the input query.

## Architecture Changes

### Previous Architecture
- Embedded project descriptions
- Retrieved similar projects
- Used projects' tasks to inform the generator

### New Architecture
- Directly embeds individual tasks
- Stores project information as metadata with each task
- Retrieves semantically similar tasks
- Groups retrieved tasks by project for context

## Major Components

### 1. Elasticsearch Integration (`elastic_search.py`)
- Index name: `tasks_embeddings` (configured in `.env`)
- Document structure:
  - `task_id`: Unique identifier for the task
  - `task_text`: The task description text
  - `embedding`: Dense vector embedding of task text
  - `project_id`: ID of related project (metadata)
  - `project_name`: Name of related project (metadata)
  - `project_description`: Description of related project (metadata)

- Key Methods:
  - `index_task()`: Index a single task with embeddings
  - `batch_index_tasks()`: Index multiple tasks in batch
  - `vector_search()`: Search by vector similarity
  - `hybrid_search()`: Combined vector and text search

### 2. Data Processing (`load_data.py`)
- `process_task()`: Process a single task for indexing
- `load_data_to_elasticsearch()`: Load all tasks with embeddings
- `parallel_load_data_to_elasticsearch()`: Parallel processing for faster loading

### 3. API Endpoints (`main.py`)
- `/api/suggest-tasks`: Find similar tasks and generate suggestions
- `/api/reload-data`: Reload task data to Elasticsearch
- `/api/status`: Get system status

### 4. Task Generation (`task_generator.py`)
- Uses retrieved similar tasks to generate relevant task suggestions
- Groups tasks by project for better context

## Data Flow

1. User inputs a project description
2. System generates embedding for the description
3. Elasticsearch retrieves semantically similar tasks
4. Tasks are grouped by their parent projects
5. Task generator uses retrieved tasks as context for generating new task suggestions
6. Generated tasks are returned to the user

## Testing

Use `test_task_embedding.py` to test:
- Elasticsearch connection
- Embedding generation
- Task indexing and retrieval
- Search functionality (both vector and hybrid)

## Running the System

Use `run_system.py` to:
- Initialize the system: `python run_system.py --init`
- Start the API server: `python run_system.py --run`
- Do both: `python run_system.py --init --run`

## Configuration

Environment variables (.env):
- `ELASTICSEARCH_HOST`: Elasticsearch host
- `ELASTICSEARCH_PORT`: Elasticsearch port
- `ELASTICSEARCH_USER`: Elasticsearch username
- `ELASTICSEARCH_PASSWORD`: Elasticsearch password
- `ELASTICSEARCH_USE_SSL`: Whether to use SSL
- `ELASTICSEARCH_CERT_PATH`: Path to SSL certificate
- `ELASTICSEARCH_INDEX`: Index name (tasks_embeddings)
- `DATABASE_URL`: MySQL database connection string

## Benefits of the New Approach

1. **Simplified Architecture**: Direct task retrieval eliminates intermediate project lookup
2. **Improved Relevance**: Finding tasks semantically similar to the query
3. **Better Context**: Tasks are grouped by project for coherent context
4. **More Efficient**: Each task becomes a searchable entity with its own embedding

## Considerations

1. **Index Size**: Task-level indexing may result in a larger index compared to project-level
2. **Redundancy**: Project metadata is duplicated across all tasks from the same project
3. **Scoring**: Hybrid search balances between semantic similarity and text matching
