# Simple database module that focuses only on the Task model
import os
import logging
import pymysql
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, Text
from sqlalchemy.orm import sessionmaker, mapper

from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost/backup")

# Create SQLAlchemy engine with echo=True to see generated SQL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define a minimal Task class with just id and text fields
# This avoids issues with column naming
class Task:
    """Simple Task class - only defining the fields we need"""
    def __init__(self, id=None, text=None):
        self.id = id
        self.text = text

def get_all_tasks():
    """Get all tasks directly using SQL, avoiding ORM mapping issues"""
    conn = None
    try:
        # Extract connection details from DATABASE_URL
        # Assuming format is mysql+pymysql://username:password@host/dbname
        parsed_url = DATABASE_URL.replace('mysql+pymysql://', '').split('@')
        user_pass = parsed_url[0].split(':')
        host_db = parsed_url[1].split('/')
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host = host_db[0]
        db = host_db[1]
        
        # Connect directly with PyMySQL
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db
        )
        
        # Execute a simple SQL query to get just the id and text columns
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, text FROM _task")
            tasks = []
            for row in cursor.fetchall():
                task = Task(id=row[0], text=row[1])
                tasks.append(task)
            
            logger.info(f"Retrieved {len(tasks)} tasks from database")
            return tasks
            
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

# Helper function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
