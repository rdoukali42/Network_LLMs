"""
Workflow client for connecting Streamlit app to the AI system.
Handles communication with the main AI workflow via the service layer.
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
    """
    Legacy workflow client for backward compatibility.
    Now delegates to the service layer for centralized backend access.
    """
    
    def __init__(self):
        """Initialize the workflow client."""
        self.service_integration = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the service integration."""
        try:
            from service_integration import ServiceIntegration
            self.service_integration = ServiceIntegration()
        except Exception as e:
            print(f"Error initializing service integration: {e}")
            import traceback
            traceback.print_exc()
            self.service_integration = None
    
    def process_query(self, query: str, username: str = None) -> dict:
        """
        Process a user query through the AI workflow via service layer.
        
        Args:
            query: The user's question or request
            username: Username for the request
            
        Returns:
            dict: Response from the AI system
        """
        if not self.service_integration:
            return {
                "status": "error",
                "error": "Service integration not initialized. Please check your configuration."
            }
        
        try:
            # Use the service layer's workflow processing
            result = self.service_integration.process_workflow_query(query, username=username)
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error processing query: {str(e)}"
            }
    
    def is_ready(self) -> bool:
        """Check if the workflow client is ready to process queries."""
        return (self.service_integration is not None and 
                self.service_integration.is_healthy())
    
    def process_message(self, message: str, username: str = None) -> dict:
        """
        Alias for process_query to maintain compatibility with ticket system.
        
        Args:
            message: The user's message or request
            username: Username for the request
            
        Returns:
            dict: Response from the AI system
        """
        return self.process_query(message, username=username)
