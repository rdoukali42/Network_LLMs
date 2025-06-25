"""
Prompts package for all AI system prompts.
Centralized location for all prompt templates and configurations.
"""

from .system_prompts import (
    SYSTEM_PROMPTS,
    WORKFLOW_PROMPTS, 
    RESPONSE_TEMPLATES,
    AGENT_CONFIGS,
    get_system_prompt,
    get_workflow_prompt,
    get_response_template,
    get_agent_config
)

__all__ = [
    'SYSTEM_PROMPTS',
    'WORKFLOW_PROMPTS',
    'RESPONSE_TEMPLATES', 
    'AGENT_CONFIGS',
    'get_system_prompt',
    'get_workflow_prompt',
    'get_response_template',
    'get_agent_config'
]
