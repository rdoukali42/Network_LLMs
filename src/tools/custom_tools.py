"""
Custom tools for agents to use.
"""

from typing import Any, Dict
from langchain.tools import BaseTool
from langfuse import observe


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the web for current information on a given topic"
    
    @observe()
    def _run(self, query: str) -> str:
        # Placeholder implementation
        return f"Web search results for: {query}"
    
    async def _arun(self, query: str) -> str:
        return self._run(query)


class DocumentAnalysisTool(BaseTool):
    name: str = "document_analysis"
    description: str = "Analyze documents for key information and insights"
    
    @observe()
    def _run(self, document: str) -> str:
        # Placeholder implementation
        return f"Analysis of document: {document[:100]}..."
    
    async def _arun(self, document: str) -> str:
        return self._run(document)


class CalculatorTool(BaseTool):
    name: str = "calculator"
    description: str = "Perform mathematical calculations"
    
    @observe()
    def _run(self, expression: str) -> str:
        try:
            # Basic calculator - in production, use a more secure evaluation
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error in calculation: {str(e)}"
    
    async def _arun(self, expression: str) -> str:
        return self._run(expression)
