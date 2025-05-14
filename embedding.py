from sentence_transformers import SentenceTransformer
import torch
import numpy as np

class EmbeddingGenerator:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def generate_embedding(self, text):
        """Generate embedding for a single text"""
        embedding = self.model.encode(text, convert_to_tensor=True)
        return embedding.cpu().numpy().tolist()
    
    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts"""
        embeddings = self.model.encode(texts, convert_to_tensor=True)
        return embeddings.cpu().numpy().tolist()
