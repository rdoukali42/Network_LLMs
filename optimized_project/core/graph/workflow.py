"""
LangGraph workflow definitions for the optimized_project.
Defines the MultiAgentWorkflow that orchestrates agent interactions.
"""

from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langfuse import observe # Assuming Langfuse is kept

# Agents will be injected, type hinting for clarity
# from ..agents import MaestroAgent, DataGuardianAgent, HRAgent, VocalAssistantAgent

class WorkflowState(TypedDict):
    """State object for the workflow graph."""
    query: str                      # The original user query
    messages: List[Dict[str, Any]]  # History of messages, can include user query
    current_step: str               # Name of the current step in the workflow
    results: Dict[str, Any]         # To store results from different agents/steps
    metadata: Dict[str, Any]        # Any other metadata to pass through the graph
    exclude_username: Optional[str] # Username to exclude for HR agent assignment


class MultiAgentWorkflow:
    """
    Multi-agent workflow using LangGraph.
    Orchestrates Maestro, DataGuardian, HRAgent, and VocalAssistantAgent.
    """

    def __init__(self, agents: Dict[str, Any]): # Agents are instances of BaseAgent subclasses
        """
        Initializes the MultiAgentWorkflow.
        Args:
            agents: A dictionary of initialized agent instances, keyed by agent name
                    (e.g., "maestro", "data_guardian", "hr_agent", "vocal_assistant").
        """
        self.agents = agents
        if not all(agent_name in self.agents for agent_name in ["maestro", "data_guardian", "hr_agent", "vocal_assistant"]):
            # This check is basic. A more robust check would verify agent types or capabilities.
            print("Warning: Not all expected core agents ('maestro', 'data_guardian', 'hr_agent', 'vocal_assistant') found in provided agents dict.")

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Builds the LangGraph StateGraph for the multi-agent workflow."""
        workflow = StateGraph(WorkflowState)

        # Add nodes for each step, corresponding to methods in this class
        workflow.add_node("maestro_preprocess", self._maestro_preprocess_step)
        workflow.add_node("data_guardian_search", self._data_guardian_search_step)
        workflow.add_node("maestro_synthesize", self._maestro_synthesize_step)
        workflow.add_node("hr_assignment", self._hr_assignment_step)
        workflow.add_node("vocal_assistant_handoff", self._vocal_assistant_handoff_step)
        workflow.add_node("maestro_finalize_response", self._maestro_finalize_response_step)

        # Define the workflow edges
        workflow.set_entry_point("maestro_preprocess")
        workflow.add_edge("maestro_preprocess", "data_guardian_search")
        workflow.add_edge("data_guardian_search", "maestro_synthesize")

        workflow.add_conditional_edges(
            "maestro_synthesize", # Source node
            self._decide_after_synthesis, # Function to decide next step
            { # Path map: output of decision function -> next node
                "route_to_hr": "hr_assignment",
                "finalize_direct_answer": "maestro_finalize_response", # If DG had enough info
                "end_workflow_outside_scope": END, # If query is OOS
                "end_workflow_general": END # Default end if no other route
            }
        )

        workflow.add_edge("hr_assignment", "vocal_assistant_handoff")
        workflow.add_edge("vocal_assistant_handoff", "maestro_finalize_response") # Maestro formats final HR/Vocal info
        workflow.add_edge("maestro_finalize_response", END) # Final end point

        return workflow.compile()

    # --- Graph Node Implementations ---
    @observe()
    def _maestro_preprocess_step(self, state: WorkflowState) -> WorkflowState:
        state = state.copy()
        state["current_step"] = "maestro_preprocess"
        # print("🚀 Workflow: Maestro Preprocessing...")

        maestro_agent = self.agents.get("maestro")
        if maestro_agent:
            result = maestro_agent.run({
                "query": state["query"],
                "stage": "preprocess"
            })
            state["results"]["maestro_preprocess_output"] = result.get("result") # Or specific field like "preprocessed_query_details"
        else:
            state["results"]["maestro_preprocess_output"] = state["query"] # Fallback: use original query
        return state

    @observe()
    def _data_guardian_search_step(self, state: WorkflowState) -> WorkflowState:
        state = state.copy()
        state["current_step"] = "data_guardian_search"
        # print("🚀 Workflow: Data Guardian Searching...")

        data_guardian_agent = self.agents.get("data_guardian")
        preprocessed_queries = state["results"].get("maestro_preprocess_output", state["query"])

        if data_guardian_agent:
            result = data_guardian_agent.run({
                "query": state["query"], # Original query for context
                "search_queries": preprocessed_queries
            })
            # DataGuardian's result is expected to be a text containing SCOPE_STATUS, INFORMATION_FOUND, etc.
            state["results"]["data_guardian_output"] = result.get("result")
            state["results"]["data_guardian_raw_search"] = result.get("raw_search_results", []) # Optional
        else:
            state["results"]["data_guardian_output"] = "Data Guardian not available. SCOPE_STATUS: UNKNOWN\nINFORMATION_FOUND: NO"
        return state

    @observe()
    def _maestro_synthesize_step(self, state: WorkflowState) -> WorkflowState:
        state = state.copy()
        state["current_step"] = "maestro_synthesize"
        # print("🚀 Workflow: Maestro Synthesizing...")

        maestro_agent = self.agents.get("maestro")
        data_guardian_text_output = state["results"].get("data_guardian_output", "")

        if maestro_agent:
            # Maestro's run method for 'synthesize' stage needs to parse DG output
            # and determine if it's sufficient, OOS, or needs HR.
            # The status for routing decision should be part of Maestro's synthesis result.
            result = maestro_agent.run({
                "query": state["query"],
                "stage": "synthesize",
                "data_guardian_result": data_guardian_text_output
            })
            state["results"]["maestro_synthesis_output"] = result.get("result")
            # Maestro's synthesis should also return a status like:
            # "sufficient_answer", "route_to_hr", "outside_scope"
            state["results"]["synthesis_decision_status"] = result.get("status", "error") # e.g. from MaestroAgent
        else:
            state["results"]["maestro_synthesis_output"] = "Maestro for synthesis not available."
            state["results"]["synthesis_decision_status"] = "route_to_hr" # Default to HR if no synthesis
        return state

    def _decide_after_synthesis(self, state: WorkflowState) -> str:
        """Determines the next step after Maestro synthesis."""
        decision_status = state["results"].get("synthesis_decision_status", "error")
        # print(f"🚀 Workflow: Decision after synthesis - Status: {decision_status}")

        if decision_status == "outside_scope":
            return "end_workflow_outside_scope"
        elif decision_status == "route_to_hr":
            return "route_to_hr"
        elif decision_status == "success": # Implies sufficient answer was synthesized
            return "finalize_direct_answer"
        else: # Default or error
            # print(f"Warning: Unexpected synthesis_decision_status '{decision_status}'. Ending workflow.")
            return "end_workflow_general"

    @observe()
    def _hr_assignment_step(self, state: WorkflowState) -> WorkflowState:
        state = state.copy()
        state["current_step"] = "hr_assignment"
        # print("🚀 Workflow: HR Assignment...")

        hr_agent = self.agents.get("hr_agent")
        if hr_agent:
            # HR Agent needs the original query/ticket details.
            # It also needs 'exclude_username' from the initial state if provided.
            hr_input = {
                "query": state["query"], # Or more structured ticket data if available from earlier steps
                "ticket_id": state["metadata"].get("ticket_id", "N/A"), # If ticket ID was in initial metadata
                "exclude_username": state.get("exclude_username")
            }
            # Add other fields to hr_input if Maestro's preprocessing extracted them
            # e.g. skills_required, priority, etc.
            # For now, keeping it simple with 'query'.

            result = hr_agent.run(hr_input)
            # HR Agent's result is a dict from HRErrorResponse or HRTicketResponse
            state["results"]["hr_assignment_output"] = result
        else:
            state["results"]["hr_assignment_output"] = {"status": "error", "error_message": "HR Agent not available."}
        return state

    @observe()
    def _vocal_assistant_handoff_step(self, state: WorkflowState) -> WorkflowState:
        state = state.copy()
        state["current_step"] = "vocal_assistant_handoff"
        # print("🚀 Workflow: Vocal Assistant Handoff...")

        vocal_assistant_agent = self.agents.get("vocal_assistant")
        hr_output = state["results"].get("hr_assignment_output", {})

        # Check if HR assignment was successful and employee data is present
        if hr_output.get("status") == "success" and hr_output.get("recommended_assignment"):
            employee_data_for_call = next((emp for emp in hr_output.get("matched_employees", [])
                                           if emp["employee_id"] == hr_output["recommended_assignment"]), None)
            if vocal_assistant_agent and employee_data_for_call:
                ticket_data_for_call = {"id": state["metadata"].get("ticket_id"), "subject": state["query"][:100], "description": state["query"]}
                result = vocal_assistant_agent.run({
                    "action": "initiate_call",
                    "ticket_data": ticket_data_for_call,
                    "employee_data": employee_data_for_call
                })
                state["results"]["vocal_assistant_output"] = result # Contains 'call_info_for_ui'
            elif not employee_data_for_call:
                state["results"]["vocal_assistant_output"] = {"status": "skipped", "result": "No specific employee data from HR to initiate call."}
            else:
                state["results"]["vocal_assistant_output"] = {"status": "skipped", "result": "Vocal Assistant not available."}
        else:
            state["results"]["vocal_assistant_output"] = {"status": "skipped", "result": "No successful HR assignment to hand off."}
        return state

    @observe()
    def _maestro_finalize_response_step(self, state: WorkflowState) -> WorkflowState:
        state = state.copy()
        state["current_step"] = "maestro_finalize_response"
        # print("🚀 Workflow: Maestro Finalizing Response...")

        maestro_agent = self.agents.get("maestro")
        final_response_content = ""

        # Case 1: Direct answer from synthesis
        if state["results"].get("synthesis_decision_status") == "success":
            final_response_content = state["results"].get("maestro_synthesis_output", "Processing complete.")

        # Case 2: Response after HR assignment and Vocal Assistant handoff
        elif state["results"].get("vocal_assistant_output", {}).get("status") == "success":
            vocal_output = state["results"]["vocal_assistant_output"]
            call_info = vocal_output.get("call_info_for_ui", {})
            hr_reasoning = state["results"].get("hr_assignment_output", {}).get("assignment_reasoning", "Assignment made by HR.")

            if call_info.get("employee_name"):
                # Use Maestro to format this message
                if maestro_agent:
                    formatted_referral = maestro_agent.run({
                        "query": state["query"], # Original query
                        "stage": "format_hr_referral",
                        "employee_details_for_referral": f"{call_info['employee_name']} (username: {call_info['employee_username']})",
                        "original_ticket_summary": state["query"][:150] # Brief summary
                    })
                    final_response_content = formatted_referral.get("result",
                        f"Your query has been routed to {call_info['employee_name']}. "
                        f"Details for call initiation have been prepared. Reason: {hr_reasoning}"
                    )
                else: # Fallback formatting
                    final_response_content = (
                        f"Your ticket has been assigned to {call_info.get('employee_name', 'an expert')}. "
                        f"A call notification will be prepared. Reasoning: {hr_reasoning}"
                    )
            else: # HR assigned but vocal assistant step had an issue or no employee data
                final_response_content = state["results"].get("hr_assignment_output", {}).get("assignment_reasoning",
                                         "Your query requires specialized help and has been routed accordingly.")

        # Case 3: HR assignment failed or no suitable agent
        elif state["results"].get("hr_assignment_output", {}).get("status") != "success" and \
             state["results"].get("synthesis_decision_status") == "route_to_hr":
            final_response_content = state["results"].get("hr_assignment_output", {}).get("error_message",
                                         "We are unable to find a suitable expert at this moment. Please try again later.")

        # Default fallback if none of the above
        if not final_response_content:
            final_response_content = "Your query has been processed. If further action is needed, you will be contacted."

        state["results"]["final_system_response"] = final_response_content
        # For consistency with AISystem's expected output key from original project
        state["results"]["synthesis"] = final_response_content
        return state

    @observe()
    def run(self, initial_workflow_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the compiled LangGraph workflow.
        Args:
            initial_workflow_input: Dictionary containing initial inputs, MUST include "query".
                                   Can also include "exclude_username", "ticket_id" in "metadata".
        Returns:
            The final results dictionary from the workflow state.
        """
        query = initial_workflow_input.get("query")
        if not query:
            raise ValueError("Input dictionary must contain a 'query' key.")

        initial_state: WorkflowState = {
            "query": query,
            "messages": [{"role": "user", "content": query}], # Simplified messages
            "current_step": "",
            "results": {},
            "metadata": {"ticket_id": initial_workflow_input.get("ticket_id")}, # Pass ticket_id if available
            "exclude_username": initial_workflow_input.get("exclude_username")
        }

        # The fallback mechanism from the original file (manual agent calls) is removed
        # as per the refactoring request to remove processes starting from API errors.
        # Errors from graph.invoke should now propagate or be handled by LangGraph's error mechanisms.
        try:
            # print(f"🚀 Invoking MultiAgentWorkflow with initial state: {initial_state}")
            final_state = self.graph.invoke(initial_state)
            # Ensure 'synthesis' key is present for compatibility with AISystem expectations
            if "final_system_response" in final_state.get("results", {}) and "synthesis" not in final_state.get("results", {}):
                final_state["results"]["synthesis"] = final_state["results"]["final_system_response"]
            return final_state.get("results", {"error": "Workflow produced no results."})
        except Exception as e:
            print(f"Critical error during graph invocation: {e}")
            import traceback
            traceback.print_exc()
            # Provide a structured error response
            return {
                "error": "Workflow execution failed.",
                "details": str(e),
                "synthesis": "We encountered an error processing your request. Please try again later." # Fallback for AISystem
            }

