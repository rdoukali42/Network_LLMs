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
    
    def __init__(self, settings=None, tools: List[BaseTool] = None):
        super().__init__("MaestroAgent", settings, tools)
        
        # Create agent executor with tools if available
        llm = self.get_llm()
        if llm and self.tools:
            self.agent_executor = self._create_agent_executor()
        else:
            self.agent_executor = None
    
    def _create_agent_executor(self):
        """Create an agent executor with tools."""
        try:
            llm = self.get_llm()
            if not llm:
                return None
                
            # Create a simple prompt for tool-enabled agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            # Create tool-calling agent
            agent = create_tool_calling_agent(llm, self.tools, prompt)
            return AgentExecutor(agent=agent, tools=self.tools, verbose=False)
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
2. Reformulate it into clear search queries for finding relevant information, should be concise and focused on the user query, using keywords and phrases
3. Determine what type of information would best answer this ticket
4. Extract any specific details that should be searched for

Provide clear, search-optimized queries that can be used to find relevant documentation.
"""
                
                if self.agent_executor:
                    # print(f"🎭 MaestroAgent preprocessing query: {query}")
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
                    llm = self.get_llm()
                    if not llm:
                        return {"agent": self.name, "status": "No LLM configured", "result": query}
                    
                    response = llm.invoke(f"{self.get_system_prompt()}\n\n{preprocess_input}")
                    return {
                        "agent": self.name,
                        "status": "success",
                        "result": response.content,
                        "query": query,
                        "stage": "preprocess"
                    }
            elif stage == "final_review":
                final_review_prompt = f"""
Please review and format the following solution into a brief, professional email-style response:

{query}

Use this exact format:

Subject: Re: [TICKET SUBJECT]

Hi [USER NAME],

Thanks for your request. [Brief summary of the solution]. [Key solution points in 1-2 sentences].

[Any additional steps or contact information].

This solution was coordinated by Anna, our Support Specialist.

Best,
Support Team

Keep the response under 150 words and focus on the actual solution, not internal processes.
"""
                llm = self.get_llm()
                response = llm.invoke(final_review_prompt)
                return {
                    "agent": self.name,
                    "status": "success",
                    "result": response.content,
                    "query": query,
                    "stage": "final_review"
                } 
            else:  # stage == "synthesize"
                # Check if DataGuardian found sufficient answer
                answer_check = self._has_sufficient_answer(data_guardian_result)
                
                if answer_check == "OUTSIDE_SCOPE":
                    # Query is outside company scope - end workflow here
                    print(f"            🎭 Query is OUTSIDE COMPANY SCOPE - ending workflow")
                    return {
                        "agent": self.name,
                        "status": "outside_scope",
                        "result": "This request is outside our company's scope of services. We focus on IT support, software development, and related technical services. Please contact the appropriate service provider for this type of request.",
                        "query": query,
                        "stage": "outside_scope_termination"
                    }
                
                elif answer_check:  # True - sufficient answer found
                    print(f"            🎭 DataGuardian Found Relevant Infos")
                    # Second stage: synthesize final response from Data Guardian's findings
                    synthesis_input = f"""
Original Support Ticket: {query}

Data Guardian's Findings: {data_guardian_result}

Based on the local document search results above, please create a brief, professional email-style response using this exact format:

Subject: Re: [TICKET SUBJECT]

Hi [USER NAME],

Thanks for your question. [Brief summary of the answer from the documents]. [Key information from the findings in 1-2 sentences].

[Any additional helpful information or next steps if relevant].

This solution was provided by Anna, our Support Specialist.

Best,
Support Team

Guidelines:
1. Keep response under 150 words total
2. Use document information as the primary source
3. Focus on answering the user's question directly
4. Maintain professional, email-like tone
5. Do not include internal processes or system details

Create a complete email response that directly addresses the ticket."""
                    
                    if self.agent_executor:
                        # print(f"🎭 MaestroAgent synthesizing response from documents for: {query}")
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
                        llm = self.get_llm()
                        if not llm:
                            return {"agent": self.name, "status": "No LLM configured", "result": "Synthesis failed"}
                        
                        response = llm.invoke(f"{self.get_system_prompt()}\n\n{synthesis_input}")
                        return {
                            "agent": self.name,
                            "status": "success",
                            "result": response.content,
                            "query": query,
                            "stage": "synthesize",
                            "source": "documents"
                        }
                else:  # False - no sufficient answer, route to HR
                    print(f"            🎭 DataGuardian Didn't found relevant infos - routing to HR")
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
    
    def _parse_data_guardian_response(self, response: str) -> Dict[str, str]:
        """Parse structured DataGuardian response."""
        lines = response.strip().split('\n')
        parsed = {}
        
        # Look for structured headers in first few lines
        for line in lines[:5]:  # Check first 5 lines for headers 
            if ':' in line:
                key, value = line.split(':', 1)
                key_clean = key.strip().upper()
                value_clean = value.strip().upper()
                
                if key_clean in ['SCOPE_STATUS', 'ANSWER_CONFIDENCE', 'INFORMATION_FOUND']:
                    parsed[key_clean.lower()] = value_clean
        
        return parsed

    def _fallback_answer_check(self, data_guardian_result: str) -> bool:
        """Fallback method that looks for information_found value instead of sentences."""
        result_lower = data_guardian_result.lower()
        
        # Only look for information_found: YES (strict)
        if 'information_found:' in result_lower:
            # Extract the value after information_found:
            lines = data_guardian_result.split('\n')
            for line in lines:
                if 'information_found:' in line.lower():
                    value = line.split(':', 1)[1].strip().upper()
                    return value == 'YES'  # Only YES, not PARTIAL
        
        # If no structured information_found field found, return False
        return False

    def _has_sufficient_answer(self, data_guardian_result: str):
        """Check if DataGuardian found sufficient answer in documents."""
        if not data_guardian_result or len(data_guardian_result.strip()) < 50:
            return False
        
        # Parse structured response from DataGuardian
        parsed_response = self._parse_data_guardian_response(data_guardian_result)
        
        # If query is outside company scope, return special status
        if parsed_response.get('scope_status') == 'OUTSIDE_SCOPE':
            return "OUTSIDE_SCOPE"
        
        # Check if we have structured information_found value
        information_found = parsed_response.get('information_found', '').upper()
        
        if information_found:
            # Use structured value if available - ONLY YES is sufficient
            if information_found == 'YES':
                return True
            else:
                # NO, PARTIAL, or any other value = insufficient
                return False
        
        # Fallback to strict value-based checking (only information_found: YES)
        return self._fallback_answer_check(data_guardian_result)

    def get_system_prompt(self) -> str:
        return """You are Maestro, a specialized agent for processing support tickets and synthesizing responses.

Your role has two stages:
1. PREPROCESSING: Analyze support tickets and reformulate them into optimized search queries
2. SYNTHESIS: Take search results from local documents and create brief, professional email-style responses

Key responsibilities:
- Understand user intent from support tickets
- Create clear search queries for document retrieval
- Synthesize information from multiple sources into concise email responses
- Provide professional, helpful responses in email format under 150 words
- Focus on actual solutions, not internal processes

Email format template:
Subject: Re: [TICKET SUBJECT]
Hi [USER NAME],
[Brief solution summary]
This solution was [provided by/coordinated by] [Agent/Employee name].
Best,
Support Team

Always be direct, helpful, and professional. Focus on solving the user's specific problem concisely."""
