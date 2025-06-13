"""
Base agent class and example implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from langfuse import observe


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""
    
    def __init__(self, name: str, tools: List[BaseTool] = None):
        self.name = name
        self.tools = tools or []
    
    @abstractmethod
    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with given input."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass


class ResearchAgent(BaseAgent):
    """Agent specialized in research and information gathering."""
    
    def __init__(self, tools: List[BaseTool] = None):
        super().__init__("ResearchAgent", tools)
    
    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation will be added
        return {"agent": self.name, "status": "placeholder"}
    
    def get_system_prompt(self) -> str:
        return """You are a research agent specialized in gathering and analyzing information.
        Your role is to search through available knowledge sources and provide comprehensive,
        accurate information on requested topics."""


class AnalysisAgent(BaseAgent):
    """Agent specialized in data analysis and synthesis."""
    
    def __init__(self, tools: List[BaseTool] = None):
        super().__init__("AnalysisAgent", tools)
    
    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation will be added
        return {"agent": self.name, "status": "placeholder"}
    
    def get_system_prompt(self) -> str:
        return """You are an analysis agent specialized in synthesizing information and drawing insights.
        Your role is to analyze data, identify patterns, and provide meaningful conclusions."""
