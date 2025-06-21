"""
DataGuardianAgent - Local document search and data verification agent.
"""

from typing import Dict, Any, List
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langfuse import observe
from .base_agent import BaseAgent


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
            return AgentExecutor(agent=agent, tools=self.tools, verbose=False)
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
                # print(f"            🛡️ DataGuardianAgent searching local documents for: {search_queries}")
                
                # Extract search terms from Maestro's reformulated queries
                search_terms = [search_queries]  # Use the reformulated query directly
                
                for search_term in search_terms:
                    if search_term.strip():
                        results = self.vector_manager.similarity_search(search_term.strip(), k=4)
                        search_results.extend(results)
            
            # Load company scope directly (always relevant)
            company_scope = self._get_company_scope()
            
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

IMPORTANT: You MUST start your response with these exact headers:

SCOPE_STATUS: [WITHIN_SCOPE | OUTSIDE_SCOPE]
ANSWER_CONFIDENCE: [HIGH | MEDIUM | LOW | NONE]
INFORMATION_FOUND: [YES | NO | PARTIAL]

Then provide your detailed analysis below.

EXAMPLE RESPONSE FORMAT:
SCOPE_STATUS: WITHIN_SCOPE
ANSWER_CONFIDENCE: HIGH
INFORMATION_FOUND: YES

Based on our company policies, the harassment reporting procedure is...

LOCAL DOCUMENT SEARCH RESULTS:
{''.join(formatted_results)}

COMPANY SCOPE AND CAPABILITIES:
{company_scope}

Please analyze the company scope and local documents to determine:
1. Is this query within the company's scope of work and capabilities?
2. Can this query be answered using available local documents?
3. Can at least one employee handle this request based on their expertise?

If the query is outside company scope (like fixing household appliances, legal advice unrelated to IT, etc.), respond explicitly with 'Outside Company Scope'.
If the query is within scope but cannot be answered from documents, proceed to analyze available information.

Analysis steps:
1. Identify which information directly answers the original query
2. Extract relevant facts, procedures, or guidance from the documents
3. Note any specific sources or references
4. Determine confidence level of the information found
5. Highlight any gaps where local documents don't have the answer
6. If no relevant information is found, clearly mention 'no relevant information'

Provide a structured analysis of what information is available locally."""
                # print(f"❌ ❌ ❌ ❌ ❌ ❌ ❌ Document Chunck : {i+1} \n {result['content']} \n Source: {result.get('metadata', {}).get('source', 'Unknown')} \n Relevance Score: {result.get('score', 'N/A')}")
                # print(f"🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️🛡️ LOCAL DOCUMENT SEARCH RESULTS: {''.join(formatted_results)}")
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
                        # Return structured format even without LLM
                        return {
                            "agent": self.name,
                            "status": "success",
                            "result": f"SCOPE_STATUS: WITHIN_SCOPE\nANSWER_CONFIDENCE: LOW\nINFORMATION_FOUND: PARTIAL\n\nFound {len(search_results)} document(s) but cannot analyze without LLM configuration:\n\n" + '\n'.join(formatted_results),
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
                # No relevant documents found, but still analyze with company scope
                company_scope = self._get_company_scope()
                
                analysis_input = f"""
Original Query: {query}
Maestro's Search Queries: {search_queries}

IMPORTANT: You MUST start your response with these exact headers:

SCOPE_STATUS: [WITHIN_SCOPE | OUTSIDE_SCOPE]
ANSWER_CONFIDENCE: [HIGH | MEDIUM | LOW | NONE]
INFORMATION_FOUND: [YES | NO | PARTIAL]

Then provide your detailed analysis below.

EXAMPLE RESPONSE FORMAT:
SCOPE_STATUS: OUTSIDE_SCOPE
ANSWER_CONFIDENCE: NONE
INFORMATION_FOUND: NO

This query is outside our company's scope of work...

LOCAL DOCUMENT SEARCH RESULTS:
No relevant documents found in the local document collection.

COMPANY SCOPE AND CAPABILITIES:
{company_scope}

Based on the company scope and capabilities above:
1. Is this query within the company's scope of work and expertise?
2. Can at least one employee handle this request based on their skills?
3. If outside company scope (like household repairs, legal advice unrelated to IT), respond with 'Outside Company Scope'.
4. If within scope but no local documents available, indicate that additional resources or direct employee consultation is required.

Provide analysis of whether this query aligns with company capabilities."""
                
                if self.agent_executor:
                    result = self.agent_executor.invoke({"input": analysis_input})
                    return {
                        "agent": self.name,
                        "status": "success",
                        "result": result.get("output", ""),
                        "query": query,
                        "documents_found": 0
                    }
                else:
                    if not self.llm:
                        return {
                            "agent": self.name,
                            "status": "success",
                            "result": "SCOPE_STATUS: WITHIN_SCOPE\nANSWER_CONFIDENCE: NONE\nINFORMATION_FOUND: NO\n\nNo relevant information found in local documents. The query may require general knowledge or information not available in the current document collection.",
                            "query": query,
                            "documents_found": 0
                        }
                    
                    response = self.llm.invoke(f"{self.get_system_prompt()}\n\n{analysis_input}")
                    return {
                        "agent": self.name,
                        "status": "success",
                        "result": response.content,
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
        

    def _get_company_scope(self) -> str:
        """Load company scope directly from file (small, always relevant)."""
        try:
            import os
            scope_file = os.path.join("data", "raw", "company_scope.md")
            if os.path.exists(scope_file):
                with open(scope_file, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                print(f"⚠️ Company scope file not found at: {scope_file}")
                return "Company scope information not available."
        except Exception as e:
            print(f"⚠️ Error reading company scope file: {e}")
            return "Company scope information not available."

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

