"""
Simplified script to load tasks directly from the database to Elasticsearch
Only uses the task table with no dependencies on other tables
"""
import time
import logging
from simple_database import get_all_tasks
from embedding import EmbeddingGenerator
from elastic_search import ElasticSearchClient
from utils import clean_text
from tqdm import tqdm
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_single_task(task, embedding_generator):
    """Process a single task for Elasticsearch indexing"""
    try:
        # Skip tasks without text
        if not task.text:
            logger.debug(f"Skipping task {task.id} - no text content")
            return None
        
        # Clean task text
        cleaned_task_text = clean_text(task.text)
        if not cleaned_task_text:
            logger.debug(f"Skipping task {task.id} - text cleaned to empty")
            return None
        
        # Generate embedding for task text
        embedding = embedding_generator.generate_embedding(cleaned_task_text)
        
        # Return task data for indexing - without any project information
        return {
            "task_id": str(task.id),
            "task_text": cleaned_task_text,
            "embedding": embedding
        }
    except Exception as e:
        logger.error(f"Error processing task {task.id}: {str(e)}")
        return None

def load_tasks_to_elasticsearch():
    """Load tasks directly from the database to Elasticsearch"""
    start_time = time.time()
    logger.info("Starting simplified task loading process")
    
    # Initialize services
    embedding_generator = EmbeddingGenerator()
    es_client = ElasticSearchClient()
    
    # Stats for tracking
    stats = {
        "total_tasks": 0,
        "processed_tasks": 0,
        "indexed_tasks": 0,
        "errors": 0
    }
    
    try:
        # Get tasks directly using our custom function - avoids SQLAlchemy ORM mapping issues
        tasks = get_all_tasks()
        logger.info(f"Loaded {len(tasks)} tasks from the database")
        
        stats["total_tasks"] = len(tasks)
        logger.info(f"Found {stats['total_tasks']} tasks in the database")
        
        if not tasks:
            logger.warning("No tasks found in database")
            return stats
        
        # Process and index tasks in batches
        batch_size = 20
        current_batch = []
        
        for task in tqdm(tasks, desc="Processing tasks"):
            # Process task
            task_data = process_single_task(task, embedding_generator)
            
            if task_data:
                current_batch.append(task_data)
                stats["processed_tasks"] += 1
                
                # Index in batches
                if len(current_batch) >= batch_size:
                    success = es_client.batch_index_tasks(current_batch)
                    if success:
                        stats["indexed_tasks"] += len(current_batch)
                    else:
                        stats["errors"] += len(current_batch)
                    
                    current_batch = []
        
        # Index any remaining tasks
        if current_batch:
            success = es_client.batch_index_tasks(current_batch)
            if success:
                stats["indexed_tasks"] += len(current_batch)
            else:
                stats["errors"] += len(current_batch)
        
        # Log results
        elapsed_time = time.time() - start_time
        logger.info(f"Task loading completed in {elapsed_time:.2f} seconds")
        logger.info(f"Tasks found: {stats['total_tasks']}, processed: {stats['processed_tasks']}, indexed: {stats['indexed_tasks']}, errors: {stats['errors']}")
        
        return stats
    except Exception as e:
        logger.error(f"Error loading tasks: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return stats

if __name__ == "__main__":
    load_tasks_to_elasticsearch()
