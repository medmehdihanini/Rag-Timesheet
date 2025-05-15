"""
Test the embedding generator
"""
import sys
import os
import unittest
import numpy as np

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.embedding.generator import EmbeddingGenerator


class TestEmbeddingGenerator(unittest.TestCase):
    """Test cases for the EmbeddingGenerator class"""

    def setUp(self):
        """Set up test environment"""
        self.generator = EmbeddingGenerator()
        self.test_text = "This is a test sentence for embeddings."

    def test_embedding_shape(self):
        """Test that the generated embedding has the correct shape"""
        embedding = self.generator.generate_embedding(self.test_text)
        self.assertEqual(len(embedding), 384)  # all-MiniLM-L6-v2 produces 384-dimensional vectors

    def test_embedding_consistency(self):
        """Test that the same text consistently produces similar embeddings"""
        embedding1 = self.generator.generate_embedding(self.test_text)
        embedding2 = self.generator.generate_embedding(self.test_text)
        
        # Convert to numpy arrays for easier comparison
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        
        # The same text should produce highly similar embeddings
        self.assertGreater(similarity, 0.99)

    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings"""
        text1 = "This is the first test sentence."
        text2 = "This is a completely different sentence about another topic."
        
        embedding1 = np.array(self.generator.generate_embedding(text1))
        embedding2 = np.array(self.generator.generate_embedding(text2))
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        
        # Different texts should have lower similarity
        self.assertLess(similarity, 0.95)


if __name__ == '__main__':
    unittest.main()
