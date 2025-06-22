"""
DataGuardianAgent - Local document search and data verification agent for optimized_project.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langfuse import observe # Assuming Langfuse is kept

from .base_agent import BaseAgent # Import from the new location
# VectorStoreManager will be injected
# from vectorstore.vector_manager import VectorStoreManager # Example

class DataGuardianAgent(BaseAgent):
    """
    Agent specialized in searching local documents and verifying data.
    Requires a VectorStoreManager instance for its operations.
    """

    def __init__(self, agent_config: Dict[str, Any],
                 vector_manager_instance: Any, # Should be an instance of VectorStoreManager
                 project_root_path: Path, # For loading company_scope.md
                 tools: Optional[List[BaseTool]] = None):
        """
        Initializes the DataGuardianAgent.
        Args:
            agent_config: Configuration dictionary for the agent.
            vector_manager_instance: An instance of VectorStoreManager.
            project_root_path: Absolute path to the 'optimized_project' root.
            tools: An optional list of Langchain tools.
        """
        super().__init__(name="DataGuardianAgent", agent_config=agent_config, tools=tools)
        self.vector_manager = vector_manager_instance
        self.project_root = project_root_path

        self.agent_executor: Optional[AgentExecutor] = None
        if self.llm and self.tools: # Check if LLM initialized successfully and tools are provided
            self.agent_executor = self._create_agent_executor()
        elif self.llm and not self.tools:
            # print(f"DataGuardianAgent '{self.name}' initialized without tools. Will use direct LLM calls for analysis.")
            pass
        else:
            print(f"Warning: DataGuardianAgent '{self.name}' LLM not initialized. Agent may not function correctly.")

    def _create_agent_executor(self) -> Optional[AgentExecutor]:
        """Create an agent executor with tools if tools are available."""
        if not self.tools:
            return None
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            return AgentExecutor(agent=agent, tools=self.tools, verbose=self.agent_config.get("verbose_logging", False))
        except Exception as e:
            print(f"⚠️ Failed to create AgentExecutor for DataGuardianAgent: {e}")
            return None

    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Searches local documents and analyzes findings based on the query.
        Args:
            input_data: A dictionary containing:
                - "query": The original user query.
                - "search_queries": Reformulated search queries from Maestro (can be a string or list of strings).
        Returns:
            A dictionary containing the agent's analysis, including scope status,
            information found, confidence, and the raw search results.
        """
        original_query = input_data.get("query", "")
        # search_queries_input can be a single string (from Maestro's direct output) or already a list.
        search_queries_input = input_data.get("search_queries", original_query)

        # Normalize search_queries_input to a list of strings
        if isinstance(search_queries_input, str):
            # If it's a multi-line string of queries, split them. Otherwise, use as is.
            # This simplistic split might need refinement if Maestro's output is more complex.
            processed_search_queries = [q.strip() for q in search_queries_input.split('\n') if q.strip()]
            if not processed_search_queries: # Fallback if split results in empty
                 processed_search_queries = [search_queries_input.strip()]
        elif isinstance(search_queries_input, list):
            processed_search_queries = [str(q).strip() for q in search_queries_input if str(q).strip()]
        else:
            processed_search_queries = [original_query.strip()] # Fallback to original query

        # Ensure there's at least one query to run
        if not any(processed_search_queries):
            processed_search_queries = [original_query.strip()]


        search_results: List[Dict[str, Any]] = []
        documents_found_count = 0

        if not self.vector_manager:
            return {
                "agent": self.name, "status": "error", "error": "VectorStoreManager not available.",
                "result": "SCOPE_STATUS: UNKNOWN\nANSWER_CONFIDENCE: NONE\nINFORMATION_FOUND: NO\n\nVector store not initialized."
            }

        try:
            # print(f"🛡️ DataGuardian searching for: {processed_search_queries}")
            for term in processed_search_queries:
                if term: # Ensure term is not empty
                    # The number of results (k) could be configurable per agent or globally
                    k_results = self.agent_config.get("search_k_results", 3)
                    results_for_term = self.vector_manager.similarity_search(query=term, k=k_results)
                    search_results.extend(results_for_term)

            # Deduplicate results based on content or a unique ID if available in metadata
            unique_search_results = []
            seen_content = set()
            for res in search_results:
                if res.get("content") not in seen_content:
                    unique_search_results.append(res)
                    seen_content.add(res.get("content"))
            search_results = unique_search_results
            documents_found_count = len(search_results)

            company_scope_content = self._get_company_scope_content()

            formatted_docs_str = "No relevant documents found in the local collection."
            if search_results:
                formatted_docs_list = []
                for i, res_item in enumerate(search_results[:5]): # Limit to top 5 for prompt brevity
                    source = res_item.get('metadata', {}).get('source', 'Unknown')
                    score = f"{res_item.get('score', 0.0):.2f}" # Format score
                    formatted_docs_list.append(
                        f"Doc {i+1} (Source: {source}, Relevance: {score}):\n{res_item['content']}\n---"
                    )
                formatted_docs_str = "\n".join(formatted_docs_list)

            analysis_prompt_input = f"""
Original User Query: {original_query}
Search Queries Used: {', '.join(processed_search_queries)}

Company Scope & Capabilities:
{company_scope_content}

Local Document Search Results (Top {min(5, documents_found_count)}):
{formatted_docs_str}

Task:
Based on the Company Scope and Local Document Search Results, analyze the Original User Query.
You MUST start your response with these EXACT headers on separate lines:
SCOPE_STATUS: [WITHIN_SCOPE | OUTSIDE_SCOPE]
INFORMATION_FOUND: [YES | NO | PARTIAL]
ANSWER_CONFIDENCE: [HIGH | MEDIUM | LOW | NONE]

Then, provide a brief analysis explaining your choices for the headers.
- SCOPE_STATUS: Is the query something our company typically handles based on the scope?
- INFORMATION_FOUND: Were relevant documents found for the query?
- ANSWER_CONFIDENCE: Based on the information found, how confident are you in providing a complete answer?

Finally, if INFORMATION_FOUND is YES or PARTIAL, synthesize the key information from the documents that directly addresses the Original User Query. Be concise.
If INFORMATION_FOUND is NO, briefly explain why the documents were not helpful or relevant.
"""
            if not self.llm:
                # Fallback if LLM is not available (e.g. API key issue)
                return {
                    "agent": self.name, "status": "success_no_llm",
                    "result": f"SCOPE_STATUS: UNKNOWN\nINFORMATION_FOUND: {'YES' if documents_found_count > 0 else 'NO'}\nANSWER_CONFIDENCE: NONE\n\nLLM for analysis not available. Found {documents_found_count} documents. Raw results:\n{formatted_docs_str}",
                    "query": original_query, "documents_found": documents_found_count,
                    "raw_search_results": search_results # Provide raw results if no LLM
                }

            # Use direct LLM call for this structured analysis, AgentExecutor might be overkill unless tools are needed here
            response_obj = self.llm.invoke(f"{self.get_system_prompt()}\n\n{analysis_prompt_input}")
            analysis_result_text = response_obj.content

            return {
                "agent": self.name, "status": "success",
                "result": analysis_result_text, # This is the full text including headers and synthesis
                "query": original_query, "documents_found": documents_found_count,
                "raw_search_results": search_results # Optionally include for downstream use
            }

        except Exception as e:
            print(f"Error in DataGuardianAgent run: {e}")
            import traceback
            traceback.print_exc()
            return {
                "agent": self.name, "status": "error", "error": str(e),
                "result": "SCOPE_STATUS: UNKNOWN\nINFORMATION_FOUND: NO\nANSWER_CONFIDENCE: NONE\n\nData Guardian search or analysis failed."
            }

    def _get_company_scope_content(self) -> str:
        """Loads company scope information from a predefined file."""
        # Path is relative to the project root passed during __init__
        scope_file_path = self.project_root / "data" / "raw" / "company_scope.md"
        try:
            if scope_file_path.exists() and scope_file_path.is_file():
                with open(scope_file_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                # print(f"Warning: Company scope file not found at: {scope_file_path}")
                return "Company scope information not available (file missing)."
        except Exception as e:
            print(f"Warning: Error reading company scope file '{scope_file_path}': {e}")
            return "Company scope information not available (read error)."

    def get_system_prompt(self) -> str:
        return """You are Data Guardian, an AI agent responsible for analyzing user queries against company documents and scope.
Your primary tasks are:
1. Determine if a user query falls WITHIN_SCOPE or OUTSIDE_SCOPE of the company's services and expertise.
2. Assess if relevant information to answer the query is found in the provided local document search results (INFORMATION_FOUND: YES, NO, or PARTIAL).
3. Estimate the confidence (ANSWER_CONFIDENCE: HIGH, MEDIUM, LOW, NONE) that a complete answer can be formed from these documents.
4. If information is found, synthesize the key points from the documents that directly address the query.

You MUST begin your response with the three headers: SCOPE_STATUS, INFORMATION_FOUND, and ANSWER_CONFIDENCE, each on a new line, followed by their respective values.
Then, provide a brief justification for your choices and the synthesized information if applicable.
Focus on factual analysis based *only* on the provided company scope and document snippets. Do not infer or use external knowledge.
"""
