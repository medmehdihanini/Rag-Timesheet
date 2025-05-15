from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import logging
from src.utils.utils import clean_text, format_tasks_for_context, extract_tasks_from_generation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskGenerator:
    def __init__(self, model_name="google/flan-t5-base"):
        logger.info(f"Initializing TaskGenerator with model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
    def generate_tasks(self, project_description, similar_projects=None, max_length=150, num_return_sequences=3):
        """Generate task suggestions based on project description and similar projects"""
        # Clean the project description
        cleaned_description = clean_text(project_description)
        
        # Create the context for the model
        context = f"Project description: {cleaned_description}\n\n"
        
        if similar_projects:
            context += "Similar projects and their tasks:\n"
            for i, project in enumerate(similar_projects):
                # Only include top 3 similar projects to keep context manageable
                if i >= 3:
                    break
                
                if project.get('project_name') and project.get('project_description'):
                    context += f"Project {i+1}: {project['project_name']}\n"
                    if project.get('project_description'):
                        context += f"Description: {clean_text(project['project_description'])}\n"
                    
                    if project.get('tasks'):
                        context += "Tasks:\n"
                        task_text = format_tasks_for_context(project['tasks'])
                        context += f"{task_text}\n"
                    context += "\n"
        
        prompt = f"{context}\nBased on the project description and similar tasks above, generate a list of 5 specific tasks for this project. Format tasks as a numbered list :"
        
        logger.debug(f"Prompt length: {len(prompt)}")
        
        # Tokenize the input
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        # Generate tasks
        try:
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=max_length,
                num_return_sequences=num_return_sequences,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                do_sample=True,
                no_repeat_ngram_size=2
            )
            
            all_tasks = []
            for output in outputs:
                generated_text = self.tokenizer.decode(output, skip_special_tokens=True)
                tasks_from_generation = extract_tasks_from_generation(generated_text)
                all_tasks.extend(tasks_from_generation)
            
            # Remove duplicates while preserving order
            unique_tasks = []
            for task in all_tasks:
                if task not in unique_tasks:
                    unique_tasks.append(task)
            
            return unique_tasks[:5]  # Return at most 5 tasks
            
        except Exception as e:
            logger.error(f"Error generating tasks: {str(e)}")
            return ["Create project documentation", 
                    "Set up development environment", 
                    "Implement core functionality",
                    "Write automated tests",
                    "Deploy and monitor application"]
