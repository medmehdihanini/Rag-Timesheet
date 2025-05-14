"""
Helper script to download and cache the required models
This script downloads the embedding and generation models in advance to avoid
downloading them on first use, which can be slow
"""

import os
import argparse
import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
import torch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_embedding_model(model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """Download and cache the sentence transformer model"""
    logger.info(f"Downloading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        # Test the model with a sample text
        test_text = "This is a test sentence to check if the model works."
        embeddings = model.encode(test_text)
        logger.info(f"Successfully downloaded embedding model. Embedding shape: {embeddings.shape}")
        return True
    except Exception as e:
        logger.error(f"Error downloading embedding model: {e}")
        return False

def download_generation_model(model_name="google/flan-t5-base"):
    """Download and cache the text generation model"""
    logger.info(f"Downloading generation model: {model_name}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Test the model with a sample text
        test_text = "Suggest 3 tasks for a web development project:"
        inputs = tokenizer(test_text, return_tensors="pt")
        outputs = model.generate(inputs.input_ids, max_length=50)
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        logger.info(f"Successfully downloaded generation model. Sample output: {decoded}")
        return True
    except Exception as e:
        logger.error(f"Error downloading generation model: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download and cache models for the Task Suggestion RAG System")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2", 
                        help="Embedding model name (default: sentence-transformers/all-MiniLM-L6-v2)")
    parser.add_argument("--generation-model", default="google/flan-t5-base",
                        help="Generation model name (default: google/flan-t5-base)")
    
    args = parser.parse_args()
    
    # Download embedding model
    success_embedding = download_embedding_model(args.embedding_model)
    
    # Download generation model
    success_generation = download_generation_model(args.generation_model)
    
    if success_embedding and success_generation:
        logger.info("All models downloaded successfully!")
    else:
        logger.warning("Some models could not be downloaded. Check the logs for details.")

if __name__ == "__main__":
    main()
