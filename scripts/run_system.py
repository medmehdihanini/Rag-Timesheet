"""
Initialize and run the task-based RAG system
"""
import os
import sys
import logging
import time
import argparse
from dotenv import load_dotenv
import uvicorn

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from new locations
from scripts.simple_load_tasks import load_tasks_to_elasticsearch
from src.data.elasticsearch.client import ElasticSearchClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def initialize_system():
    """Initialize the task-based RAG system by setting up Elasticsearch and loading data"""
    logger.info("Initializing task-based RAG system...")
    
    # Check Elasticsearch connection
    es_client = ElasticSearchClient()
    if not es_client.es_available:
        logger.error("Failed to connect to Elasticsearch. Please check your Elasticsearch instance and settings.")
        return False
    
    # Load data from database to Elasticsearch
    logger.info("Loading tasks from database to Elasticsearch...")
    start_time = time.time()
    stats = load_tasks_to_elasticsearch()
    elapsed_time = time.time() - start_time
    
    logger.info(f"Data loading completed in {elapsed_time:.2f} seconds")
    logger.info(f"Loaded {stats['indexed_tasks']} tasks, {stats['errors']} errors")
    
    # Check if any tasks were loaded
    if stats["indexed_tasks"] == 0:
        logger.warning("No tasks were indexed. The system may not work properly.")
        return False
    
    logger.info("System initialization completed successfully!")
    return True

def start_api_server(host="0.0.0.0", port=8000, reload=False):
    """Start the FastAPI server"""
    logger.info(f"Starting API server on {host}:{port}")
    from src.api.app import app
    uvicorn.run(app, host=host, port=port, reload=reload)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize and run the task-based RAG system')
    parser.add_argument('--init', action='store_true', help='Initialize the system by loading data to Elasticsearch')
    parser.add_argument('--run', action='store_true', help='Start the API server')
    parser.add_argument('--host', type=str, default="0.0.0.0", help='Host to run the API server on')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the API server on')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    
    args = parser.parse_args()
    
    if args.init:
        if initialize_system():
            logger.info("System initialized successfully!")
        else:
            logger.error("System initialization failed.")
    
    if args.run:
        start_api_server(host=args.host, port=args.port, reload=args.reload)
    
    if not args.init and not args.run:
        parser.print_help()
