"""
Base agent class for all agents in the system.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import observe


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""
    
    def __init__(self, name: str, config: Dict[str, Any] = None, tools: List[BaseTool] = None):
        self.name = name
        self.tools = tools or []
        
        # Initialize LLM if config provided
        if config:
            self.llm = ChatGoogleGenerativeAI(
                model=config['llm']['model'],
                temperature=config['llm']['temperature'],
                google_api_key=os.getenv('GOOGLE_API_KEY')
            )
        else:
            self.llm = None
    
    @abstractmethod
    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with given input."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

