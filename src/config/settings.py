"""
Centralized application settings and configuration.
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    employees_db_path: str = "data/databases/employees.db"
    chroma_db_path: str = "data/chroma_db"
    backup_path: str = "data/backups"
    connection_timeout: int = 30
    max_connections: int = 10


@dataclass
class LLMConfig:
    """LLM service configuration."""
    provider: str = "openai"  # openai, anthropic, etc.
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    collection_name: str = "company_documents"
    embedding_model: str = "text-embedding-ada-002"
    max_results: int = 10
    similarity_threshold: float = 0.7


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    session_timeout: int = 3600  # 1 hour
    max_login_attempts: int = 3
    password_min_length: int = 8
    require_password_complexity: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    log_file: str = "logs/ai_ticket_system.log"
    error_log_file: str = "logs/errors.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class UIConfig:
    """User interface configuration."""
    app_title: str = "AI Ticket System"
    app_icon: str = "🎫"
    theme: str = "light"
    page_layout: str = "wide"
    show_sidebar: bool = True


class Settings:
    """Main settings class that aggregates all configuration."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.llm = LLMConfig()
        self.vector_store = VectorStoreConfig()
        self.security = SecurityConfig()
        self.logging = LoggingConfig()
        self.ui = UIConfig()
        
        # Load environment overrides
        self._load_from_environment()
        
        # Ensure required directories exist
        self._ensure_directories()
    
    def _load_from_environment(self):
        """Load configuration overrides from environment variables."""
        # Database settings
        if db_path := os.getenv("EMPLOYEES_DB_PATH"):
            self.database.employees_db_path = db_path
        
        if chroma_path := os.getenv("CHROMA_DB_PATH"):
            self.vector_store.collection_name = chroma_path
        
        # LLM settings
        if provider := os.getenv("LLM_PROVIDER"):
            self.llm.provider = provider
        
        if model := os.getenv("LLM_MODEL"):
            self.llm.model = model
        
        if temp := os.getenv("LLM_TEMPERATURE"):
            try:
                self.llm.temperature = float(temp)
            except ValueError:
                pass
        
        # Logging settings
        if log_level := os.getenv("LOG_LEVEL"):
            self.logging.level = log_level.upper()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            Path(self.database.employees_db_path).parent,
            Path(self.database.chroma_db_path),
            Path(self.database.backup_path),
            Path(self.logging.log_file).parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_database_url(self) -> str:
        """Get the database connection URL."""
        return f"sqlite:///{self.database.employees_db_path}"
    
    def get_database_path(self) -> str:
        """Get the database file path without the sqlite:// prefix."""
        return self.database.employees_db_path
    
    @staticmethod
    def extract_database_path(database_url: str) -> str:
        """Extract the file path from a database URL."""
        if database_url.startswith("sqlite:///"):
            return database_url[10:]  # Remove "sqlite:///" prefix
        elif database_url.startswith("sqlite://"):
            return database_url[9:]   # Remove "sqlite://" prefix
        else:
            return database_url  # Already a file path
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys from environment variables."""
        return {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "langfuse_secret_key": os.getenv("LANGFUSE_SECRET_KEY"),
            "langfuse_public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
        }
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Check required API keys
        api_keys = self.get_api_keys()
        if not api_keys.get("openai_api_key") and self.llm.provider == "openai":
            errors.append("OpenAI API key is required when using OpenAI provider")
        
        # Check database paths
        if not Path(self.database.employees_db_path).parent.exists():
            errors.append(f"Database directory does not exist: {Path(self.database.employees_db_path).parent}")
        
        # Check logging directory
        if not Path(self.logging.log_file).parent.exists():
            errors.append(f"Logging directory does not exist: {Path(self.logging.log_file).parent}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "database": self.database.__dict__,
            "llm": self.llm.__dict__,
            "vector_store": self.vector_store.__dict__,
            "security": self.security.__dict__,
            "logging": self.logging.__dict__,
            "ui": self.ui.__dict__,
        }
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value by key name.
        
        Args:
            key: Setting key (e.g., "OPENAI_API_KEY", "llm.temperature")
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        # Handle environment variables directly
        if key.isupper() and "_" in key:
            return os.getenv(key, default)
        
        # Handle dotted notation (e.g., "llm.temperature")
        if "." in key:
            section, setting = key.split(".", 1)
            if hasattr(self, section):
                section_obj = getattr(self, section)
                if hasattr(section_obj, setting):
                    return getattr(section_obj, setting)
        
        # Handle direct attribute access
        if hasattr(self, key):
            return getattr(self, key)
        
        # Return default if not found
        return default
    
    @property
    def is_production(self) -> bool:
        """Check if the application is running in production mode."""
        env = os.getenv("ENVIRONMENT", "development").lower()
        return env in ["production", "prod"]


# Global settings instance
settings = Settings()
