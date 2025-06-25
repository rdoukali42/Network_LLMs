"""
Base agent class for all agents in the system.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langfuse import observe
from integrations.llm_client import LLMClient


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""
    
    def __init__(self, name: str, settings=None, tools: List[BaseTool] = None, llm_client: Optional[LLMClient] = None):
        self.name = name
        self.tools = tools or []
        self.settings = settings
        
        # Use centralized LLM client or create a new one
        if llm_client:
            self.llm_client = llm_client
        elif settings:
            self.llm_client = LLMClient(settings)
        else:
            # Fallback to None - agents should handle this case
            self.llm_client = None
    
    def get_llm(self):
        """Get LLM instance from the centralized client."""
        if self.llm_client:
            return self.llm_client.get_llm("gemini-1.5-flash")  # Updated to current model
        return None
    
    @abstractmethod
    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with given input."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

