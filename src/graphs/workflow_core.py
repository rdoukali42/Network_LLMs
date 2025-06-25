"""
Core workflow implementation with LangGraph orchestration.
"""
import os
import sys
import traceback
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langfuse import observe

# Add path to access front modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .workflow_state import WorkflowState
from .agent_steps import AgentSteps
from .call_handler import CallHandler
from .redirect_handler import RedirectHandler
from utils.exceptions import WorkflowError


class MultiAgentWorkflow:
    """Multi-agent workflow using LangGraph for Maestro and Data Guardian."""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.agent_steps = AgentSteps(agents)
        self.call_handler = CallHandler(agents)
        self.redirect_handler = RedirectHandler(agents)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the workflow graph."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each step
        workflow.add_node("maestro_preprocess", self.agent_steps.maestro_preprocess_step)
        workflow.add_node("data_guardian", self.agent_steps.data_guardian_step)
        workflow.add_node("maestro_synthesize", self.agent_steps.maestro_synthesize_step)
        workflow.add_node("hr_agent", self.agent_steps.hr_agent_step)
        workflow.add_node("vocal_assistant", self.agent_steps.vocal_assistant_step)
        workflow.add_node("maestro_final", self.agent_steps.maestro_final_step)
        
        # NEW NODES for redirect functionality
        workflow.add_node("call_completion_handler", self.call_handler.call_completion_handler_step)
        workflow.add_node("redirect_detector", self.redirect_handler.redirect_detector_step)
        workflow.add_node("employee_searcher", self.redirect_handler.employee_searcher_step)
        workflow.add_node("maestro_redirect_selector", self.redirect_handler.maestro_redirect_selector_step)
        
        # Define edges: Maestro → Data Guardian → Maestro → [Decision] → End or HR → Vocal → [Redirect Check] → End or Redirect Flow
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
        
        # Route through call completion handler
        workflow.add_edge("vocal_assistant", "call_completion_handler")
        
        # 🔧 FIXED: Check call completion status with proper routing
        # - "call_waiting": Call just initiated → END (prevents premature ticket completion)
        # - "complete": Call completed normally → maestro_final 
        # - "redirect": Call completed with redirect → redirect_detector
        
        # 🔧 FIXED: Check call completion status with proper routing
        workflow.add_conditional_edges(
            "call_completion_handler",
            self.call_handler.check_call_completion,
            {
                "redirect": "redirect_detector",
                "complete": "maestro_final",
                "call_waiting": END  # 🔧 NEW: Stop workflow when call is just initiated
            }
        )
        
        # REDIRECT FLOW EDGES (triggered after call completion)
        workflow.add_edge("redirect_detector", "employee_searcher")
        workflow.add_edge("employee_searcher", "maestro_redirect_selector")
        workflow.add_edge("maestro_redirect_selector", "vocal_assistant")  # Go directly to vocal_assistant
        workflow.add_edge("vocal_assistant", "call_completion_handler")  # Added missing edge for redirect flow
        
        workflow.add_edge("maestro_final", END)
        
        return workflow.compile()
    
    def _route_after_synthesis(self, state: WorkflowState) -> str:
        """Route to HR agent if no sufficient answer found."""
        synthesis_status = state["results"].get("synthesis_status", "success")
        if synthesis_status == "outside_scope":
            print("     🚫 Query outside company scope - ending workflow...\n")
            return "end"  # End workflow for outside scope queries
        elif synthesis_status == "route_to_hr":
            print("     🔄 Routing to HR Agent for further assistance...\n")
            return "hr_agent"
        return "end"
    
    @observe()
    def run(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete workflow."""
        query = initial_input.get("query", "")
        exclude_username = initial_input.get("exclude_username", None)
        
        initial_state: WorkflowState = {
            "messages": [{"content": query, "type": "user"}],
            "current_step": "",
            "results": {},
            "metadata": initial_input,
            "query": query,  # Ensure query is preserved
            "exclude_username": exclude_username  # Pass user exclusion context
        }
        
        # Run the graph workflow - NO FALLBACK, must work or fail
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state["results"]
        except Exception as e:
            # No fallback - throw the error to caller
            error_msg = f"Workflow execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise WorkflowError(error_msg) from e
    
    @observe()
    def process_end_call(self, end_call_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process END_CALL directly without going through the broken LangGraph routing.
        This bypasses the hardcoded entry point and state overwriting issues.
        """
        print(f"\n🔄 PROCESSING END_CALL DIRECTLY (bypassing broken graph routing)")
        print(f"🔄 END_CALL: Input state keys: {list(end_call_state.keys())}")
        
        try:
            # Extract conversation data from messages
            messages = end_call_state.get("messages", [])
            conversation_content = ""
            if messages and len(messages) > 0:
                conversation_content = messages[0].get("content", "")
            
            print(f"🔄 END_CALL: Extracted conversation content (length: {len(conversation_content)})")
            
            # Convert input to proper WorkflowState format
            state: WorkflowState = {
                "messages": messages,
                "current_step": "call_completion_handler",
                "results": {
                    # Set up vocal assistant result with conversation data for redirect analysis
                    "vocal_assistant": {
                        "action": "end_call",
                        "status": "call_completed",
                        "conversation_summary": conversation_content,
                        "conversation_data": {
                            "conversation_summary": conversation_content,
                            "response": conversation_content
                        }
                    }
                },
                "metadata": end_call_state.get("metadata", {}),
                "query": conversation_content  # Use conversation as query for processing
            }
            
            print(f"🔄 END_CALL: Starting call completion handler...")
            
            # 🔧 DEBUG: Check if vocal assistant result has the right format
            vocal_result = state["results"].get("vocal_assistant", {})
            print(f"🔄 END_CALL: 🔧 DEBUG: Vocal result keys: {list(vocal_result.keys()) if vocal_result else 'None'}")
            print(f"🔄 END_CALL: 🔧 DEBUG: Call action: {vocal_result.get('action', 'None')}")
            print(f"🔄 END_CALL: 🔧 DEBUG: Call status: {vocal_result.get('status', 'None')}")
            
            # Step 1: Process call completion
            state = self.call_handler.call_completion_handler_step(state)
            call_completed = state["results"].get("call_completed", False)
            
            print(f"🔄 END_CALL: Call completed: {call_completed}")
            
            if not call_completed:
                print(f"🔄 END_CALL: Call not completed, finishing workflow")
                # Call not completed, just finish
                state = self.agent_steps.maestro_final_step(state)
                return state["results"]
            
            # Step 2: Check for redirect
            print(f"🔄 END_CALL: Checking for redirect...")
            redirect_decision = self.call_handler.check_for_redirect(state)
            
            if redirect_decision == "redirect":
                print(f"🔄 END_CALL: REDIRECT DETECTED - Processing redirect workflow")
                
                # Step 3a: Process redirect flow
                state = self.redirect_handler.redirect_detector_step(state)
                state = self.redirect_handler.employee_searcher_step(state)
                state = self.redirect_handler.maestro_redirect_selector_step(state)
                state = self.agent_steps.vocal_assistant_step(state)  # Use regular vocal_assistant
                
                # Add missing call completion handler for redirect flow
                state = self.call_handler.call_completion_handler_step(state)
                
            else:
                print(f"🔄 END_CALL: No redirect detected - completing normally")
            
            # Only continue to final processing if call is completed
            call_completed = state.get("results", {}).get("call_completed", True)
            if call_completed:
                print(f"🔄 END_CALL: Call completed - proceeding to final processing")
                # Step 4: Final processing
                state = self.agent_steps.maestro_final_step(state)
            else:
                print(f"🔄 END_CALL: Call initiated but not completed - returning to frontend for live call")
                # Return to frontend for the live call interface
                early_return = {
                    "results": state["results"],
                    "status": "call_waiting", 
                    "call_active": True,
                    "redirect_call_initiated": True
                }
                print(f"🔄 END_CALL: Early return keys: {list(early_return.keys())}")
                print(f"🔄 END_CALL: Early return status: {early_return.get('status')}")
                print(f"🔄 END_CALL: Early return call_active: {early_return.get('call_active')}")
                print(f"🔄 END_CALL: Early return redirect_call_initiated: {early_return.get('redirect_call_initiated')}")
                return early_return
            
            print(f"🔄 END_CALL: Direct processing completed successfully")
            print(f"🔄 END_CALL: Final result keys: {list(state['results'].keys())}")
            
            return state["results"]
            
        except Exception as e:
            print(f"❌ END_CALL: Direct processing failed: {e}")
            print(f"❌ END_CALL: Traceback: {traceback.format_exc()}")
            
            # Return error state
            return {
                "error": f"END_CALL processing failed: {str(e)}",
                "status": "error"
            }
