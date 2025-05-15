"""
Test the utility functions
"""
import sys
import os
import unittest

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.utils import clean_text, preprocess_project_description, format_tasks_for_context, extract_tasks_from_generation


class TestUtilsFunctions(unittest.TestCase):
    """Test cases for utility functions"""

    def test_clean_text(self):
        """Test the clean_text function"""
        # Test whitespace handling
        self.assertEqual(clean_text("  Hello  World  "), "Hello World")
        
        # Test special character removal
        self.assertEqual(clean_text("Hello@World#123"), "HelloWorld123")
        
        # Test keeping allowed characters
        self.assertEqual(clean_text("Hello, World! This is a test."), "Hello, World! This is a test.")
        
        # Test empty input
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_preprocess_project_description(self):
        """Test the preprocess_project_description function"""
        # Short description should return as is after cleaning
        short_desc = "Short description"
        self.assertEqual(preprocess_project_description(short_desc), clean_text(short_desc))
        
        # Add more tests specific to the preprocess_project_description function

    def test_format_tasks_for_context(self):
        """Test the format_tasks_for_context function"""
        # Test with a list of task dictionaries
        tasks = [
            {"id": 1, "text": "Task one"},
            {"id": 2, "text": "Task two"}
        ]
        
        formatted = format_tasks_for_context(tasks)
        self.assertIn("Task one", formatted)
        self.assertIn("Task two", formatted)
        
        # Test with empty list
        self.assertEqual(format_tasks_for_context([]), "")

    def test_extract_tasks_from_generation(self):
        """Test the extract_tasks_from_generation function"""
        # Test with task list in generated text
        generated = "Here are some tasks: 1. First task 2. Second task 3. Third task"
        tasks = extract_tasks_from_generation(generated)
        
        self.assertEqual(len(tasks), 3)
        self.assertIn("First task", tasks)
        self.assertIn("Second task", tasks)
        self.assertIn("Third task", tasks)
        
        # Test with no tasks
        self.assertEqual(extract_tasks_from_generation("No tasks here"), [])


if __name__ == '__main__':
    unittest.main()