# Example of how to use (for testing, not part of the class itself)
if __name__ == '__main__':
    # This requires mock agents or a full setup.
    print("MultiAgentWorkflow defined. For testing, instantiate with mock/real agents and call run().")

    # Mock Agent structure for testing
    class MockAgent:
        def __init__(self, name):
            self.name = name
        def run(self, input_data):
            print(f"MockAgent '{self.name}' received: {input_data}")
            if self.name == "maestro" and input_data.get("stage") == "preprocess":
                return {"result": input_data["query"]} # Simple echo for search_queries
            if self.name == "data_guardian":
                return {"result": "SCOPE_STATUS: WITHIN_SCOPE\nINFORMATION_FOUND: YES\nANSWER_CONFIDENCE: HIGH\n\nFound relevant info."}
            if self.name == "maestro" and input_data.get("stage") == "synthesize":
                return {"result": "Synthesized answer based on DG.", "status": "success"} # or "route_to_hr" or "outside_scope"
            if self.name == "hr_agent":
                return {"status": "success", "recommended_assignment": "emp123",
                        "matched_employees": [{"employee_id": "emp123", "name": "Mock Employee"}],
                        "assignment_reasoning": "Mock HR assigned emp123"}
            if self.name == "vocal_assistant":
                return {"status": "success", "action_result": "call_data_prepared",
                        "call_info_for_ui": {"employee_name": "Mock Employee"}}
            return {"result": f"Mock output from {self.name}"}

    mock_agents = {
        "maestro": MockAgent("maestro"),
        "data_guardian": MockAgent("data_guardian"),
        "hr_agent": MockAgent("hr_agent"),
        "vocal_assistant": MockAgent("vocal_assistant"),
    }

    # Test Case 1: Direct Answer
    # print("\n--- Test Case 1: Direct Answer ---")
    # workflow = MultiAgentWorkflow(mock_agents)
    # results_direct = workflow.run({"query": "What is our VPN setup?"})
    # print(f"Results (Direct Answer): {json.dumps(results_direct, indent=2)}")

    # Test Case 2: Route to HR
    # print("\n--- Test Case 2: Route to HR ---")
    # class MockMaestroSynthHR(MockAgent): # Override synthesis for HR routing
    #     def run(self, input_data):
    #         if input_data.get("stage") == "synthesize":
    #             return {"result": "Info insufficient, routing.", "status": "route_to_hr"}
    #         return super().run(input_data)

    # mock_agents_hr = {**mock_agents, "maestro": MockMaestroSynthHR("maestro_hr_route")}
    # workflow_hr = MultiAgentWorkflow(mock_agents_hr)
    # results_hr = workflow_hr.run({"query": "I need help with my payroll.", "ticket_id": "TICKET123", "exclude_username": "user_self"})
    # print(f"Results (Route to HR): {json.dumps(results_hr, indent=2)}")

    # Test Case 3: Outside Scope
    # print("\n--- Test Case 3: Outside Scope ---")
    # class MockMaestroSynthOOS(MockAgent):
    #     def run(self, input_data):
    #         if input_data.get("stage") == "synthesize":
    #             return {"result": "This is outside scope.", "status": "outside_scope"}
    #         return super().run(input_data)

    # mock_agents_oos = {**mock_agents, "maestro": MockMaestroSynthOOS("maestro_oos")}
    # workflow_oos = MultiAgentWorkflow(mock_agents_oos)
    # results_oos = workflow_oos.run({"query": "Can you fix my toaster?"})
    # print(f"Results (Outside Scope): {json.dumps(results_oos, indent=2)}")
