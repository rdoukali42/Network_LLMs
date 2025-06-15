"""
LangGraph workflow definitions.
"""

from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langfuse import observe


class WorkflowState(TypedDict):
    """State object for the workflow."""
    messages: List[Dict]
    current_step: str
    results: Dict[str, Any]
    metadata: Dict[str, Any]
    query: str  # Add query as explicit field


class MultiAgentWorkflow:
    """Multi-agent workflow using LangGraph for Maestro and Data Guardian."""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the workflow graph."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each step
        workflow.add_node("maestro_preprocess", self._maestro_preprocess_step)
        workflow.add_node("data_guardian", self._data_guardian_step)
        workflow.add_node("maestro_synthesize", self._maestro_synthesize_step)
        workflow.add_node("hr_agent", self._hr_agent_step)
        workflow.add_node("vocal_assistant", self._vocal_assistant_step)
        workflow.add_node("maestro_final", self._maestro_final_step)
        
        # Define edges: Maestro → Data Guardian → Maestro → [Decision] → End or HR → Vocal → End
        workflow.set_entry_point("maestro_preprocess")
        workflow.add_edge("maestro_preprocess", "data_guardian")
        workflow.add_edge("data_guardian", "maestro_synthesize")
        workflow.add_conditional_edges(
            "maestro_synthesize",
            self._route_after_synthesis,
            {
                "end": END,
                "hr_agent": "hr_agent"
            }
        )
        workflow.add_edge("hr_agent", "vocal_assistant")
        workflow.add_edge("vocal_assistant", "maestro_final")
        workflow.add_edge("maestro_final", END)
        
        return workflow.compile()
    
    @observe()
    def _maestro_preprocess_step(self, state: WorkflowState) -> WorkflowState:
        """Maestro preprocessing step - reformulate query for search."""
        state = state.copy()
        state["current_step"] = "maestro_preprocess"
        
        # Get query from state
        query = state.get("query", "")
        if not query and state.get("messages"):
            query = state["messages"][-1].get("content", "")
        
        # Run Maestro preprocessing
        if "maestro" in self.agents:
            maestro_result = self.agents["maestro"].run({
                "query": query,
                "stage": "preprocess"
            })
            state["results"]["maestro_preprocess"] = maestro_result.get("result", "Query processed")
        else:
            state["results"]["maestro_preprocess"] = query  # Fallback
        
        return state
    
    @observe()
    def _data_guardian_step(self, state: WorkflowState) -> WorkflowState:
        """Data Guardian step - search local documents."""
        state = state.copy()
        state["current_step"] = "data_guardian"
        
        # Get query and preprocessed queries
        query = state.get("query", "")
        search_queries = state["results"].get("maestro_preprocess", query)
        
        # Run Data Guardian search
        if "data_guardian" in self.agents:
            data_guardian_result = self.agents["data_guardian"].run({
                "query": query,
                "search_queries": search_queries
            })
            state["results"]["data_guardian"] = data_guardian_result.get("result", "No documents found")
        else:
            state["results"]["data_guardian"] = "Data Guardian not available"
        
        return state
    
    @observe()
    def _maestro_synthesize_step(self, state: WorkflowState) -> WorkflowState:
        """Maestro synthesis step - create final response or route to HR."""
        state = state.copy()
        state["current_step"] = "maestro_synthesize"
        
        # Get query and Data Guardian result
        query = state.get("query", "")
        data_guardian_result = state["results"].get("data_guardian", "")
        
        # Run Maestro synthesis
        if "maestro" in self.agents:
            synthesis_result = self.agents["maestro"].run({
                "query": query,
                "stage": "synthesize",
                "data_guardian_result": data_guardian_result
            })
            state["results"]["synthesis"] = synthesis_result.get("result", "Response generated")
            state["results"]["synthesis_status"] = synthesis_result.get("status", "success")
        else:
            # Fallback synthesis
            state["results"]["synthesis"] = f"Based on available information: {data_guardian_result}"
            state["results"]["synthesis_status"] = "success"
        
        return state
    
    def _route_after_synthesis(self, state: WorkflowState) -> str:
        """Route to HR agent if no sufficient answer found."""
        synthesis_status = state["results"].get("synthesis_status", "success")
        if synthesis_status == "route_to_hr":
            return "hr_agent"
        return "end"
    
    @observe()
    def _hr_agent_step(self, state: WorkflowState) -> WorkflowState:
        """HR Agent step - find suitable employee."""
        state = state.copy()
        state["current_step"] = "hr_agent"
        
        # Get query
        query = state.get("query", "")
        
        # Run HR Agent
        if "hr_agent" in self.agents:
            hr_result = self.agents["hr_agent"].run({"query": query})
            state["results"]["hr_agent"] = hr_result.get("result", "No employee found")
            state["results"]["hr_action"] = hr_result.get("action", "no_assignment")
            state["results"]["employee_data"] = hr_result.get("employee_data", None)
        else:
            state["results"]["hr_agent"] = "HR Agent not available"
            state["results"]["hr_action"] = "no_assignment"
        
        return state
    
    @observe()
    def _vocal_assistant_step(self, state: WorkflowState) -> WorkflowState:
        """Vocal Assistant step - initiate voice call with assigned employee."""
        state = state.copy()
        state["current_step"] = "vocal_assistant"
        
        # Get query and HR results
        query = state.get("query", "")
        hr_action = state["results"].get("hr_action", "no_assignment")
        employee_data = state["results"].get("employee_data", None)
        
        if hr_action == "assign" and employee_data:
            # Prepare ticket data from query and state
            ticket_data = {
                "id": "temp_id",  # Will be set by ticket system
                "subject": "Support Request",
                "description": query,
                "category": "Technical Issue",
                "priority": "Medium"
            }
            
            # Run Vocal Assistant
            if "vocal_assistant" in self.agents:
                vocal_result = self.agents["vocal_assistant"].run({
                    "action": "initiate_call",
                    "ticket_data": ticket_data,
                    "employee_data": employee_data,
                    "query": query
                })
                state["results"]["vocal_assistant"] = vocal_result.get("result", "Call initiated")
                state["results"]["vocal_action"] = vocal_result.get("action", "start_call")
                state["results"]["call_info"] = vocal_result.get("call_info", None)
            else:
                state["results"]["vocal_assistant"] = "Vocal Assistant not available"
                state["results"]["vocal_action"] = "no_call"
        else:
            state["results"]["vocal_assistant"] = "No employee assigned for voice call"
            state["results"]["vocal_action"] = "no_call"
        
        return state

    @observe()
    def _maestro_final_step(self, state: WorkflowState) -> WorkflowState:
        """Final Maestro step - format employee referral response or voice call result."""
        state = state.copy()
        state["current_step"] = "maestro_final"
        
        # Get query and results
        query = state.get("query", "")
        hr_result = state["results"].get("hr_agent", "")
        vocal_action = state["results"].get("vocal_action", "no_call")
        call_info = state["results"].get("call_info", None)
        
        if vocal_action == "start_call" and call_info:
            # Voice call initiated - provide call information
            final_response = f"""Your ticket has been assigned to {call_info.get('employee_name', 'an expert')} who will contact you shortly.

A voice call is being initiated to discuss your issue in detail and provide a personalized solution.

Please be ready to answer the call to discuss: {call_info.get('ticket_subject', 'your request')}

The assigned expert will call you to resolve this matter efficiently."""
        else:
            # Standard HR referral response
            final_response = f"""I couldn't find a direct answer in our knowledge base for your request, but I can help connect you with the right expert.

{hr_result}

Please reach out to them directly - they'll be able to provide specialized assistance with your specific issue."""
        
        state["results"]["final_response"] = final_response
        state["results"]["synthesis"] = final_response  # Update synthesis for consistency
        
        return state
    
    @observe()
    def run(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete workflow."""
        query = initial_input.get("query", "")
        
        initial_state: WorkflowState = {
            "messages": [{"content": query, "type": "user"}],
            "current_step": "",
            "results": {},
            "metadata": initial_input,
            "query": query  # Ensure query is preserved
        }
        
        # Try to run the graph workflow, fallback to simple execution
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state["results"]
        except Exception as e:
            # Fallback: run agents manually in sequence
            print(f"Running fallback workflow for: {query}")
            
            # Step 1: Maestro preprocessing
            maestro_preprocess = self.agents["maestro"].run({
                "query": query,
                "stage": "preprocess"
            })
            print(f"Maestro preprocess result: {maestro_preprocess}")
            
            # Step 2: Data Guardian search
            data_guardian_result = self.agents["data_guardian"].run({
                "query": query,
                "search_queries": maestro_preprocess.get("result", query)
            })
            print(f"Data Guardian result: {data_guardian_result}")
            
            # Step 3: Maestro synthesis
            maestro_synthesis = self.agents["maestro"].run({
                "query": query,
                "stage": "synthesize", 
                "data_guardian_result": data_guardian_result.get("result", "")
            })
            print(f"Maestro synthesis result: {maestro_synthesis}")
            
            # Check if need to route to HR
            if maestro_synthesis.get("status") == "route_to_hr":
                # Step 4: HR Agent
                hr_result = self.agents.get("hr_agent", {}).run({"query": query}) if "hr_agent" in self.agents else {"result": "HR Agent not available"}
                print(f"HR Agent result: {hr_result}")
                
                # Step 5: Final response formatting
                final_response = f"""I couldn't find a direct answer in our knowledge base for your request, but I can help connect you with the right expert.

{hr_result.get("result", "")}

Please reach out to them directly - they'll be able to provide specialized assistance with your specific issue."""
                
                return {
                    "maestro_preprocess": maestro_preprocess.get("result", ""),
                    "data_guardian": data_guardian_result.get("result", ""),
                    "hr_agent": hr_result.get("result", ""),
                    "synthesis": final_response,
                    "documents_found": data_guardian_result.get("documents_found", 0)
                }
            
            # Return combined results
            return {
                "maestro_preprocess": maestro_preprocess.get("result", ""),
                "data_guardian": data_guardian_result.get("result", ""),
                "synthesis": maestro_synthesis.get("result", ""),
                "documents_found": data_guardian_result.get("documents_found", 0)
            }
