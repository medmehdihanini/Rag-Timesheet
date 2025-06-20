from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from src.utils.utils import clean_text, format_tasks_for_context, extract_tasks_from_generation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskGenerator:
    def __init__(self, model_name="google/flan-t5-base"):
        logger.info(f"Initializing TaskGenerator with model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Fallback tasks for different confidence levels
        self.fallback_tasks = {
            "high_confidence": [
                "Define project requirements and specifications",
                "Create project architecture and design documents", 
                "Set up development environment and tools",
                "Implement core functionality components",
                "Write comprehensive test cases and documentation"
            ],
            "medium_confidence": [
                "Analyze project requirements",
                "Design system architecture", 
                "Develop core features",
                "Test and validate functionality",
                "Document project implementation"
            ],
            "low_confidence": [
                "Research project requirements",
                "Plan development approach",
                "Create basic implementation",
                "Perform initial testing",
                "Prepare project documentation"
            ],            "very_low_confidence": [
                "I'm not sure what specific tasks would be appropriate for this input. Could you please provide a clearer project description related to software development, web applications, or other technical projects?"
            ]
        }
    
    def assess_context_quality(self, project_description: str, similar_projects: List[Dict]) -> Dict[str, Any]:
        """Assess the quality of context for generation"""
        assessment = {
            "description_quality": "low",
            "context_relevance": 0.0,
            "has_similar_context": False,
            "total_similar_tasks": 0,
            "unique_projects": 0,
            "avg_similarity_score": 0.0
        }
        
        # Assess description quality
        desc_words = len(project_description.split())
        if desc_words >= 10:
            assessment["description_quality"] = "high"
        elif desc_words >= 5:
            assessment["description_quality"] = "medium"
        
        # Assess similar projects context
        if similar_projects:
            assessment["has_similar_context"] = True
            assessment["unique_projects"] = len(similar_projects)
            
            total_tasks = sum(len(p.get('tasks', [])) for p in similar_projects)
            assessment["total_similar_tasks"] = total_tasks
            
            # Calculate average similarity score
            scores = [p.get('score', 0.0) for p in similar_projects if p.get('score', 0.0) > 0]
            if scores:
                assessment["avg_similarity_score"] = sum(scores) / len(scores)
        
        # Overall context relevance score
        relevance_factors = [
            assessment["description_quality"] == "high",
            assessment["has_similar_context"],
            assessment["total_similar_tasks"] > 0,
            assessment["avg_similarity_score"] > 0.3
        ]
        
        assessment["context_relevance"] = sum(relevance_factors) / len(relevance_factors)
        
        return assessment
    
    def create_enhanced_prompt(self, project_description: str, similar_projects: List[Dict], context_assessment: Dict) -> str:
        """Create an enhanced prompt based on context quality"""
        
        # Clean the project description
        cleaned_description = clean_text(project_description)
        
        # Base prompt structure
        prompt_parts = []
        
        # Add instruction based on context quality
        if context_assessment["context_relevance"] >= 0.75:
            instruction = "You are an expert project manager. Based on the project description and similar successful projects below, generate specific, actionable tasks."
        elif context_assessment["context_relevance"] >= 0.5:
            instruction = "You are a project management assistant. Based on the project description and available context, suggest relevant tasks."
        else:
            instruction = "Based on the project description provided, suggest general project tasks."
        
        prompt_parts.append(instruction)
        prompt_parts.append(f"\nProject Description: {cleaned_description}")
        
        # Add context from similar projects if available and relevant
        if similar_projects and context_assessment["has_similar_context"]:
            prompt_parts.append("\nSimilar Projects for Reference:")
            
            for i, project in enumerate(similar_projects[:3]):  # Limit to top 3
                if project.get('project_name') and project.get('tasks'):
                    prompt_parts.append(f"\nProject {i+1}: {project['project_name']}")
                    if project.get('project_description'):
                        prompt_parts.append(f"Description: {clean_text(project['project_description'])}")
                    
                    if project.get('tasks'):
                        prompt_parts.append("Example tasks:")
                        task_text = format_tasks_for_context(project['tasks'][:5])  # Limit tasks
                        prompt_parts.append(task_text)
        
        # Add generation instruction
        if context_assessment["context_relevance"] >= 0.5:
            generation_instruction = "\nGenerate 5 specific, actionable tasks for this project. Each task should be clear, measurable, and relevant to the project description. Format as a numbered list:"
        else:
            generation_instruction = "\nGenerate 5 general project tasks that might be relevant. Format as a numbered list:"
        
        prompt_parts.append(generation_instruction)
        
        return "\n".join(prompt_parts)
    
    def determine_confidence_level(self, context_assessment: Dict, query_metadata: Dict = None) -> str:
        """Determine overall confidence level for task generation"""
        factors = []
        
        # Context quality factors
        factors.append(context_assessment.get("context_relevance", 0.0))
        
        # Query quality factors if available
        if query_metadata:
            factors.append(query_metadata.get("relevance_score", 0.0))
            if not query_metadata.get("is_coherent", True):
                factors.append(0.0)  # Penalize incoherent queries
        
        # Calculate overall confidence
        if not factors:
            overall_confidence = 0.0
        else:
            overall_confidence = sum(factors) / len(factors)
        
        # Map to confidence levels
        if overall_confidence >= 0.7:
            return "high_confidence"
        elif overall_confidence >= 0.5:
            return "medium_confidence"
        elif overall_confidence >= 0.3:
            return "low_confidence"
        else:
            return "very_low_confidence"
    
    def generate_tasks(self, project_description: str, similar_projects: List[Dict] = None, 
                      max_length: int = 150, num_return_sequences: int = 3, 
                      query_metadata: Dict = None) -> List[str]:
        """Generate task suggestions with enhanced quality control"""
        
        # Assess context quality
        context_assessment = self.assess_context_quality(project_description, similar_projects or [])
        
        # Determine confidence level
        confidence_level = self.determine_confidence_level(context_assessment, query_metadata)
        
        logger.info(f"Generation confidence level: {confidence_level}")
        logger.info(f"Context assessment: {context_assessment}")
        
        # For very low confidence, return appropriate fallback responses
        if confidence_level == "very_low_confidence":
            logger.warning("Very low confidence in input quality, returning fallback responses")
            return self.fallback_tasks["very_low_confidence"]
        
        # For low confidence, mix generated and fallback tasks
        if confidence_level == "low_confidence" and context_assessment["context_relevance"] < 0.2:
            logger.warning("Low confidence with poor context, returning fallback tasks")
            return self.fallback_tasks["low_confidence"]
        
        # Generate tasks using the model
        try:
            prompt = self.create_enhanced_prompt(project_description, similar_projects or [], context_assessment)
            
            logger.debug(f"Generated prompt length: {len(prompt)}")
            
            # Tokenize with appropriate truncation
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            
            # Adjust generation parameters based on confidence
            if confidence_level == "high_confidence":
                temperature = 0.7
                top_k = 50
                top_p = 0.9
            elif confidence_level == "medium_confidence":
                temperature = 0.8
                top_k = 40
                top_p = 0.85
            else:  # low_confidence
                temperature = 0.9
                top_k = 30
                top_p = 0.8
            
            # Generate tasks
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=max_length,
                num_return_sequences=min(num_return_sequences, 3),  # Limit sequences
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                do_sample=True,
                no_repeat_ngram_size=2,
                early_stopping=True
            )
            
            all_tasks = []
            for output in outputs:
                generated_text = self.tokenizer.decode(output, skip_special_tokens=True)
                tasks_from_generation = extract_tasks_from_generation(generated_text)
                all_tasks.extend(tasks_from_generation)
            
            # Remove duplicates while preserving order
            unique_tasks = []
            for task in all_tasks:
                if task not in unique_tasks and len(task.strip()) > 5:
                    unique_tasks.append(task.strip())
            
            # If generation failed or produced poor results, use fallbacks
            if len(unique_tasks) < 2:
                logger.warning("Generation produced insufficient tasks, using fallbacks")
                fallback_tasks = self.fallback_tasks.get(confidence_level, self.fallback_tasks["medium_confidence"])
                return fallback_tasks[:5]
            
            # Ensure we have exactly 5 tasks
            if len(unique_tasks) < 5:
                fallback_tasks = self.fallback_tasks.get(confidence_level, self.fallback_tasks["medium_confidence"])
                unique_tasks.extend(fallback_tasks[:5-len(unique_tasks)])
            
            return unique_tasks[:5]
            
        except Exception as e:
            logger.error(f"Error generating tasks: {str(e)}")
            # Return appropriate fallback based on confidence level
            fallback_tasks = self.fallback_tasks.get(confidence_level, self.fallback_tasks["medium_confidence"])
            return fallback_tasks[:5]
