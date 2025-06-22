"""
MaestroAgent - Query processing and response synthesis agent for optimized_project.
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langfuse import observe # Assuming Langfuse is kept

from .base_agent import BaseAgent # Import from the new location

class MaestroAgent(BaseAgent):
    """
    Agent specialized in query processing, response synthesis, and final review.
    """

    def __init__(self, agent_config: Dict[str, Any], tools: Optional[List[BaseTool]] = None):
        """
        Initializes the MaestroAgent.
        Args:
            agent_config: Configuration dictionary for the agent, including LLM settings.
            tools: An optional list of Langchain tools.
        """
        super().__init__(name="MaestroAgent", agent_config=agent_config, tools=tools)

        self.agent_executor: Optional[AgentExecutor] = None
        if self.llm and self.tools: # Check if LLM initialized successfully and tools are provided
            self.agent_executor = self._create_agent_executor()
        elif self.llm and not self.tools:
            # print(f"MaestroAgent '{self.name}' initialized without tools. Will use direct LLM calls.")
            pass # No executor if no tools
        else:
            print(f"Warning: MaestroAgent '{self.name}' LLM not initialized. Agent may not function correctly.")

    def _create_agent_executor(self) -> Optional[AgentExecutor]:
        """Create an agent executor with tools if tools are available."""
        if not self.tools: # Should not happen if called from __init__ logic, but defensive
            return None
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()), # System prompt defined in this class
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])

            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            return AgentExecutor(agent=agent, tools=self.tools, verbose=self.agent_config.get("verbose_logging", False))
        except Exception as e:
            print(f"⚠️ Failed to create AgentExecutor for MaestroAgent: {e}")
            return None

    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the MaestroAgent based on the provided input data and stage.
        Args:
            input_data: A dictionary containing:
                - "query": The user's query or relevant text.
                - "stage": The processing stage ("preprocess", "synthesize", "final_review").
                - "data_guardian_result": (Optional) Result from DataGuardianAgent for synthesis.
        Returns:
            A dictionary containing the agent's output.
        """
        query = input_data.get("query", "")
        stage = input_data.get("stage", "preprocess")
        data_guardian_result = input_data.get("data_guardian_result", "")

        if not self.llm:
            return {
                "agent": self.name, "status": "error", "error": "LLM not configured for MaestroAgent",
                "result": "MaestroAgent LLM not available."
            }

        try:
            if stage == "preprocess":
                prompt_input = f"""
Original Support Ticket: {query}

Analyze this support ticket and perform the following:
1. Identify the core question or issue.
2. Reformulate it into 1-3 concise, keyword-focused search queries suitable for a vector database search.
3. Briefly state the type of information needed to answer this ticket (e.g., "technical steps", "policy information", "employee contact").
4. List any specific entities (names, product versions, error codes) mentioned that are crucial for the search.

Output format should be:
Search Queries:
- [Query 1]
- [Query 2]
Information Type: [Type]
Critical Entities: [Entity 1, Entity 2]
"""
                result_key = "preprocessed_query_details"

            elif stage == "synthesize":
                answer_check_status = self._has_sufficient_answer_from_dg(data_guardian_result)

                if answer_check_status == "OUTSIDE_SCOPE":
                    return {
                        "agent": self.name, "status": "outside_scope",
                        "result": "This request appears to be outside the company's primary scope of IT support and software services. Please clarify or contact an appropriate provider.",
                        "query": query, "stage": "synthesis_aborted_outside_scope"
                    }

                elif answer_check_status == "SUFFICIENT_ANSWER":
                    prompt_input = f"""
Original Support Ticket: {query}
Data Guardian's Search Findings: {data_guardian_result}

Synthesize a comprehensive and helpful response to the support ticket using ONLY the information from Data Guardian's Findings.
Follow these guidelines:
- Directly address the user's original query.
- If the findings provide a clear answer, present it clearly.
- If the findings include steps, list them.
- If specific documents were cited by Data Guardian (e.g., with source metadata), mention the relevant document source if it adds credibility, but focus on the information itself.
- Maintain a professional and supportive tone.
- Do NOT invent information not present in the findings. If the findings are insufficient, state that a clear answer could not be constructed from the provided documents.
"""
                    result_key = "synthesis_result"
                    return_status = "success"
                else: # "INSUFFICIENT_ANSWER" or other
                    return {
                        "agent": self.name, "status": "route_to_hr",
                        "result": "The initial document search did not yield a conclusive answer. Further assistance may be required.",
                        "query": query, "stage": "synthesis_insufficient_data"
                    }

            elif stage == "final_review": # For voice call solution review
                # Input 'query' for this stage is expected to be a structured prompt
                # including original ticket, conversation, and employee solution.
                prompt_input = query
                result_key = "final_reviewed_solution"

            elif stage == "format_hr_referral": # New stage for consistent HR referral formatting
                employee_details = input_data.get("employee_details_for_referral", "an available expert")
                original_ticket_summary = input_data.get("original_ticket_summary", query)
                prompt_input = f"""
The system has identified {employee_details} as a suitable contact for the issue: "{original_ticket_summary}".
Please craft a brief, polite message to the user, informing them that their query requires specialized assistance and they should contact the identified expert/department.
Mention the nature of the query briefly. Do not promise the expert will proactively contact them.
Example: "For your query regarding '{original_ticket_summary}', we recommend contacting {employee_details} who can provide specialized assistance."
"""
                result_key = "formatted_hr_referral"

            else:
                return {"agent": self.name, "status": "error", "error": f"Unknown stage: {stage}", "result": ""}

            # Execute with AgentExecutor if available and tools might be relevant, else direct LLM
            if self.agent_executor and stage in ["synthesize"]: # Example: only synthesis might use calculator
                # print(f"🎭 MaestroAgent ({stage}) using AgentExecutor for: {query[:50]}...")
                response_obj = self.agent_executor.invoke({"input": prompt_input})
                output = response_obj.get("output", "")
            else:
                # print(f"🎭 MaestroAgent ({stage}) using direct LLM call for: {query[:50]}...")
                response_obj = self.llm.invoke(f"{self.get_system_prompt(stage)}\n\n{prompt_input}")
                output = response_obj.content

            return {
                "agent": self.name, "status": return_status if stage == "synthesize" else "success",
                "result": output, result_key: output, "query": query, "stage": stage
            }

        except Exception as e:
            print(f"Error in MaestroAgent run (stage: {stage}): {e}")
            import traceback
            traceback.print_exc()
            return {
                "agent": self.name, "status": "error", "error": str(e),
                "result": f"MaestroAgent processing failed at stage {stage}."
            }

    def _parse_structured_dg_response(self, dg_response_text: str) -> Dict[str, str]:
        """Parses key-value pairs from Data Guardian's text response if structured."""
        parsed: Dict[str, str] = {}
        # Example expected keys: SCOPE_STATUS, INFORMATION_FOUND, ANSWER_CONFIDENCE
        # This is a simplified parser. Robust parsing might use regex or more specific delimiters.
        for line in dg_response_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key_clean = key.strip().upper().replace(" ", "_") # e.g., "SCOPE STATUS" -> "SCOPE_STATUS"
                value_clean = value.strip().upper()
                if key_clean in ['SCOPE_STATUS', 'INFORMATION_FOUND', 'ANSWER_CONFIDENCE']:
                    parsed[key_clean.lower()] = value_clean
        return parsed

    def _has_sufficient_answer_from_dg(self, data_guardian_result: str) -> str:
        """
        Determines if Data Guardian's result is sufficient, outside scope, or needs HR.
        Returns: "SUFFICIENT_ANSWER", "OUTSIDE_SCOPE", or "INSUFFICIENT_ANSWER".
        """
        if not data_guardian_result or len(data_guardian_result.strip()) < 20: # Arbitrary short length
            return "INSUFFICIENT_ANSWER"

        parsed_dg = self._parse_structured_dg_response(data_guardian_result)

        scope_status = parsed_dg.get('scope_status')
        if scope_status == 'OUTSIDE_SCOPE':
            return "OUTSIDE_SCOPE"

        information_found = parsed_dg.get('information_found')
        # Consider "YES" as sufficient. "PARTIAL" or "NO" or missing implies insufficient.
        if information_found == 'YES':
            return "SUFFICIENT_ANSWER"

        # Fallback: if not clearly "YES" or "OUTSIDE_SCOPE", assume insufficient.
        # This can be refined with confidence scores if available from DataGuardian.
        return "INSUFFICIENT_ANSWER"

    def get_system_prompt(self, stage: Optional[str] = None) -> str:
        common_intro = "You are Maestro, a specialized AI agent. Your primary goal is to be helpful, accurate, and professional."
        if stage == "preprocess":
            return f"{common_intro} You are in PREPROCESSING mode. Your task is to analyze user queries and reformulate them for effective information retrieval."
        elif stage == "synthesize":
            return f"{common_intro} You are in SYNTHESIS mode. Your task is to create comprehensive answers based on provided information. If you use tools, integrate their output naturally into your response."
        elif stage == "final_review":
            return f"{common_intro} You are in FINAL REVIEW mode. Your task is to review and refine a proposed solution or message, ensuring clarity, conciseness, and professional tone, based on specific instructions."
        elif stage == "format_hr_referral":
            return f"{common_intro} You are in HR REFERRAL FORMATTING mode. Your task is to craft a polite referral message to the user."

        # Default system prompt if no specific stage or for general tool use
        return f"""{common_intro}
You assist in a multi-stage support ticket processing system.
- In 'preprocess' stage, you analyze tickets and prepare search queries.
- In 'synthesize' stage, you use search results (and tools like a calculator if needed) to build answers.
- In 'final_review' stage, you refine solutions, often from voice call summaries.
- In 'format_hr_referral' stage, you create messages for HR routing.
Follow instructions precisely for each stage.
Available tools for some stages:
- calculator: Perform mathematical calculations.
"""
