"""
Utility functions for the Task Suggestion RAG System
"""
import re
import logging
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean and preprocess text for embedding and generation"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters that might not be useful for embeddings
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    
    return text

def preprocess_project_description(description: str) -> str:
    """Preprocess project description for better embedding and retrieval"""
    # Clean the text first
    clean_description = clean_text(description)
    
    # If description is too short, return as is
    if len(clean_description.split()) < 10:
        return clean_description
    
    # For longer descriptions, we could potentially extract key phrases or summarize
    # This is a simple implementation - just truncate very long descriptions
    words = clean_description.split()
    if len(words) > 200:
        clean_description = ' '.join(words[:200])
        
    return clean_description

def format_tasks_for_context(tasks: List[Dict[str, Any]]) -> str:
    """Format tasks into a structured text for better context"""
    if not tasks:
        return "No related tasks available."
    
    task_texts = []
    for task in tasks:
        if task.get("task_text"):
            task_texts.append(f"- {task['task_text']}")
    
    if not task_texts:
        return "No task descriptions available."
    
    return "\n".join(task_texts)

def extract_tasks_from_generation(generated_text: str) -> List[str]:
    """Extract individual tasks from generated text"""
    # Remove any prefix like "Here are some tasks:"
    cleaned_text = re.sub(r'^.*?(?=\s*-|\s*\d+\.|\n)', '', generated_text, flags=re.DOTALL)
    
    # Split by common list markers
    tasks = []
    
    # Try to match numbered or bulleted lists
    patterns = [
        r'\d+\.\s*(.*?)(?=\n\d+\.|\n-|\Z)',  # Numbered lists: "1. Task"
        r'-\s*(.*?)(?=\n-|\n\d+\.|\Z)',      # Dash bullets: "- Task"
        r'•\s*(.*?)(?=\n•|\n-|\n\d+\.|\Z)',  # Bullet points: "• Task"
        r'\*\s*(.*?)(?=\n\*|\n-|\n\d+\.|\Z)' # Asterisk bullets: "* Task"
    ]
    
    found = False
    for pattern in patterns:
        matches = re.finditer(pattern, cleaned_text, re.DOTALL)
        for match in matches:
            task = match.group(1).strip()
            if task and len(task) > 3:  # Minimum task length
                tasks.append(task)
                found = True
    
    # If no structured lists are found, split by newlines
    if not found:
        lines = cleaned_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:  # Minimum line length
                tasks.append(line)
    
    # Remove duplicates while preserving order
    unique_tasks = []
    for task in tasks:
        if task not in unique_tasks:
            unique_tasks.append(task)
    
    return unique_tasks

def validate_database_connection(db_url: str) -> bool:
    """Validate database connection"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.exc import SQLAlchemyError
        
        engine = create_engine(db_url)
        connection = engine.connect()
        connection.close()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        return False
    except ImportError:
        logger.error("SQLAlchemy not installed")
        return False

def validate_elasticsearch_connection(host: str, port: str) -> bool:
    """Validate Elasticsearch connection"""
    try:
        from elasticsearch import Elasticsearch
        
        es = Elasticsearch([f"http://{host}:{port}"])
        if es.ping():
            return True
        else:
            logger.error("Could not connect to Elasticsearch")
            return False
    except Exception as e:
        logger.error(f"Elasticsearch connection error: {e}")
        return False
