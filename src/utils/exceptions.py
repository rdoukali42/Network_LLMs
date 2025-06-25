"""
Custom exception classes for the AI Ticket System.
"""


class AITicketSystemException(Exception):
    """Base exception class for all AI Ticket System errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or "GENERIC_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ValidationError(AITicketSystemException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": value})


class BusinessLogicError(AITicketSystemException):
    """Raised when business logic rules are violated."""
    
    def __init__(self, message: str, rule: str = None, context: dict = None):
        super().__init__(message, "BUSINESS_LOGIC_ERROR", {"rule": rule, "context": context or {}})


class ServiceError(AITicketSystemException):
    """Raised when service operations fail."""
    
    def __init__(self, message: str, service_name: str = None, operation: str = None):
        super().__init__(message, "SERVICE_ERROR", {"service": service_name, "operation": operation})


class AgentError(AITicketSystemException):
    """Raised when agent operations fail."""
    
    def __init__(self, message: str, agent_name: str = None, stage: str = None):
        super().__init__(message, "AGENT_ERROR", {"agent": agent_name, "stage": stage})


class DatabaseError(AITicketSystemException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        super().__init__(message, "DATABASE_ERROR", {"operation": operation, "table": table})


class IntegrationError(AITicketSystemException):
    """Raised when external service integration fails."""
    
    def __init__(self, message: str, service: str = None, endpoint: str = None):
        super().__init__(message, "INTEGRATION_ERROR", {"service": service, "endpoint": endpoint})


class ConfigurationError(AITicketSystemException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIGURATION_ERROR", {"config_key": config_key})


class WorkflowError(AITicketSystemException):
    """Raised when workflow execution fails."""
    
    def __init__(self, message: str, workflow_stage: str = None, workflow_id: str = None):
        super().__init__(message, "WORKFLOW_ERROR", {"stage": workflow_stage, "workflow_id": workflow_id})


class AuthenticationError(AITicketSystemException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, user_id: str = None):
        super().__init__(message, "AUTHENTICATION_ERROR", {"user_id": user_id})


class AuthorizationError(AITicketSystemException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str, user_id: str = None, resource: str = None):
        super().__init__(message, "AUTHORIZATION_ERROR", {"user_id": user_id, "resource": resource})


class EventError(AITicketSystemException):
    """Raised when event operations fail."""
    
    def __init__(self, message: str, event_type: str = None, handler: str = None):
        super().__init__(message, "EVENT_ERROR", {"event_type": event_type, "handler": handler})


class LLMError(AITicketSystemException):
    """Raised when LLM operations fail."""
    
    def __init__(self, message: str, model: str = None, provider: str = None):
        super().__init__(message, "LLM_ERROR", {"model": model, "provider": provider})


class VectorError(AITicketSystemException):
    """Raised when vector database operations fail."""
    
    def __init__(self, message: str, collection: str = None, operation: str = None):
        super().__init__(message, "VECTOR_ERROR", {"collection": collection, "operation": operation})
