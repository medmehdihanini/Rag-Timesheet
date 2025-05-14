import os
import logging
import ssl
import certifi
from elasticsearch import Elasticsearch, helpers, exceptions
import json
import urllib3
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress insecure HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ElasticSearchClient:
    def __init__(self):
        """Initialize Elasticsearch client with configuration from environment variables"""
        self.es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        self.es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
        self.es_user = os.getenv("ELASTICSEARCH_USER")
        self.es_password = os.getenv("ELASTICSEARCH_PASSWORD")
        self.use_ssl = os.getenv("ELASTICSEARCH_USE_SSL", "false").lower() == "true"
        self.cert_path = os.getenv("ELASTICSEARCH_CERT_PATH")
        self.index_name = os.getenv("ELASTICSEARCH_INDEX", "tasks_embeddings")
        
        protocol = "https" if self.use_ssl else "http"
        url = f"{protocol}://{self.es_host}:{self.es_port}"
        logger.info(f"Connecting to Elasticsearch at {url}")
        
        # Connect to Elasticsearch
        try:
            # Using the successful connection method from test_es_connection.py
            if self.use_ssl:
                logger.info("Using HTTPS connection with SSL settings")
                
                # Create connection arguments based on the successful test
                es_kwargs = {
                    "hosts": [f"https://{self.es_host}:{self.es_port}"],
                    "verify_certs": False,           # Don't verify SSL certs in dev
                    "ssl_show_warn": False,          # Don't show SSL warnings
                    "request_timeout": 30,           # Increase timeout for slower connections
                    "retry_on_timeout": True,        # Retry on timeout
                }
                
                # Add certificate path if provided
                if self.cert_path:
                    es_kwargs["ca_certs"] = self.cert_path
                
                # Add authentication if provided
                if self.es_user and self.es_password:
                    es_kwargs["basic_auth"] = (self.es_user, self.es_password)
                
                self.es = Elasticsearch(**es_kwargs)
            else:
                # For HTTP connection (fallback, though we're using HTTPS)
                logger.info("Using HTTP connection")
                es_kwargs = {
                    "hosts": [f"http://{self.es_host}:{self.es_port}"],
                    "request_timeout": 30,
                    "retry_on_timeout": True
                }
                
                # Add auth if provided
                if self.es_user and self.es_password:
                    es_kwargs["basic_auth"] = (self.es_user, self.es_password)
                
                self.es = Elasticsearch(**es_kwargs)
            
            # Test connection
            logger.info("Testing connection to Elasticsearch...")
            ping_result = self.es.ping()
            
            if not ping_result:
                logger.warning("Could not connect to Elasticsearch, some features may not work")
                self.es_available = False
            else:
                logger.info("Successfully connected to Elasticsearch")
                self.es_available = True
                self.create_index_if_not_exists()
        except Exception as e:
            logger.error(f"Error connecting to Elasticsearch: {str(e)}")
            self.es_available = False
            
    def create_index_if_not_exists(self):
        """Create the Elasticsearch index with task embeddings mapping if it doesn't exist"""
        try:
            index_exists = self.es.indices.exists(index=self.index_name)
            if not index_exists:
                logger.info(f"Creating index '{self.index_name}'")
                
                # Create index with task embeddings mapping
                mapping = {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    },
                    "mappings": {
                        "properties": {
                            "task_id": {"type": "keyword"},
                            "task_text": {"type": "text", "analyzer": "standard"},
                            "embedding": {
                                "type": "dense_vector",
                                "dims": 384,  # all-MiniLM-L6-v2 has 384 dimensions
                                "index": True,
                                "similarity": "cosine"
                            },
                            # Project info kept as metadata
                            "project_id": {"type": "keyword"},
                            "project_name": {"type": "text", "analyzer": "standard"},
                            "project_description": {"type": "text", "analyzer": "standard"}
                        }
                    }
                }
                self.es.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Index '{self.index_name}' created successfully")
        except exceptions.ElasticsearchException as e:
            logger.error(f"Error creating index: {str(e)}")
    
    def index_task(self, task_id: str, task_text: str, embedding: List[float], 
                   project_id: str, project_name: str, project_description: str) -> bool:
        """Index a task with its text embedding and project context"""
        if not self.es_available:
            logger.error("Elasticsearch not available")
            return False
            
        try:
            doc = {
                "task_id": task_id,
                "task_text": task_text,
                "embedding": embedding,
                "project_id": project_id,
                "project_name": project_name,
                "project_description": project_description
            }
            
            self.es.index(index=self.index_name, body=doc, id=task_id)
            return True
        except Exception as e:
            logger.error(f"Error indexing task: {str(e)}")
            return False
    
    def batch_index_tasks(self, tasks_data: List[Dict[str, Any]]) -> bool:
        """Batch index multiple tasks with their embeddings"""
        if not self.es_available:
            logger.error("Elasticsearch not available")
            return False
            
        if not tasks_data:
            logger.warning("No tasks data provided for indexing")
            return False
        
        try:
            actions = []
            
            for data in tasks_data:
                action = {
                    "_index": self.index_name,
                    "_id": data["task_id"],
                    "_source": data
                }
                actions.append(action)
            
            if actions:
                helpers.bulk(self.es, actions)
                logger.info(f"Bulk indexed {len(actions)} tasks")
                return True
            return False
        except Exception as e:
            logger.error(f"Error batch indexing tasks: {str(e)}")
            return False
    
    def vector_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar tasks based on vector embedding"""
        if not self.es_available:
            logger.error("Elasticsearch not available")
            return []
            
        try:
            query = {
                "knn": {
                    "field": "embedding",
                    "query_vector": query_embedding,
                    "k": top_k,
                    "num_candidates": top_k * 2
                }
            }
            
            response = self.es.search(
                index=self.index_name,
                body={"query": query, "size": top_k}
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "task_id": hit["_source"]["task_id"],
                    "task_text": hit["_source"]["task_text"],
                    "project_id": hit["_source"]["project_id"],
                    "project_name": hit["_source"]["project_name"],
                    "project_description": hit["_source"]["project_description"],
                    "score": hit["_score"]
                })
            
            logger.info(f"Vector search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            return []
    
    def hybrid_search(self, query_text: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using both semantic (vector) and lexical (text) search
        """
        if not self.es_available:
            logger.error("Elasticsearch not available")
            return []
            
        try:
            # Hybrid search query combining KNN and text search
            query = {
                "bool": {
                    "should": [
                        {
                            "knn": {
                                "field": "embedding",
                                "query_vector": query_embedding,
                                "k": top_k * 2,
                                "num_candidates": top_k * 4
                            }
                        },
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": ["task_text^3", "project_name^2", "project_description"],
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            }
            
            response = self.es.search(
                index=self.index_name,
                body={
                    "query": query,
                    "size": top_k
                }
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "task_id": hit["_source"]["task_id"],
                    "task_text": hit["_source"]["task_text"],
                    "project_id": hit["_source"]["project_id"],
                    "project_name": hit["_source"]["project_name"],
                    "project_description": hit["_source"]["project_description"],
                    "score": hit["_score"]
                })
            
            logger.info(f"Hybrid search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return []
            
    def delete_task(self, task_id: str) -> bool:
        """Delete a task from the index"""
        if not self.es_available:
            logger.error("Elasticsearch not available")
            return False
            
        try:
            self.es.delete(index=self.index_name, id=task_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.es_available:
            logger.error("Elasticsearch not available")
            return {"available": False}
            
        try:
            stats = self.es.indices.stats(index=self.index_name)
            count = self.es.count(index=self.index_name)
            
            return {
                "available": True,
                "doc_count": count["count"],
                "index_size_bytes": stats["indices"][self.index_name]["total"]["store"]["size_in_bytes"],
                "index_name": self.index_name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"available": False, "error": str(e)}
