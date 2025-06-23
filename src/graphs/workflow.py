"""
Main workflow module - imports and re-exports the modular workflow components.
This file maintains backward compatibility while delegating to the modular architecture.
"""

# Re-export the main classes and types for backward compatibility
from .workflow_state import WorkflowState
from .workflow_core import MultiAgentWorkflow
from .agent_steps import AgentSteps
from .call_handler import CallHandler
from .redirect_handler import RedirectHandler
from .workflow_utils import WorkflowUtils

# Main exports that external modules expect
__all__ = [
    'WorkflowState',
    'MultiAgentWorkflow',
    'AgentSteps', 
    'CallHandler',
    'RedirectHandler',
    'WorkflowUtils'
]
