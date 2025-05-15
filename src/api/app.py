import time
import logging
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Import from new module locations
from src.models.embedding.generator import EmbeddingGenerator
from src.data.elasticsearch.client import ElasticSearchClient
from src.models.generation.task_generator import TaskGenerator
from src.utils.utils import clean_text, preprocess_project_description

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Task Suggestion RAG System", 
    description="A system that suggests tasks based on project descriptions using Retrieval Augmented Generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
logger.info("Initializing services...")
embedding_generator = EmbeddingGenerator()
es_client = ElasticSearchClient()
task_generator = TaskGenerator()

# Pydantic models
class TaskSuggestion(BaseModel):
    task_text: str = Field(..., description="The suggested task text")

class SimilarTask(BaseModel):
    task_id: str = Field(..., description="Task identifier")
    task_text: str = Field(..., description="The task text")
    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Name of the related project")
    project_description: str = Field(..., description="Project description")
    score: Optional[float] = Field(None, description="Similarity score")

class TaskSuggestionRequest(BaseModel):
    project_description: str = Field(..., description="The project description to generate task suggestions for")
    num_suggestions: Optional[int] = Field(3, description="Number of task suggestions to generate")
    use_hybrid_search: Optional[bool] = Field(False, description="Whether to use hybrid search (vector + text) or just vector search")
    
class TaskSuggestionResponse(BaseModel):
    suggestions: List[TaskSuggestion] = Field(..., description="The suggested tasks")
    similar_tasks: Optional[List[SimilarTask]] = Field(None, description="Similar tasks used for context")
    processing_time: float = Field(..., description="Processing time in seconds")

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    return {"message": "Task Suggestion RAG API is running", "version": "1.0.0"}

@app.post("/api/suggest-tasks", response_model=TaskSuggestionResponse)
async def suggest_tasks(request: TaskSuggestionRequest):
    """
    Suggest tasks based on a project description using RAG (Retrieval Augmented Generation)
    """
    start_time = time.time()
    
    try:
        # Clean and preprocess the input description
        cleaned_description = preprocess_project_description(request.project_description)
        
        # Generate embedding for the input description
        query_embedding = embedding_generator.generate_embedding(cleaned_description)
        
        # Search for similar tasks in Elasticsearch - using hybrid search if specified
        if request.use_hybrid_search:
            similar_tasks = es_client.hybrid_search(
                query_text=cleaned_description,
                query_embedding=query_embedding, 
                top_k=5
            )
        else:
            similar_tasks = es_client.vector_search(query_embedding, top_k=5)
            logger.info(f"Vector search returned {len(similar_tasks)} similar tasks")
        
        # Convert the task data for task generator format
        # Group tasks by project for better context organization
        projects_with_tasks = {}
        for task in similar_tasks:
            project_id = task["project_id"]
            if project_id not in projects_with_tasks:
                projects_with_tasks[project_id] = {
                    "project_id": project_id,
                    "project_name": task["project_name"],
                    "project_description": task["project_description"],
                    "tasks": [],
                    "score": task["score"]  # Use the highest task score for the project
                }
            
            projects_with_tasks[project_id]["tasks"].append({
                "task_id": task["task_id"],
                "task_text": task["task_text"]
            })
        
        # Convert dict to list for the task generator
        similar_projects = list(projects_with_tasks.values())
        
        # Generate task suggestions using T5 model with retrieved context
        suggested_tasks = task_generator.generate_tasks(
            project_description=cleaned_description,
            similar_projects=similar_projects,
            num_return_sequences=min(request.num_suggestions, 5)  # Limit to 5 max
        )
        
        # Format the response
        suggestions = [TaskSuggestion(task_text=task) for task in suggested_tasks]
        
        processed_tasks = [
            SimilarTask(
                task_id=t["task_id"],
                task_text=t["task_text"],
                project_id=t["project_id"],
                project_name=t["project_name"],
                project_description=t["project_description"],
                score=t["score"]
            ) for t in similar_tasks
        ]
        
        processing_time = time.time() - start_time
        
        return TaskSuggestionResponse(
            suggestions=suggestions,
            similar_tasks=processed_tasks,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error suggesting tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error suggesting tasks: {str(e)}")

@app.post("/api/reload-data")
async def reload_data(background_tasks: BackgroundTasks):
    """
    Reload all data from MySQL to Elasticsearch
    This is an admin endpoint to refresh the data
    """
    try:
        # Import here to avoid circular imports
        from simple_load_tasks import load_tasks_to_elasticsearch
        
        # Run in background to avoid blocking the response
        background_tasks.add_task(load_tasks_to_elasticsearch)
        
        return {"message": "Task data reload started in background", "status": "success"}
    except Exception as e:
        logger.error(f"Error starting data reload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting data reload: {str(e)}")

@app.get("/api/status")
async def get_status():
    """
    Get system status including Elasticsearch stats
    """
    try:
        # Check if services are running
        es_stats = es_client.get_stats() if hasattr(es_client, 'get_stats') else {"available": False}
        
        return {
            "status": "ok",
            "elasticsearch": es_stats,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "generation_model": "google/flan-t5-base"
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error getting system status: {str(e)}"
            }
        )

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

def start():
    """Entry point for the console script defined in setup.py"""
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()
