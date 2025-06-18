"""
MaestroAgent - Query processing and response synthesis agent.
"""

from typing import Dict, Any, List
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langfuse import observe
from .base_agent import BaseAgent


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
2. Reformulate it into clear search queries for finding relevant information, should be concise and focused on the user query
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
            # "confidence level regarding information",
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
