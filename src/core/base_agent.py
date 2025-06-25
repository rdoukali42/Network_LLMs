"""
Base agent class providing common functionality for all AI agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger
from utils.exceptions import AITicketSystemException


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the system.
    
    Provides common functionality like logging, error handling,
    and standardized input/output interfaces.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None, tools: Optional[List] = None):
        """Initialize the base agent."""
        self.name = name
        self.config = config or {}
        self.tools = tools or []
        self.logger = get_logger(f"agent.{name}")
        
        self.logger.info(f"Initializing {name} agent")
        self._initialize()
    
    def _initialize(self):
        """Initialize agent-specific components. Override in subclasses."""
        pass
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for the agent.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Dictionary containing results and status
            
        Raises:
            AITicketSystemException: If processing fails
        """
        pass
    
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        Should be overridden in subclasses.
        """
        return "You are a helpful AI assistant."
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data format and requirements.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(input_data, dict):
            self.logger.error("Input data must be a dictionary")
            return False
        
        return True
    
    def format_output(self, result: Any, status: str = "success", error: Optional[str] = None) -> Dict[str, Any]:
        """
        Format output in standardized format.
        
        Args:
            result: The main result data
            status: Status of the operation (success, error, partial)
            error: Error message if status is error
            
        Returns:
            Standardized output dictionary
        """
        output = {
            "agent": self.name,
            "status": status,
            "result": result,
            "timestamp": self._get_timestamp()
        }
        
        if error:
            output["error"] = error
            
        return output
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Handle errors in a standardized way.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Standardized error response
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(f"Agent {self.name} error: {error_msg}")
        
        return self.format_output(
            result=None,
            status="error", 
            error=error_msg
        )
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.name}', tools={len(self.tools)})"
