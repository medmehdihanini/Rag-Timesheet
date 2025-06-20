"""
Utility functions for the Task Suggestion RAG System
"""
import re
import logging
from typing import List, Dict, Any, Tuple

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

def assess_text_quality(text: str) -> Dict[str, Any]:
    """Assess the quality and characteristics of input text"""
    if not text:
        return {
            "length": 0,
            "word_count": 0,
            "sentence_count": 0,
            "avg_word_length": 0.0,
            "has_technical_terms": False,
            "readability_score": 0.0,
            "quality_level": "very_poor"
        }
    
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Calculate basic metrics
    word_count = len(words)
    sentence_count = len(sentences)
    avg_word_length = sum(len(word) for word in words) / word_count if words else 0
    
    # Check for technical/project-related terms
    technical_terms = [
        'api', 'database', 'frontend', 'backend', 'ui', 'ux', 'framework',
        'algorithm', 'architecture', 'deployment', 'integration', 'testing',
        'development', 'implementation', 'design', 'analysis', 'planning'
    ]
    
    has_technical_terms = any(term in text.lower() for term in technical_terms)
    
    # Simple readability assessment
    if word_count == 0:
        readability_score = 0.0
    else:
        # Basic readability based on sentence and word length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else word_count
        readability_score = min(1.0, (avg_sentence_length / 20.0) + (avg_word_length / 10.0))
    
    # Determine quality level
    if word_count >= 20 and sentence_count >= 2 and has_technical_terms:
        quality_level = "excellent"
    elif word_count >= 10 and sentence_count >= 1:
        quality_level = "good"
    elif word_count >= 5:
        quality_level = "fair"
    elif word_count >= 2:
        quality_level = "poor"
    else:
        quality_level = "very_poor"
    
    return {
        "length": len(text),
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_word_length": avg_word_length,
        "has_technical_terms": has_technical_terms,
        "readability_score": readability_score,
        "quality_level": quality_level
    }

def format_tasks_for_context(tasks: List[Dict[str, Any]]) -> str:
    """Format tasks into a structured text for better context"""
    if not tasks:
        return "No related tasks available."
    
    task_texts = []
    for i, task in enumerate(tasks[:10], 1):  # Limit to top 10 tasks
        if task.get("task_text"):
            # Clean and format task text
            task_text = clean_text(task["task_text"])
            if len(task_text) > 100:  # Truncate very long tasks
                task_text = task_text[:100] + "..."
            task_texts.append(f"{i}. {task_text}")
    
    if not task_texts:
        return "No task descriptions available."
    
    return "\n".join(task_texts)

def extract_tasks_from_generation(generated_text: str) -> List[str]:
    """Extract individual tasks from generated text with improved parsing"""
    if not generated_text:
        return []
    
    # Remove any prefix like "Here are some tasks:" or model artifacts
    cleaned_text = re.sub(r'^.*?(?=\s*[-•\*]|\s*\d+\.|\n)', '', generated_text, flags=re.DOTALL)
    
    # Also remove common model prefixes
    prefixes_to_remove = [
        r'here are \d* tasks?:?',
        r'based on.*?:',
        r'the following tasks?:?',
        r'suggested tasks?:?',
        r'project tasks?:?'
    ]
    
    for prefix in prefixes_to_remove:
        cleaned_text = re.sub(prefix, '', cleaned_text, flags=re.IGNORECASE)
    
    cleaned_text = cleaned_text.strip()
    
    # Split by common list markers with improved patterns
    tasks = []
    
    # Try to match numbered or bulleted lists
    patterns = [
        r'(\d+)\.\s*([^.\n]+?)(?=\n\d+\.|\n[-•\*]|\Z)',  # Numbered lists: "1. Task"
        r'[-•\*]\s*([^.\n]+?)(?=\n[-•\*]|\n\d+\.|\Z)',   # Bullet lists
        r'^([^.\n]+?)(?=\n[^.\n]+|\Z)'                    # Simple line-based splitting
    ]
    
    found = False
    for pattern in patterns:
        matches = re.finditer(pattern, cleaned_text, re.MULTILINE | re.DOTALL)
        for match in matches:
            if len(match.groups()) > 1:
                task = match.group(2).strip()  # For numbered lists
            else:
                task = match.group(1).strip()  # For other patterns
            
            # Clean up the task
            task = re.sub(r'[^\w\s.,;:!?()-]', '', task)
            task = re.sub(r'\s+', ' ', task).strip()
            
            if task and len(task) > 5 and len(task) < 200:  # Reasonable task length
                tasks.append(task)
                found = True
    
    # If no structured lists are found, split by newlines and clean
    if not found:
        lines = cleaned_text.split('\n')
        for line in lines:
            line = line.strip()
            # Remove numbering and bullet points
            line = re.sub(r'^\d+\.\s*', '', line)
            line = re.sub(r'^[-•\*]\s*', '', line)
            line = re.sub(r'[^\w\s.,;:!?()-]', '', line)
            line = re.sub(r'\s+', ' ', line).strip()
            
            if line and len(line) > 5 and len(line) < 200:
                tasks.append(line)
    
    # Remove duplicates while preserving order and filter quality
    unique_tasks = []
    for task in tasks:
        # Additional quality checks
        words = task.split()
        if (task not in unique_tasks and 
            len(words) >= 3 and  # At least 3 words
            len(words) <= 30 and  # Not too long
            not task.lower().startswith(('the', 'a', 'an', 'and', 'or', 'but'))):  # Not starting with articles/conjunctions
            unique_tasks.append(task)
    
    return unique_tasks

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts using simple metrics"""
    if not text1 or not text2:
        return 0.0
    
    # Tokenize and clean
    words1 = set(clean_text(text1.lower()).split())
    words2 = set(clean_text(text2.lower()).split())
    
    # Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def validate_task_relevance(task_text: str, project_description: str) -> Tuple[bool, float]:
    """Validate if a generated task is relevant to the project description"""
    if not task_text or not project_description:
        return False, 0.0
    
    # Calculate semantic similarity
    similarity = calculate_semantic_similarity(task_text, project_description)
    
    # Check for project-related keywords in the task
    project_keywords = extract_keywords_from_text(project_description)
    task_keywords = extract_keywords_from_text(task_text)
    
    keyword_overlap = len(project_keywords.intersection(task_keywords))
    keyword_relevance = keyword_overlap / max(len(project_keywords), 1)
    
    # Combined relevance score
    combined_score = (similarity * 0.6) + (keyword_relevance * 0.4)
    
    # Task is relevant if combined score is above threshold
    is_relevant = combined_score >= 0.2  # Adjust threshold as needed
    
    return is_relevant, combined_score

def extract_keywords_from_text(text: str) -> set:
    """Extract meaningful keywords from text"""
    if not text:
        return set()
    
    # Remove stop words and extract meaningful terms
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
    
    words = clean_text(text.lower()).split()
    keywords = {word for word in words if len(word) > 2 and word not in stop_words}
    
    return keywords

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
