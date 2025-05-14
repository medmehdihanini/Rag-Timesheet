import os
from elastic_search_simplified import ElasticSearchClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_elasticsearch():
    """Initialize Elasticsearch index and test connection"""
    try:
        logger.info("Testing connection to Elasticsearch...")
        es_client = ElasticSearchClient()
        
        # Test connection
        if es_client.es.ping():
            logger.info("Successfully connected to Elasticsearch")
        else:
            logger.error("Could not connect to Elasticsearch")
            return
        
        # Create index if not exists (this is redundant as the client already does this,
        # but it's good to have an explicit initialization script)
        es_client.create_index_if_not_exists()
        logger.info(f"Elasticsearch index '{es_client.index_name}' is ready")
        
    except Exception as e:
        logger.error(f"Error initializing Elasticsearch: {str(e)}")

if __name__ == "__main__":
    initialize_elasticsearch()
