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

class QueryValidationRequest(BaseModel):
    text: str = Field(..., description="Text to validate for query quality")

class QueryValidationResponse(BaseModel):
    is_coherent: bool = Field(..., description="Whether the query is coherent")
    relevance_score: float = Field(..., description="Relevance score (0.0 to 1.0)")
    confidence_level: str = Field(..., description="Confidence level")
    should_process: bool = Field(..., description="Whether the query should be processed")
    enhancement_applied: bool = Field(..., description="Whether enhancement was applied")
    recommendations: List[str] = Field(..., description="Recommendations for improving the query")

class SystemAnalytics(BaseModel):
    status: str = Field(..., description="System status")
    elasticsearch: Dict[str, Any] = Field(..., description="Elasticsearch statistics")
    embedding_model: Dict[str, Any] = Field(..., description="Embedding model information")
    generation_model: Dict[str, Any] = Field(..., description="Generation model information")
    features: Dict[str, bool] = Field(..., description="Available system features")

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
    Suggest tasks based on a project description using enhanced RAG with quality control
    """
    start_time = time.time()
    
    try:
        # Step 1: Validate and enhance the query
        enhanced_description, query_metadata = embedding_generator.validate_and_enhance_query(
            request.project_description
        )
        
        logger.info(f"Query validation - Coherent: {query_metadata['is_coherent']}, "
                   f"Relevance: {query_metadata['relevance_score']:.3f}, "
                   f"Should process: {query_metadata['should_process']}")
          # Step 2: Handle low-quality or irrelevant queries
        if not query_metadata['should_process']:
            processing_time = time.time() - start_time
            
            # Return single appropriate response for poor quality input
            fallback_suggestions = [
                TaskSuggestion(task_text="I'm not sure what specific tasks would be appropriate for this input. Could you please provide a clearer project description related to software development, web applications, or other technical projects?")
            ]
            
            return TaskSuggestionResponse(
                suggestions=fallback_suggestions,
                similar_tasks=[],
                processing_time=processing_time
            )
        
        # Step 3: Clean and preprocess the enhanced description
        cleaned_description = preprocess_project_description(enhanced_description)
        
        # Step 4: Generate embedding for the input description
        query_embedding = embedding_generator.generate_embedding(cleaned_description)
        
        # Step 5: Search for similar tasks with improved filtering
        search_kwargs = {
            "top_k": 8,  # Get more candidates for better filtering
            "min_score": 0.1  # Basic relevance threshold
        }
        
        if request.use_hybrid_search:
            similar_tasks = es_client.hybrid_search(
                query_text=cleaned_description,
                query_embedding=query_embedding,
                **search_kwargs
            )
        else:
            similar_tasks = es_client.vector_search(
                query_embedding, 
                **search_kwargs
            )
        
        logger.info(f"Search returned {len(similar_tasks)} similar tasks")
        
        # Step 6: Apply additional similarity filtering
        filtered_tasks = embedding_generator.filter_results_by_similarity(
            similar_tasks, 
            min_threshold=0.2  # Higher threshold for final results
        )
        
        logger.info(f"After filtering: {len(filtered_tasks)} relevant tasks")
        
        # Step 7: Calculate overall confidence in results
        result_confidence = embedding_generator.calculate_result_confidence(
            filtered_tasks, 
            query_metadata
        )
        
        logger.info(f"Result confidence: {result_confidence}")
        
        # Step 8: Group tasks by project for better context organization
        projects_with_tasks = {}
        for task in filtered_tasks[:5]:  # Limit to top 5 most relevant
            project_id = task.get("project_id", "unknown")
            if project_id not in projects_with_tasks:
                projects_with_tasks[project_id] = {
                    "project_id": project_id,
                    "project_name": task.get("project_name", ""),
                    "project_description": task.get("project_description", ""),
                    "tasks": [],
                    "score": task.get("score", 0.0)
                }
            
            projects_with_tasks[project_id]["tasks"].append({
                "task_id": task["task_id"],
                "task_text": task["task_text"]
            })
        
        similar_projects = list(projects_with_tasks.values())
        
        # Step 9: Generate task suggestions with enhanced quality control
        suggested_tasks = task_generator.generate_tasks(
            project_description=cleaned_description,
            similar_projects=similar_projects,
            num_return_sequences=min(request.num_suggestions, 3),
            query_metadata=query_metadata
        )
        
        # Step 10: Format the response
        suggestions = [TaskSuggestion(task_text=task) for task in suggested_tasks]
        
        processed_tasks = [
            SimilarTask(
                task_id=t["task_id"],
                task_text=t["task_text"],
                project_id=t.get("project_id", ""),
                project_name=t.get("project_name", ""),
                project_description=t.get("project_description", ""),
                score=t.get("normalized_score", t.get("score", 0.0))
            ) for t in filtered_tasks
        ]
        
        processing_time = time.time() - start_time
        
        logger.info(f"Task suggestion completed in {processing_time:.3f}s with {result_confidence} confidence")
        
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
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
        from simple_load_tasks import load_tasks_to_elasticsearch
        
        # Run in background to avoid blocking the response
        background_tasks.add_task(load_tasks_to_elasticsearch)
        
        return {"message": "Task data reload started in background", "status": "success"}
    except Exception as e:
        logger.error(f"Error starting data reload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting data reload: {str(e)}")

@app.post("/api/validate-query", response_model=QueryValidationResponse)
async def validate_query(request: QueryValidationRequest):
    """
    Validate query quality and get recommendations for improvement
    """
    try:
        # Validate and enhance the query
        enhanced_text, metadata = embedding_generator.validate_and_enhance_query(request.text)
        
        # Generate recommendations based on the validation results
        recommendations = []
        
        if not metadata['is_coherent']:
            recommendations.append("Try to write a clearer, more structured description")
            recommendations.append("Use complete sentences and avoid random characters")
        
        if metadata['relevance_score'] < 0.3:
            recommendations.append("Include more project-specific terms (e.g., development, implementation, design)")
            recommendations.append("Describe what type of project or system you're working on")
        
        if metadata['relevance_score'] < 0.5:
            recommendations.append("Add technical details about the technologies or frameworks involved")
            recommendations.append("Mention specific deliverables or objectives")
        
        if len(request.text.split()) < 5:
            recommendations.append("Provide more detailed description (aim for at least 10-15 words)")
        
        if not recommendations:
            recommendations.append("Your query looks good! It should produce relevant task suggestions.")
        
        return QueryValidationResponse(
            is_coherent=metadata['is_coherent'],
            relevance_score=metadata['relevance_score'],
            confidence_level=metadata['confidence_level'],
            should_process=metadata['should_process'],
            enhancement_applied=metadata['enhancement_applied'],
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error validating query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating query: {str(e)}")

@app.get("/api/analytics", response_model=SystemAnalytics)
async def get_analytics():
    """
    Get system analytics and performance metrics
    """
    try:
        # Get Elasticsearch statistics
        es_stats = es_client.get_stats() if hasattr(es_client, 'get_stats') else {"available": False}
        
        # Get embedding model info
        embedding_info = {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dimensions": 384,
            "similarity_threshold": getattr(embedding_generator, 'similarity_threshold', 0.3)
        }
        
        # Get generation model info
        generation_info = {
            "model_name": "google/flan-t5-base",
            "confidence_levels": ["high", "medium", "low", "very_low"]
        }
        
        return SystemAnalytics(
            status="ok",
            elasticsearch=es_stats,
            embedding_model=embedding_info,
            generation_model=generation_info,
            features={
                "query_validation": True,
                "similarity_filtering": True,
                "confidence_scoring": True,
                "hybrid_search": True,
                "fallback_responses": True
            }
        )
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error getting system analytics: {str(e)}"
            }
        )

@app.get("/api/status")
async def get_status():
    """
    Get basic system status
    """
    try:
        # Check if services are running
        es_available = getattr(es_client, 'es_available', False)
        
        return {
            "status": "ok",
            "services": {
                "elasticsearch": es_available,
                "embedding_generator": True,
                "task_generator": True
            },
            "version": "1.0.0"
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
