"""
Base service class providing common functionality for all services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from utils.logging_config import get_logger
from utils.exceptions import ServiceError, ValidationError


class BaseService(ABC):
    """
    Abstract base class for all services in the system.
    
    Provides common functionality like logging, error handling,
    validation, and standardized patterns.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the base service."""
        self.name = name
        self.config = config or {}
        self.logger = get_logger(f"service.{name}")
        
        self.logger.info(f"Initializing {name} service")
        self._initialize()
    
    def _initialize(self):
        """Initialize service-specific components. Override in subclasses."""
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Return the service name. Must be implemented by subclasses."""
        pass
    
    def validate_input(self, data: Dict[str, Any], required_fields: Optional[list] = None) -> bool:
        """
        Validate input data.
        
        Args:
            data: Input data to validate
            required_fields: List of required field names
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("Input data must be a dictionary")
        
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(f"Missing required fields: {missing_fields}")
        
        return True
    
    def create_response(self, 
                       data: Any, 
                       status: str = "success", 
                       message: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create standardized service response.
        
        Args:
            data: The response data
            status: Response status (success, error, partial)
            message: Optional message
            metadata: Optional metadata
            
        Returns:
            Standardized response dictionary
        """
        response = {
            "service": self.get_service_name(),
            "status": status,
            "data": data,
            "timestamp": self._get_timestamp()
        }
        
        if message:
            response["message"] = message
            
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Handle service errors in a standardized way.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            Standardized error response
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(f"Service {self.name} error: {error_msg}")
        
        return self.create_response(
            data=None,
            status="error",
            message=error_msg
        )
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _log_operation(self, operation: str, data: Optional[Dict[str, Any]] = None):
        """Log service operations."""
        if data:
            self.logger.info(f"Service {self.name} - {operation}: {data}")
        else:
            self.logger.info(f"Service {self.name} - {operation}")
    
    def __str__(self) -> str:
        """String representation of the service."""
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the service."""
        return f"{self.__class__.__name__}(name='{self.name}', config_keys={list(self.config.keys())})"
