"""
Configuration module for the AI Ticket System.
Contains all settings, prompts, and configuration management.
"""

# Configuration components
from .settings import settings, Settings
from .prompts import (
    SYSTEM_PROMPTS, WORKFLOW_PROMPTS, RESPONSE_TEMPLATES, 
    get_system_prompt, get_workflow_prompt, get_response_template
)

__all__ = [
    'settings',
    'Settings',
    'SYSTEM_PROMPTS',
    'WORKFLOW_PROMPTS', 
    'RESPONSE_TEMPLATES',
    'get_system_prompt',
    'get_workflow_prompt',
    'get_response_template'
]
