#!/usr/bin/env python
"""
System verification script to check that all components of the RAG-Timesheet system
are properly configured and accessible.
"""
import os
import sys
import time
import logging
import importlib
import traceback
from typing import Dict, List, Any
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemVerifier:
    """Verifies system components and configurations"""
    
    def __init__(self):
        self.results = {
            "python_environment": False,
            "dependencies": False,
            "configuration": False,
            "database": False,
            "elasticsearch": False,
            "models": False
        }
        
    def check_python_environment(self) -> bool:
        """Verify Python version and environment"""
        try:
            import platform
            python_version = platform.python_version()
            logger.info(f"Python version: {python_version}")
            
            major, minor, _ = map(int, python_version.split('.'))
            if major < 3 or (major == 3 and minor < 8):
                logger.warning(f"Python version {python_version} may be too old. Recommended: 3.8+")
                return False
                
            import sys
            logger.info(f"Python executable: {sys.executable}")
            logger.info(f"Python path: {sys.path}")
            
            self.results["python_environment"] = True
            return True
        except Exception as e:
            logger.error(f"Error checking Python environment: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """Check required dependencies"""
        required_packages = [
            "fastapi", 
            "uvicorn", 
            "sqlalchemy", 
            "pymysql",
            "elasticsearch", 
            "sentence_transformers", 
            "transformers",
            "torch",
            "python-dotenv",
            "tqdm"
        ]
        
        missing = []
        for package in required_packages:
            try:
                importlib.import_module(package.replace('-', '_'))
                logger.info(f"✅ {package} is installed")
            except ImportError:
                missing.append(package)
                logger.warning(f"❌ {package} is not installed")
        
        if missing:
            logger.warning(f"Missing packages: {', '.join(missing)}")
            return False
        
        self.results["dependencies"] = True
        return True
        
    def check_configuration(self) -> bool:
        """Check environment configuration"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # Check required env vars
            required_vars = [
                "DATABASE_URL",
                "ELASTICSEARCH_HOST",
                "ELASTICSEARCH_PORT"
            ]
            
            missing = []
            for var in required_vars:
                if not os.getenv(var):
                    missing.append(var)
                    logger.warning(f"❌ Missing environment variable: {var}")
                else:
                    logger.info(f"✅ Found environment variable: {var}")
            
            if missing:
                logger.warning("Some environment variables are missing")
                return False
            
            self.results["configuration"] = True
            return True
        except Exception as e:
            logger.error(f"Error checking configuration: {e}")
            return False
    
    def check_database(self) -> bool:
        """Check database connection"""
        try:
            # Import late to ensure proper environment loading
            from src.data.database.simple_database import get_all_tasks
            
            # Test connection by getting a small sample
            tasks = get_all_tasks()
            if tasks is None:
                logger.error("Failed to get tasks from database")
                return False
                
            task_count = len(tasks)
            logger.info(f"✅ Database connection successful, found {task_count} tasks")
            
            self.results["database"] = True
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
    
    def check_elasticsearch(self) -> bool:
        """Check Elasticsearch connection"""
        try:
            from src.data.elasticsearch.client import ElasticSearchClient
            
            es_client = ElasticSearchClient()
            if not es_client.es_available:
                logger.error("❌ Elasticsearch is not available")
                return False
            
            stats = es_client.get_stats()
            logger.info(f"✅ Elasticsearch connection successful")
            logger.info(f"   Index: {stats.get('index_name')}")
            logger.info(f"   Documents: {stats.get('doc_count')}")
            
            self.results["elasticsearch"] = True
            return True
        except Exception as e:
            logger.error(f"Error connecting to Elasticsearch: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
    
    def check_models(self) -> bool:
        """Check ML models"""
        try:
            from src.models.embedding.generator import EmbeddingGenerator
            from src.models.generation.task_generator import TaskGenerator
            
            # Test embedding
            embedding_generator = EmbeddingGenerator()
            test_text = "Test text for embedding"
            embedding = embedding_generator.generate_embedding(test_text)
            logger.info(f"✅ Embedding model working, vector length: {len(embedding)}")
            
            # Test task generator model (basic initialization only)
            task_generator = TaskGenerator()
            logger.info(f"✅ Task generator model initialized")
            
            self.results["models"] = True
            return True
        except Exception as e:
            logger.error(f"Error checking ML models: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
    
    def run_all_checks(self) -> Dict[str, bool]:
        """Run all verification checks"""
        logger.info("Starting system verification...")
        
        self.check_python_environment()
        self.check_dependencies()
        self.check_configuration()
        
        # These checks depend on configuration
        if self.results["configuration"]:
            self.check_database()
            self.check_elasticsearch()
            self.check_models()
        
        # Print summary
        logger.info("\n=== Verification Results ===")
        all_passed = True
        for check, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {check}")
            if not result:
                all_passed = False
        
        if all_passed:
            logger.info("\n✅ All checks passed! The system is ready to use.")
        else:
            logger.warning("\n❌ Some checks failed. Please address the issues above.")
        
        return self.results

if __name__ == "__main__":
    verifier = SystemVerifier()
    verifier.run_all_checks()
