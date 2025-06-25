"""
Application-wide constants for the AI Ticket System.
"""

from enum import Enum
from typing import Dict, Any


# Application Information
APP_NAME = "AI Ticket System"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Professional Enterprise AI-Powered Ticket Management System"

# Database Constants
DEFAULT_DATABASE_PATH = "data/databases/employees.db"
VECTOR_DATABASE_PATH = "data/chroma_db"
BACKUP_DATABASE_PATH = "data/backups"

# Agent Names
class AgentNames:
    MAESTRO = "MaestroAgent"
    HR = "HRAgent"
    DATA_GUARDIAN = "DataGuardianAgent"
    VOCAL_ASSISTANT = "VocalAssistant"

# Workflow States
class WorkflowStates(Enum):
    INITIALIZED = "initialized"
    PROCESSING = "processing"
    WAITING_FOR_INPUT = "waiting_for_input"
    AGENT_PROCESSING = "agent_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Agent Processing Stages
class AgentStages:
    PREPROCESS = "preprocess"
    MAIN_PROCESSING = "main_processing"
    SYNTHESIZE = "synthesize"
    POST_PROCESS = "post_process"

# Ticket Statuses
class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"

# Ticket Priorities
class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

# User Roles
class UserRole(Enum):
    EMPLOYEE = "employee"
    HR_SPECIALIST = "hr_specialist"
    MANAGER = "manager"
    ADMIN = "admin"
    SYSTEM = "system"

# Communication Channels
class CommunicationChannel(Enum):
    CHAT = "chat"
    EMAIL = "email"
    PHONE = "phone"
    VIDEO_CALL = "video_call"
    IN_PERSON = "in_person"

# API Response Codes
class ResponseCodes:
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

# Configuration Keys
class ConfigKeys:
    # LLM Configuration
    LLM_MODEL = "llm_model"
    LLM_TEMPERATURE = "llm_temperature"
    LLM_MAX_TOKENS = "llm_max_tokens"
    
    # Vector Database
    VECTOR_COLLECTION_NAME = "vector_collection_name"
    VECTOR_EMBEDDING_MODEL = "vector_embedding_model"
    VECTOR_SIMILARITY_THRESHOLD = "vector_similarity_threshold"
    
    # Application Settings
    MAX_CONVERSATION_HISTORY = "max_conversation_history"
    SESSION_TIMEOUT = "session_timeout"
    DEFAULT_LANGUAGE = "default_language"
    
    # Logging
    LOG_LEVEL = "log_level"
    LOG_FORMAT = "log_format"
    
    # Security
    JWT_SECRET = "jwt_secret"
    SESSION_SECRET = "session_secret"
    API_RATE_LIMIT = "api_rate_limit"

# Default Configuration Values
DEFAULT_CONFIG: Dict[str, Any] = {
    ConfigKeys.LLM_MODEL: "gpt-4",
    ConfigKeys.LLM_TEMPERATURE: 0.7,
    ConfigKeys.LLM_MAX_TOKENS: 2000,
    ConfigKeys.VECTOR_COLLECTION_NAME: "hr_documents",
    ConfigKeys.VECTOR_EMBEDDING_MODEL: "text-embedding-ada-002",
    ConfigKeys.VECTOR_SIMILARITY_THRESHOLD: 0.7,
    ConfigKeys.MAX_CONVERSATION_HISTORY: 50,
    ConfigKeys.SESSION_TIMEOUT: 3600,  # 1 hour
    ConfigKeys.DEFAULT_LANGUAGE: "en",
    ConfigKeys.LOG_LEVEL: "INFO",
    ConfigKeys.LOG_FORMAT: "json",
    ConfigKeys.API_RATE_LIMIT: 100  # requests per minute
}

# File Extensions and MIME Types
ALLOWED_DOCUMENT_EXTENSIONS = ['.txt', '.md', '.pdf', '.docx', '.doc']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
ALLOWED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.m4a']

MIME_TYPES = {
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp'
}

# API Endpoints
class APIEndpoints:
    # Authentication
    LOGIN = "/api/auth/login"
    LOGOUT = "/api/auth/logout"
    REFRESH = "/api/auth/refresh"
    
    # Users
    USERS = "/api/users"
    USER_PROFILE = "/api/users/profile"
    
    # Tickets
    TICKETS = "/api/tickets"
    TICKET_DETAIL = "/api/tickets/{ticket_id}"
    TICKET_MESSAGES = "/api/tickets/{ticket_id}/messages"
    
    # Workflows
    WORKFLOWS = "/api/workflows"
    WORKFLOW_STATUS = "/api/workflows/{workflow_id}/status"
    
    # Health Check
    HEALTH = "/api/health"
    METRICS = "/api/metrics"

# Error Messages
class ErrorMessages:
    INVALID_INPUT = "Invalid input provided"
    UNAUTHORIZED_ACCESS = "Unauthorized access"
    RESOURCE_NOT_FOUND = "Resource not found"
    INTERNAL_SERVER_ERROR = "Internal server error"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"
    VALIDATION_FAILED = "Data validation failed"
    OPERATION_FAILED = "Operation failed to complete"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions"

# Success Messages
class SuccessMessages:
    OPERATION_COMPLETED = "Operation completed successfully"
    RESOURCE_CREATED = "Resource created successfully"
    RESOURCE_UPDATED = "Resource updated successfully"
    RESOURCE_DELETED = "Resource deleted successfully"
    LOGIN_SUCCESSFUL = "Login successful"
    LOGOUT_SUCCESSFUL = "Logout successful"

# Limits and Constraints
class Limits:
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_MESSAGE_LENGTH = 10000
    MAX_TICKET_TITLE_LENGTH = 200
    MAX_USERNAME_LENGTH = 50
    MAX_EMAIL_LENGTH = 254
    MIN_PASSWORD_LENGTH = 8
    MAX_CONVERSATION_TURNS = 100
    MAX_SEARCH_RESULTS = 50

# Regular Expressions
class RegexPatterns:
    EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE = r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
    USERNAME = r'^[a-zA-Z0-9_]{3,30}$'
    TICKET_ID = r'^TICKET-\d{8}-[A-Z0-9]{6}$'

# Cache Settings
class CacheSettings:
    DEFAULT_TTL = 3600  # 1 hour
    SHORT_TTL = 300     # 5 minutes
    LONG_TTL = 86400    # 24 hours
    CACHE_PREFIX = "ait_system"

# Feature Flags
class FeatureFlags:
    ENABLE_VOICE_INTERFACE = True
    ENABLE_ANALYTICS = True
    ENABLE_NOTIFICATIONS = True
    ENABLE_REAL_TIME_UPDATES = True
    ENABLE_FILE_UPLOADS = True
    ENABLE_API_RATE_LIMITING = True
    ENABLE_AUDIT_LOGGING = True
