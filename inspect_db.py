"""
Script to inspect the database structure and determine actual column names
"""
import os
import logging
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost/backup")

def inspect_database():
    """Inspect the database structure to get table and column information"""
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Get all table names
        tables = inspector.get_table_names()
        logger.info(f"Tables in database: {tables}")
        
        # Look for the _task table
        if "_task" in tables:
            logger.info("Found _task table, inspecting columns...")
            
            # Get columns for _task table
            columns = inspector.get_columns("_task")
            for column in columns:
                logger.info(f"Column: {column['name']}, Type: {column['type']}")
            
            return columns
        else:
            logger.error("_task table not found in database!")
            return None
            
    except Exception as e:
        logger.error(f"Error inspecting database: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("Inspecting database structure...")
    inspect_database()
