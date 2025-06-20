from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import re
from typing import List, Tuple, Optional

class EmbeddingGenerator:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        
        # Domain-specific keywords for relevance detection
        self.domain_keywords = {
            'high_relevance': [
                'project', 'task', 'development', 'implementation', 'design', 'testing', 
                'deployment', 'analysis', 'management', 'planning', 'documentation',
                'requirements', 'specification', 'architecture', 'coding', 'programming',
                'database', 'frontend', 'backend', 'api', 'integration', 'review',
                'maintenance', 'monitoring', 'security', 'performance', 'optimization',
                'client', 'stakeholder', 'meeting', 'deliverable', 'milestone',
                'sprint', 'agile', 'scrum', 'timeline', 'deadline', 'budget',
                'quality', 'assurance', 'training', 'deployment', 'release'
            ],
            'medium_relevance': [
                'work', 'business', 'process', 'system', 'application', 'software',
                'solution', 'feature', 'function', 'workflow', 'procedure',
                'operation', 'service', 'platform', 'infrastructure', 'framework',
                'technology', 'tool', 'resource', 'asset', 'component'
            ],
            'low_relevance': [
                'report', 'document', 'file', 'data', 'information', 'content',
                'user', 'customer', 'support', 'help', 'guide', 'manual'
            ]
        }
        
        # Minimum similarity threshold for considering results relevant
        self.similarity_threshold = 0.3
        self.high_confidence_threshold = 0.7
        
    def calculate_query_relevance(self, text: str) -> Tuple[float, str]:
        """
        Calculate how relevant the query is to the domain (0.0 to 1.0)
        Returns (relevance_score, confidence_level)
        """
        if not text or len(text.strip()) < 5:
            return 0.0, "very_low"
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        if len(words) < 2:
            return 0.1, "very_low"
        
        # Calculate relevance based on keyword presence
        high_score = sum(1 for word in words if word in self.domain_keywords['high_relevance'])
        medium_score = sum(1 for word in words if word in self.domain_keywords['medium_relevance'])
        low_score = sum(1 for word in words if word in self.domain_keywords['low_relevance'])
        
        total_score = (high_score * 3) + (medium_score * 2) + (low_score * 1)
        max_possible_score = len(words) * 3
        
        if max_possible_score == 0:
            relevance_score = 0.0
        else:
            relevance_score = min(total_score / max_possible_score, 1.0)
        
        # Boost score if query contains project/task-specific patterns
        project_patterns = [
            r'\b(project|task|develop|implement|create|build|design)\b',
            r'\b(web|mobile|app|system|software|platform)\b',
            r'\b(frontend|backend|database|api|ui|ux)\b'
        ]
        
        pattern_matches = sum(1 for pattern in project_patterns 
                            if re.search(pattern, text_lower))
        
        if pattern_matches > 0:
            relevance_score = min(relevance_score + (pattern_matches * 0.1), 1.0)
        
        # Determine confidence level
        if relevance_score >= 0.7:
            confidence = "high"
        elif relevance_score >= 0.4:
            confidence = "medium"
        elif relevance_score >= 0.2:
            confidence = "low"
        else:
            confidence = "very_low"
        
        return relevance_score, confidence
    
    def is_coherent_query(self, text: str) -> bool:
        """Check if the query is coherent and meaningful"""
        if not text or len(text.strip()) < 3:
            return False
        
        # Check for basic coherence indicators
        words = text.split()
        if len(words) < 2:
            return False
        
        # Check for excessive repetition (spam-like)
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
            return False
        
        # Check for random character sequences
        if re.search(r'[a-zA-Z]{20,}', text):  # Very long words without spaces
            return False
        
        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', text)) / len(text)
        if special_char_ratio > 0.3:
            return False
        
        return True
    
    def validate_and_enhance_query(self, text: str) -> Tuple[str, dict]:
        """
        Validate query and return enhanced version with metadata
        Returns (processed_text, metadata)
        """
        metadata = {
            'original_length': len(text),
            'is_coherent': False,
            'relevance_score': 0.0,
            'confidence_level': 'very_low',
            'should_process': False,
            'enhancement_applied': False
        }
        
        # Basic coherence check
        metadata['is_coherent'] = self.is_coherent_query(text)
        if not metadata['is_coherent']:
            return text, metadata
        
        # Calculate relevance
        relevance_score, confidence_level = self.calculate_query_relevance(text)
        metadata['relevance_score'] = relevance_score
        metadata['confidence_level'] = confidence_level
        
        # Decide if query should be processed
        metadata['should_process'] = (
            metadata['is_coherent'] and 
            relevance_score >= 0.15  # Very low threshold for processing
        )
        
        # Enhance query if needed (simple enhancement)
        enhanced_text = text
        if relevance_score < 0.5 and metadata['should_process']:
            # Add context hint for better embedding
            enhanced_text = f"project task description: {text}"
            metadata['enhancement_applied'] = True
        
        return enhanced_text, metadata
    
    def filter_results_by_similarity(self, results: List[dict], min_threshold: Optional[float] = None) -> List[dict]:
        """Filter search results based on similarity threshold"""
        threshold = min_threshold or self.similarity_threshold
        
        filtered_results = []
        for result in results:
            score = result.get('score', 0.0)
            
            # Elasticsearch scores can be different depending on search type
            # For cosine similarity, scores are typically between 0 and 2
            # Normalize to 0-1 range if needed
            if score > 2:  # Likely raw Elasticsearch score
                normalized_score = min(score / 10.0, 1.0)  # Simple normalization
            else:
                normalized_score = score
            
            result['normalized_score'] = normalized_score
            
            if normalized_score >= threshold:
                filtered_results.append(result)
        
        return filtered_results
    
    def calculate_result_confidence(self, results: List[dict], query_metadata: dict) -> str:
        """Calculate overall confidence in the results"""
        if not results:
            return "no_results"
        
        # Factor in query relevance
        query_relevance = query_metadata.get('relevance_score', 0.0)
        
        # Factor in result scores
        avg_score = np.mean([r.get('normalized_score', 0.0) for r in results])
        max_score = max([r.get('normalized_score', 0.0) for r in results])
        
        # Combined confidence score
        combined_score = (query_relevance * 0.4) + (avg_score * 0.3) + (max_score * 0.3)
        
        if combined_score >= 0.7:
            return "high"
        elif combined_score >= 0.5:
            return "medium"
        elif combined_score >= 0.3:
            return "low"
        else:
            return "very_low"
    
    def generate_embedding(self, text):
        """Generate embedding for a single text"""
        embedding = self.model.encode(text, convert_to_tensor=True)
        return embedding.cpu().numpy().tolist()
    
    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts"""
        embeddings = self.model.encode(texts, convert_to_tensor=True)
        return embeddings.cpu().numpy().tolist()
