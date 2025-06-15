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
                # Check if DataGuardian found sufficient answer
                if self._has_sufficient_answer(data_guardian_result):
                    # Second stage: synthesize final response from Data Guardian's findings
                    synthesis_input = f"""
Original Support Ticket: {query}

Data Guardian's Findings: {data_guardian_result}

Based on the local document search results above, please create a comprehensive, helpful response to the support ticket. 

Guidelines:
1. Use the document information as the primary source
2. Provide clear, actionable answers
3. Include source references when using document information
4. Maintain a professional, supportive tone
5. Use calculations if needed (use calculator tool)

Create a complete response that directly addresses the ticket."""
                    
                    if self.agent_executor:
                        print(f"🎭 MaestroAgent synthesizing response from documents for: {query}")
                        result = self.agent_executor.invoke({"input": synthesis_input})
                        return {
                            "agent": self.name,
                            "status": "success", 
                            "result": result.get("output", ""),
                            "query": query,
                            "stage": "synthesize",
                            "source": "documents"
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
                            "stage": "synthesize",
                            "source": "documents"
                        }
                else:
                    # No sufficient answer in documents - route to HR Agent
                    return {
                        "agent": self.name,
                        "status": "route_to_hr",
                        "result": "No sufficient answer found in documents",
                        "query": query,
                        "stage": "route_to_hr"
                    }
                    
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "result": f"Maestro processing failed: {e}"
            }
    
    def _has_sufficient_answer(self, data_guardian_result: str) -> bool:
        """Check if DataGuardian found sufficient answer in documents."""
        if not data_guardian_result or len(data_guardian_result.strip()) < 50:
            return False
        
        # Check for common "no answer" indicators
        no_answer_phrases = [
            "no relevant information",
            "no documents found",
            "no matching documents",
            "cannot find",
            "not found in",
            "no information available",
            "search returned no results",
            "no relevant documents",
            "insufficient to assist",
            "additional resources are required",
            "additional resources required",
            "local documents are completely lacking",
            "documents do not contain information",
            "no information directly answering",
            "confidence level: 0%",
            "gaps in information",
            "local document collection is insufficient",
            "the provided local document chunks",
            "none of them address",
            "completely lacking information",
            "does not contain information",
            # Enhanced detection for DataGuardian's detailed analysis responses
            "none of the provided document chunks contain information",
            "document chunks contain information on",
            "completely lack information",
            "no such information exists in the provided documents",
            "confidence level regarding information",
            "no facts, procedures, or guidance",
            "are irrelevant to the user's query",
            "do not contain any information relevant",
            "focused exclusively on",
            "entirely focused on"
        ]
        
        result_lower = data_guardian_result.lower()
        for phrase in no_answer_phrases:
            if phrase in result_lower:
                return False
        
        return True

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


class HRAgent(BaseAgent):
    """Agent specialized in finding the best employee to handle tickets when documents don't have answers."""
    
    def __init__(self, config: Dict[str, Any] = None, tools: List[BaseTool] = None, availability_tool=None):
        super().__init__("HRAgent", config, tools)
        self.availability_tool = availability_tool
        
        # Create agent executor with tools if available
        if self.llm and self.tools:
            self.agent_executor = self._create_agent_executor()
        else:
            self.agent_executor = None
    
    def _create_agent_executor(self):
        """Create an agent executor with tools."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        except Exception as e:
            print(f"⚠️ Failed to create HR agent executor: {e}")
            return None

    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        
        try:
            print(f"👥 HRAgent finding expert for: {query}")
            
            # Get available employees
            if self.availability_tool:
                available_employees = self.availability_tool.get_available_employees()
            else:
                return {
                    "agent": self.name,
                    "status": "error",
                    "result": "No availability tool configured"
                }
            
            # Find best match
            best_match_data = self._find_best_employee_match(query, available_employees)
            
            if best_match_data:
                return {
                    "agent": self.name,
                    "status": "success",
                    "action": "assign",
                    "employee_data": best_match_data,
                    "result": self._format_employee_recommendation(best_match_data),
                    "query": query
                }
            else:
                return {
                    "agent": self.name,
                    "status": "success",
                    "action": "no_assignment",
                    "result": "No suitable employees available at the moment",
                    "query": query
                }
                
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "result": f"HR Agent failed: {e}"
            }
    
    def _find_best_employee_match(self, query: str, available_employees: Dict) -> Dict:
        """Find the best employee match for the query."""
        # Combine available and busy employees (busy can handle urgent issues)
        candidates = available_employees["available"] + available_employees["busy"]
        
        if not candidates:
            return None
        
        # Simple keyword matching for ticket routing
        query_lower = query.lower()
        
        # Score employees based on relevance
        scored_candidates = []
        for employee in candidates:
            score = 0
            role = employee.get('role_in_company', '').lower()
            expertise = employee.get('expertise', '').lower()
            responsibilities = employee.get('responsibilities', '').lower()
            
            # Score based on keyword matches
            for keyword in query_lower.split():
                if keyword in role:
                    score += 3
                if keyword in expertise:
                    score += 5
                if keyword in responsibilities:
                    score += 2
            
            # Prefer available over busy
            if employee.get('availability_status') == 'Available':
                score += 1
            
            scored_candidates.append((score, employee))
        
        # Sort by score and get best match
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        if scored_candidates[0][0] > 0:  # At least some relevance
            return scored_candidates[0][1]
        else:
            # Return first available if no keyword matches
            if scored_candidates:
                return scored_candidates[0][1]
            return None
    
    def _format_employee_recommendation(self, employee: Dict) -> str:
        """Format employee recommendation for response."""
        status_emoji = {
            'Available': '🟢',
            'Busy': '🟡',
            'In Meeting': '🔴',
            'Do Not Disturb': '🔴'
        }.get(employee.get('availability_status', 'Unknown'), '❓')
        
        return f"""👤 **{employee.get('full_name', 'Unknown')}** (@{employee.get('username', 'unknown')})
🏢 **Role**: {employee.get('role_in_company', 'Not specified')}
💼 **Expertise**: {employee.get('expertise', 'Not specified')}
📋 **Responsibilities**: {employee.get('responsibilities', 'Not specified')}
{status_emoji} **Status**: {employee.get('availability_status', 'Unknown')}

This employee has the expertise to help with your request."""

    def get_system_prompt(self) -> str:
        return """You are HR Agent, specialized in matching support tickets with the most suitable available employees.

Your primary responsibilities:
- Analyze support ticket content to understand required expertise
- Search through available employees based on their roles, expertise, and responsibilities
- Match ticket requirements with employee capabilities
- Consider employee availability status when making recommendations
- Provide clear reasoning for employee recommendations

Key principles:
- Prioritize employees who are Available over those who are Busy
- Match technical expertise to technical problems
- Consider role compatibility with the ticket type
- Always provide the employee's contact information and current status
- Explain why this employee is the best match for the specific ticket

You help ensure every ticket gets routed to the right person, even when our documentation doesn't have the answer."""
