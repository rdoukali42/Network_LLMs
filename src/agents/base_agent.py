"""
Base agent class and example implementations.
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


class ResearchAgent(BaseAgent):
    """Agent specialized in research and information gathering."""
    
    def __init__(self, config: Dict[str, Any] = None, tools: List[BaseTool] = None):
        super().__init__("ResearchAgent", config, tools)
        
        # Create agent executor with tools if available
        if self.llm and self.tools:
            self.agent_executor = self._create_agent_executor()
        else:
            self.agent_executor = None
    
    def _create_agent_executor(self):
        """Create an agent executor with tools."""
        try:
            # Create a simple prompt for tool-enabled agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            # Create tool-calling agent
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        except Exception as e:
            print(f"⚠️ Failed to create agent executor: {e}")
            return None

    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        
        try:
            # Use agent executor with tools if available
            if self.agent_executor:
                print(f"🔍 ResearchAgent using tools for: {query}")
                result = self.agent_executor.invoke({"input": query})
                return {
                    "agent": self.name,
                    "status": "success",
                    "result": result.get("output", ""),
                    "query": query
                }
            else:
                # Fallback to direct LLM call
                print(f"🔍 ResearchAgent using LLM only for: {query}")
                if not self.llm:
                    return {"agent": self.name, "status": "No LLM configured", "result": "Research placeholder"}
                
                research_prompt = f"""
        {self.get_system_prompt()}
        
        Research Topic: {query}
        
        Please provide comprehensive research on this topic. Include:
        1. Key facts and information
        2. Current trends or developments  
        3. Relevant statistics or data
        4. Multiple perspectives if applicable
        
        Answer directly and be comprehensive but concise.
        """
                
                response = self.llm.invoke(research_prompt)
                return {
                    "agent": self.name,
                    "status": "success",
                    "result": response.content,
                    "query": query
                }
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "result": f"Research failed: {e}"
            }

    def get_system_prompt(self) -> str:
        return """You are a research agent specialized in gathering and analyzing information.
        Your role is to provide comprehensive, accurate information on requested topics.
        
        Available tools:
        - calculator: Use this for mathematical calculations
        - document_analysis: Use this to analyze documents for insights
        
        Focus on facts, data, and reliable information. Answer questions directly and thoroughly.
        Use your extensive knowledge base to provide comprehensive answers.
        Do not ask for clarification - provide the best research you can based on the given topic."""


class AnalysisAgent(BaseAgent):
    """Agent specialized in data analysis and synthesis."""
    
    def __init__(self, config: Dict[str, Any] = None, tools: List[BaseTool] = None):
        super().__init__("AnalysisAgent", config, tools)
        
        # Create agent executor with tools if available
        if self.llm and self.tools:
            self.agent_executor = self._create_agent_executor()
        else:
            self.agent_executor = None
    
    def _create_agent_executor(self):
        """Create an agent executor with tools."""
        try:
            # Create a simple prompt for tool-enabled agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            # Create tool-calling agent
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        except Exception as e:
            print(f"⚠️ Failed to create agent executor: {e}")
            return None

    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        research_result = input_data.get("research_result", "")
        
        try:
            # Prepare input for analysis
            analysis_input = f"""
Original Question: {query}
Research Information: {research_result}

Based on the research provided, please analyze and provide:
1. Key insights and conclusions
2. Calculations if numbers are involved (use calculator tool if needed)
3. Practical implications
4. Clear, actionable recommendations

If the question asks for calculations, show your work step by step.
"""
            
            # Use agent executor with tools if available
            if self.agent_executor:
                print(f"🔬 AnalysisAgent using tools for: {query}")
                result = self.agent_executor.invoke({"input": analysis_input})
                return {
                    "agent": self.name,
                    "status": "success",
                    "result": result.get("output", ""),
                    "query": query
                }
            else:
                # Fallback to direct LLM call
                print(f"🔬 AnalysisAgent using LLM only for: {query}")
                if not self.llm:
                    return {"agent": self.name, "status": "No LLM configured", "result": "Analysis placeholder"}
                
                analysis_prompt = f"""
        {self.get_system_prompt()}
        
        {analysis_input}
        """
                
                response = self.llm.invoke(analysis_prompt)
                return {
                    "agent": self.name,
                    "status": "success", 
                    "result": response.content,
                    "query": query
                }
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "result": f"Analysis failed: {e}"
            }
    
    def get_system_prompt(self) -> str:
        return """You are an analysis agent specialized in synthesizing information and drawing insights.
        Your role is to analyze data, identify patterns, and provide meaningful conclusions.
        Focus on providing clear analysis, calculations, and actionable insights.
        When you need to perform calculations, use the calculator tool.
        Answer directly based on the information provided - do not ask for clarification."""
