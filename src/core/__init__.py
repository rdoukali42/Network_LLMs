"""
Core module for the AI Ticket System.
Contains the main business logic and orchestration components.
"""

__version__ = "2.0.0"
__author__ = "AI Ticket System Team"

# Base classes
from .base_agent import BaseAgent
from .base_service import BaseService
from .base_repository import BaseRepository

# Core components (to be implemented)
# from .workflow_engine import WorkflowEngine
# from .agent_manager import AgentManager  
# from .state_manager import StateManager

__all__ = [
    'BaseAgent',
    'BaseService', 
    'BaseRepository',
    # 'WorkflowEngine',
    # 'AgentManager', 
    # 'StateManager'
]
