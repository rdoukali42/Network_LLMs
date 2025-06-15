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


class MaestroAgent(BaseAgent):
    """Agent specialized in query processing and response synthesis."""
    
    def __init__(self, config: Dict[str, Any] = None, tools: List[BaseTool] = None):
        super().__init__("MaestroAgent", config, tools)
        
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
        stage = input_data.get("stage", "preprocess")  # preprocess or synthesize
        data_guardian_result = input_data.get("data_guardian_result", "")
        
        try:
            if stage == "preprocess":
                # First stage: process and reformulate the query
                preprocess_input = f"""
Original Support Ticket: {query}

Please analyze this support ticket and:
1. Identify the key question or request
2. Reformulate it into clear search queries for finding relevant information
3. Determine what type of information would best answer this ticket
4. Extract any specific details that should be searched for

Provide clear, search-optimized queries that can be used to find relevant documentation.
"""
                
                if self.agent_executor:
                    print(f"🎭 MaestroAgent preprocessing query: {query}")
                    result = self.agent_executor.invoke({"input": preprocess_input})
                    return {
                        "agent": self.name,
                        "status": "success",
                        "result": result.get("output", ""),
                        "query": query,
                        "stage": "preprocess"
                    }
                else:
                    # Fallback to direct LLM call
                    if not self.llm:
                        return {"agent": self.name, "status": "No LLM configured", "result": query}
                    
                    response = self.llm.invoke(f"{self.get_system_prompt()}\n\n{preprocess_input}")
                    return {
                        "agent": self.name,
                        "status": "success",
                        "result": response.content,
                        "query": query,
                        "stage": "preprocess"
                    }
            
            else:  # stage == "synthesize"
                # Second stage: synthesize final response from Data Guardian's findings
                synthesis_input = f"""
Original Support Ticket: {query}

Data Guardian's Findings: {data_guardian_result}

Based on the local document search results above, please create a comprehensive, helpful response to the support ticket. 

Guidelines:
1. If relevant information was found in local documents, use it as the primary source
2. Provide clear, actionable answers
3. Include source references when using document information
4. If no relevant local information was found, provide general helpful guidance
5. Maintain a professional, supportive tone
6. Use calculations if needed (use calculator tool)

Create a complete response that directly addresses the ticket."""
                
                if self.agent_executor:
                    print(f"🎭 MaestroAgent synthesizing response for: {query}")
                    result = self.agent_executor.invoke({"input": synthesis_input})
                    return {
                        "agent": self.name,
                        "status": "success", 
                        "result": result.get("output", ""),
                        "query": query,
                        "stage": "synthesize"
                    }
                else:
                    # Fallback to direct LLM call
                    if not self.llm:
                        return {"agent": self.name, "status": "No LLM configured", "result": "Synthesis failed"}
                    
                    response = self.llm.invoke(f"{self.get_system_prompt()}\n\n{synthesis_input}")
                    return {
                        "agent": self.name,
                        "status": "success",
                        "result": response.content,
                        "query": query,
                        "stage": "synthesize"
                    }
                    
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "result": f"Maestro processing failed: {e}"
            }

    def get_system_prompt(self) -> str:
        return """You are Maestro, a specialized agent for processing support tickets and synthesizing responses.

Your role has two stages:
1. PREPROCESSING: Analyze support tickets and reformulate them into optimized search queries
2. SYNTHESIS: Take search results from local documents and create comprehensive responses

Available tools:
- calculator: Use this for mathematical calculations when needed

Key responsibilities:
- Understand user intent from support tickets
- Create clear search queries for document retrieval
- Synthesize information from multiple sources into coherent responses
- Provide professional, helpful responses with proper source attribution
- Use calculations when the ticket involves numerical questions

Always be direct, helpful, and professional. Focus on solving the user's specific problem."""


class DataGuardianAgent(BaseAgent):
    """Agent specialized in searching local documents and data verification."""
    
    def __init__(self, config: Dict[str, Any] = None, tools: List[BaseTool] = None, vector_manager=None):
        super().__init__("DataGuardianAgent", config, tools)
        self.vector_manager = vector_manager
        
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
        search_queries = input_data.get("search_queries", "")
        
        try:
            # Search local documents using vector store
            search_results = []
            
            if self.vector_manager and search_queries:
                print(f"🛡️ DataGuardianAgent searching local documents for: {search_queries}")
                
                # Extract search terms from Maestro's reformulated queries
                search_terms = [search_queries]  # Use the reformulated query directly
                
                for search_term in search_terms:
                    if search_term.strip():
                        results = self.vector_manager.similarity_search(search_term.strip(), k=4)
                        search_results.extend(results)
            
            # Format search results for analysis
            if search_results:
                formatted_results = []
                for i, result in enumerate(search_results):
                    formatted_results.append(f"""
Document Chunk {i+1}:
Content: {result['content']}
Source: {result.get('metadata', {}).get('source', 'Unknown')}
Relevance Score: {result.get('score', 'N/A')}
""")
                
                analysis_input = f"""
Original Query: {query}
Maestro's Search Queries: {search_queries}

LOCAL DOCUMENT SEARCH RESULTS:
{''.join(formatted_results)}

Please analyze these search results and:
1. Identify which information directly answers the original query
2. Extract relevant facts, procedures, or guidance from the documents
3. Note any specific sources or references
4. Determine confidence level of the information found
5. Highlight any gaps where local documents don't have the answer

Provide a structured analysis of what information is available locally."""
                
                if self.agent_executor:
                    result = self.agent_executor.invoke({"input": analysis_input})
                    return {
                        "agent": self.name,
                        "status": "success",
                        "result": result.get("output", ""),
                        "query": query,
                        "documents_found": len(search_results)
                    }
                else:
                    # Fallback to direct LLM call
                    if not self.llm:
                        # Return raw search results if no LLM
                        return {
                            "agent": self.name,
                            "status": "success",
                            "result": '\n'.join(formatted_results),
                            "query": query,
                            "documents_found": len(search_results)
                        }
                    
                    response = self.llm.invoke(f"{self.get_system_prompt()}\n\n{analysis_input}")
                    return {
                        "agent": self.name,
                        "status": "success",
                        "result": response.content,
                        "query": query,
                        "documents_found": len(search_results)
                    }
            else:
                # No relevant documents found
                return {
                    "agent": self.name,
                    "status": "success",
                    "result": "No relevant information found in local documents. The query may require general knowledge or information not available in the current document collection.",
                    "query": query,
                    "documents_found": 0
                }
                
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "result": f"Data Guardian search failed: {e}"
            }

    def get_system_prompt(self) -> str:
        return """You are Data Guardian, a specialized agent for searching and verifying information in local documents.

Your primary responsibilities:
- Search through local document collections using vector similarity
- Verify information accuracy against stored documents
- Extract relevant facts, procedures, and guidance from document sources
- Provide source attribution and confidence levels
- Identify gaps where local documents don't contain needed information

Available tools:
- document_analysis: Use this to analyze document content in detail

Key principles:
- Only provide information that can be verified from local documents
- Always cite sources when available
- Be transparent about confidence levels and information gaps
- Focus on factual, explicit information rather than inference
- Clearly distinguish between documented facts and missing information

You are the guardian of data integrity - ensure responses are grounded in actual document content."""
