"""
Workflow client for connecting Streamlit app to the AI system.
Handles communication with the main AI workflow.
"""

import os
import sys
from pathlib import Path

# Load environment variables
project_root = Path(__file__).parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    print("Warning: python-dotenv not found. Environment variables should be set manually.")

# Add src to path
sys.path.insert(0, str(project_root / "src"))

class WorkflowClient:
    """Client for interacting with the AI workflow system."""
    
    def __init__(self):
        """Initialize the workflow client."""
        self.system = None
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the AI system."""
        try:
            # Change to project root for proper imports
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            # Import with explicit path to avoid conflicts
            import sys
            sys.path.insert(0, str(project_root / "src"))
            
            from main import AISystem
            self.system = AISystem()
            
            # Restore working directory
            os.chdir(original_cwd)
            
        except Exception as e:
            print(f"Error initializing AI system: {e}")
            import traceback
            traceback.print_exc()
            self.system = None
    
    def process_query(self, query: str) -> dict:
        """
        Process a user query through the AI workflow.
        
        Args:
            query: The user's question or request
            
        Returns:
            dict: Response from the AI system
        """
        if not self.system:
            return {
                "status": "error",
                "error": "AI system not initialized. Please check your configuration."
            }
        
        try:
            # Change to project root for processing
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            # Process the query through the workflow
            result = self.system.process_query(query)
            
            # Restore working directory
            os.chdir(original_cwd)
            
            return result
            
        except Exception as e:
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            
            return {
                "status": "error",
                "error": f"Error processing query: {str(e)}"
            }
    
    def is_ready(self) -> bool:
        """Check if the workflow client is ready to process queries."""
        return self.system is not None
    
    def process_message(self, message: str) -> dict:
        """
        Alias for process_query to maintain compatibility with ticket system.
        
        Args:
            message: The user's message or request
            
        Returns:
            dict: Response from the AI system
        """
        return self.process_query(message)
