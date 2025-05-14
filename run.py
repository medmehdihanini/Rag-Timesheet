#!/usr/bin/env python3
"""
Entry point script for Task Suggestion RAG System
"""

import argparse
import logging
import subprocess
import sys
import os
import platform
from dotenv import load_dotenv
import time

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import sqlalchemy
        import sentence_transformers
        import transformers
        import elasticsearch
        import torch
        logger.info("All required packages are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing required package: {e}")
        logger.info("Please run: pip install -r requirements.txt")
        return False

def init_elasticsearch():
    """Initialize Elasticsearch indices"""
    logger.info("Initializing Elasticsearch...")
    try:
        from init_elasticsearch import initialize_elasticsearch
        initialize_elasticsearch()
    except Exception as e:
        logger.error(f"Error initializing Elasticsearch: {e}")
        return False
    return True

def load_data(parallel=False, workers=4):
    """Load data from MySQL to Elasticsearch"""
    logger.info("Loading data from MySQL to Elasticsearch...")
    try:
        if parallel:
            logger.info(f"Using parallel processing with {workers} workers")
            from load_data import parallel_load_data_to_elasticsearch
            parallel_load_data_to_elasticsearch(max_workers=workers)
        else:
            from load_data import load_data_to_elasticsearch
            load_data_to_elasticsearch()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return False
    return True

def start_api(host="127.0.0.1", port=8000, dev_mode=True):
    """Start the FastAPI application"""
    logger.info(f"Starting FastAPI application on {host}:{port}...")
    reload_flag = "--reload" if dev_mode else ""
    cmd = f"uvicorn main:app --host {host} --port {port} {reload_flag}"
    subprocess.run(cmd, shell=True)

def download_models():
    """Download and cache models"""
    logger.info("Downloading models...")
    try:
        from download_models import download_embedding_model, download_generation_model
        embedding_success = download_embedding_model()
        generation_success = download_generation_model()
        return embedding_success and generation_success
    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        return False

def docker_operations(operation, services=None):
    """Handle Docker operations"""
    if services is None:
        services = []
    
    services_str = " ".join(services) if services else ""
    
    if operation == "up":
        cmd = f"docker-compose up -d {services_str}"
        logger.info("Starting Docker containers...")
    elif operation == "down":
        cmd = f"docker-compose down {services_str}"
        logger.info("Stopping Docker containers...")
    elif operation == "build":
        cmd = f"docker-compose build {services_str}"
        logger.info("Building Docker images...")
    elif operation == "logs":
        cmd = f"docker-compose logs -f {services_str}"
        logger.info("Showing Docker logs...")
    else:
        logger.error(f"Unknown Docker operation: {operation}")
        return False
    
    logger.info(f"Running: {cmd}")
    return subprocess.run(cmd, shell=True).returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Task Suggestion RAG System")
    parser.add_argument("--init", action="store_true", help="Initialize Elasticsearch indices")
    parser.add_argument("--load-data", action="store_true", help="Load data from MySQL to Elasticsearch")
    parser.add_argument("--parallel", action="store_true", help="Use parallel processing for data loading")
    parser.add_argument("--workers", type=int, default=4, help="Number of workers for parallel processing")
    parser.add_argument("--start-api", action="store_true", help="Start the FastAPI application")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the API server")
    parser.add_argument("--port", default=8000, type=int, help="Port for the API server")
    parser.add_argument("--no-dev", action="store_true", help="Run in production mode (no auto-reload)")
    parser.add_argument("--download-models", action="store_true", help="Download and cache models")
    
    # Docker commands
    parser.add_argument("--docker-up", action="store_true", help="Start Docker containers")
    parser.add_argument("--docker-down", action="store_true", help="Stop Docker containers")
    parser.add_argument("--docker-build", action="store_true", help="Build Docker images")
    parser.add_argument("--docker-logs", action="store_true", help="Show Docker logs")
    parser.add_argument("--services", nargs="+", help="Specific Docker services to target")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Docker operations
    if args.docker_up:
        docker_operations("up", args.services)
        # Give Elasticsearch time to start
        logger.info("Waiting for Elasticsearch to start...")
        time.sleep(10)
        return
    
    if args.docker_down:
        docker_operations("down", args.services)
        return
    
    if args.docker_build:
        docker_operations("build", args.services)
        return
    
    if args.docker_logs:
        docker_operations("logs", args.services)
        return
    
    # Download models
    if args.download_models:
        download_models()
        return
    
    # Check requirements for local operation
    if not check_requirements():
        return
    
    # Initialize Elasticsearch
    if args.init:
        if not init_elasticsearch():
            return
    
    # Load data
    if args.load_data:
        if not load_data(args.parallel, args.workers):
            return
    
    # Start API
    if args.start_api:
        dev_mode = not args.no_dev
        start_api(host=args.host, port=args.port, dev_mode=dev_mode)

if __name__ == "__main__":
    main()
