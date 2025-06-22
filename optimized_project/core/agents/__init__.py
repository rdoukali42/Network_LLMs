# Makes 'agents' a package to group all agent definitions.

from .base_agent import BaseAgent
from .maestro_agent import MaestroAgent
from .data_guardian_agent import DataGuardianAgent
from .hr_agent import HRAgent
from .vocal_assistant_agent import VocalAssistantAgent

__all__ = [
    "BaseAgent",
    "MaestroAgent",
    "DataGuardianAgent",
    "HRAgent",
    "VocalAssistantAgent"
]
