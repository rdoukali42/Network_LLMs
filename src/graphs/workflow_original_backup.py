"""
LangGraph workflow definitions.
"""

import sys
import os
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langfuse import observe
from datetime import datetime

# Add path to access front modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import redirect functionality
from agents.vocal_assistant import VocalResponse

# Import front modules for ticket management and notifications
try:
    from front.tickets.ticket_manager import TicketManager
    from front.database import DatabaseManager
    FRONT_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ WORKFLOW: Could not import front modules: {e}")
    TicketManager = None
    DatabaseManager = None
    FRONT_MODULES_AVAILABLE = False


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
        
        # 🆕 NEW NODES for redirect functionality
        workflow.add_node("call_completion_handler", self._call_completion_handler_step)
        workflow.add_node("redirect_detector", self._redirect_detector_step)
        workflow.add_node("employee_searcher", self._employee_searcher_step)
        workflow.add_node("maestro_redirect_selector", self._maestro_redirect_selector_step)
        # workflow.add_node("vocal_assistant_redirect", self._vocal_assistant_redirect_step)  # 🔧 REMOVED: No longer needed
        
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
        
        # 🔄 UPDATED: Route through call completion handler
        workflow.add_edge("vocal_assistant", "call_completion_handler")
        
        # 🆕 NEW CONDITIONAL EDGE: Check call completion status
        workflow.add_conditional_edges(
            "call_completion_handler",
            self._check_call_completion,
            {
                "redirect": "redirect_detector",
                "complete": "maestro_final"
            }
        )
        
        # 🆕 REDIRECT FLOW EDGES (triggered after call completion)
        workflow.add_edge("redirect_detector", "employee_searcher")
        workflow.add_edge("employee_searcher", "maestro_redirect_selector")
        workflow.add_edge("maestro_redirect_selector", "vocal_assistant")  # 🔧 FIXED: Go directly to vocal_assistant
        workflow.add_edge("vocal_assistant", "call_completion_handler")  # 🔧 FIXED: Added missing edge for redirect flow
        # workflow.add_edge("vocal_assistant_redirect", "maestro_final")  # 🔧 REMOVED: No longer needed
        
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
            print("     🎯 Starting Maestro Agent - Workflow coordination beginning...\n")
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
            print("     🛡️ Data Guardian Agent is searching documents.../n")
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
            print("     🎯 Maestro: Consulting Data Guardian for knowledge retrieval...")
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
        if synthesis_status == "outside_scope":
            print("     🚫 Query outside company scope - ending workflow...\n")
            return "end"  # End workflow for outside scope queries
        elif synthesis_status == "route_to_hr":
            print("     🔄 Routing to HR Agent for further assistance...\n")
            return "hr_agent"
        return "end"
    
    @observe()
    def _hr_agent_step(self, state: WorkflowState) -> WorkflowState:
        """HR Agent step - find suitable employee."""
        state = state.copy()
        state["current_step"] = "hr_agent"
        
        # Ensure results dict exists and preserve existing data
        if "results" not in state:
            state["results"] = {}
        else:
            # Make a copy of existing results to preserve them
            state["results"] = state["results"].copy()
        
        # Get query
        query = state.get("query", "")
        
        # Run HR Agent (AvailabilityTool will automatically filter current user)
        if "hr_agent" in self.agents:
            print("     🤖 Starting HR Agent - Employee matching in progress.../n")
            hr_result = self.agents["hr_agent"].run({"query": query})
            
            # DEBUG: Print HR result to understand structure
            # print("🔍 WORKFLOW DEBUG - HR Agent result:")
            # print(f"   Status: {hr_result.get('status')} (type: {type(hr_result.get('status'))})")
            # print(f"   Status value: {getattr(hr_result.get('status'), 'value', 'No value attr')}")
            # print(f"   Keys in hr_result: {list(hr_result.keys())}")
            # print(f"   Matched employees count: {len(hr_result.get('matched_employees', []))}")
            # print(f"   Recommended assignment: {hr_result.get('recommended_assignment')}")
            
            # Handle new Pydantic response format - status is a StatusEnum object
            status = hr_result.get("status")
            status_check = status and (str(status) == "StatusEnum.SUCCESS" or status.value == "success")
            # print(f"🔍 WORKFLOW DEBUG - Status check: {status_check}")
            
            if status_check:
                # print("✅ WORKFLOW DEBUG - Status check passed, processing employees...")
                # Extract information from new structured response
                matched_employees = hr_result.get("matched_employees", [])
                recommended_assignment = hr_result.get("recommended_assignment")
                
                # print(f"   Matched employees: {len(matched_employees)}")
                # print(f"   Recommended assignment: {recommended_assignment}")
                
                if matched_employees and recommended_assignment:
                    # print("✅ WORKFLOW DEBUG - Found employees and assignment, processing...")
                    # Get the recommended employee data
                    recommended_employee = next(
                        (emp for emp in matched_employees if emp["employee_id"] == recommended_assignment), 
                        matched_employees[0] if matched_employees else None
                    )
                    
                    # print(f"   Recommended employee: {recommended_employee.get('name') if recommended_employee else 'None'}")
                    
                    if recommended_employee:
                        # print("✅ WORKFLOW DEBUG - Creating employee data and setting assignment...")
                        # Add this debug block before creating legacy_employee_data (around line 166)
                        # print("📋📋📋📋📋📋📋🔍 DEBUG: Checking employee data keys...")
                        # print(f"📋📋📋📋📋📋📋 Recommended Employee Raw Data: {recommended_employee}")
                        # print(f"📋 📋📋📋📋📋Available Keys: {list(recommended_employee.keys())}")
                        # print("📋📋📋📋📋📋🔍 Key-Value pairs:")
                        # for key, value in recommended_employee.items():
                            # print(f"   → {key}: {value}")
                        # print("=" * 50)
                        # Convert to legacy format for compatibility
                        legacy_employee_data = {
                            "id": recommended_employee["employee_id"],
                            "username": recommended_employee["username"], 
                            "full_name": recommended_employee["name"],
                            "email": recommended_employee["email"],
                            "department": recommended_employee["department"],
                            "role_in_company": f"Score: {recommended_employee['overall_score']:.2f}",
                            "expertise": ", ".join(recommended_employee["skills"][:3]),
                            "responsibilities": recommended_employee["match_reasoning"],
                            "availability_status": recommended_employee["availability_status"]
                        }
                        
                        state["results"]["hr_agent"] = hr_result.get("assignment_reasoning", "Employee assigned")
                        state["results"]["hr_action"] = "assign"
                        state["results"]["employee_data"] = legacy_employee_data
                        state["results"]["hr_response"] = hr_result  # Store full response for future use
                        # print("✅ WORKFLOW DEBUG - Assignment data set successfully!")
                    else:
                        print("❌ WORKFLOW DEBUG - No recommended employee found")
                        state["results"]["hr_agent"] = "No suitable employee found"
                        state["results"]["hr_action"] = "no_assignment"
                        state["results"]["employee_data"] = None
                        state["results"]["hr_response"] = hr_result
                else:
                    state["results"]["hr_agent"] = "No suitable employees available at the moment"
                    state["results"]["hr_action"] = "no_assignment" 
                    state["results"]["employee_data"] = None
                    state["results"]["hr_response"] = hr_result
            else:
                # Handle error responses
                error_message = hr_result.get("error_message", "HR Agent processing failed")
                state["results"]["hr_agent"] = error_message
                state["results"]["hr_action"] = "no_assignment"
                state["results"]["employee_data"] = None
                state["results"]["hr_response"] = hr_result
        else:
            state["results"]["hr_agent"] = "HR Agent not available"
            state["results"]["hr_action"] = "no_assignment"
            state["results"]["employee_data"] = None
        
        return state
    
    @observe()
    def _vocal_assistant_step(self, state: WorkflowState) -> WorkflowState:
        """Vocal Assistant step - initiate voice call with assigned employee."""
        state = state.copy()
        state["current_step"] = "vocal_assistant"
        
        print(f"\n     📞 VOCAL ASSISTANT STEP: Initiating voice call...")
        
        # Ensure results dict exists and preserve existing data
        if "results" not in state:
            state["results"] = {}
        else:
            # Make a copy of existing results to preserve them
            state["results"] = state["results"].copy()
        
        # Get query and HR results
        query = state.get("query", "")
        hr_action = state["results"].get("hr_action", "no_assignment")
        employee_data = state["results"].get("employee_data", None)
        
        print(f"     � VOCAL ASSISTANT STEP: HR action: {hr_action}")
        print(f"     📞 VOCAL ASSISTANT STEP: Employee assigned: {'Yes' if employee_data else 'No'}")
        if employee_data:
            print(f"     📞 VOCAL ASSISTANT STEP: Employee: {employee_data.get('full_name', 'Unknown')} ({employee_data.get('username', 'No username')})")
        
        if hr_action == "assign" and employee_data:
            # Check if this is a redirect scenario
            redirect_context = state["results"].get("redirect_context", {})
            is_redirect = redirect_context.get("is_redirect", False)
            
            # Prepare ticket data from query and state
            if is_redirect:
                # For redirects, use existing ticket data with redirect context
                ticket_data = state["results"].get("ticket_data", {})
                if not ticket_data:
                    # 🔧 FIXED: Use real ticket ID from metadata, not temp ID
                    real_ticket_id = state["metadata"].get("ticket_id", "unknown")
                    ticket_data = {
                        "id": real_ticket_id,  # Use REAL ticket ID!
                        "subject": "Redirected Support Request", 
                        "description": query,
                        "category": "Technical Issue",
                        "priority": "Medium"
                    }
                
                print(f"     📞 VOCAL ASSISTANT STEP: REDIRECT CALL - Existing ticket: {ticket_data.get('id', 'Unknown')}")
                print(f"     📞 VOCAL ASSISTANT STEP: Redirect reason: {redirect_context.get('redirect_reason', 'Specialized expertise')}")
                print(f"     📞 VOCAL ASSISTANT STEP: Previous employee: {redirect_context.get('original_employee', 'Unknown')}")
                
                # Add redirect information to query for context
                enhanced_query = f"REDIRECT: {query} [Redirected from {redirect_context.get('original_employee', 'previous employee')} - Reason: {redirect_context.get('redirect_reason', 'specialized expertise needed')}]"
                
            else:
                # Regular new ticket
                ticket_data = {
                    "id": "temp_id",  # Will be set by ticket system
                    "subject": "Support Request",
                    "description": query,
                    "category": "Technical Issue", 
                    "priority": "Medium"
                }
                enhanced_query = query
                print(f"     📞 VOCAL ASSISTANT STEP: NEW CALL - Fresh ticket")
            
            print(f"     📞 VOCAL ASSISTANT STEP: Ticket data prepared: {ticket_data}")
            
            # Run Vocal Assistant
            if "vocal_assistant" in self.agents:
                print(f"     📞 VOCAL ASSISTANT STEP: Calling VocalAssistant...")
                
                vocal_input = {
                    "action": "initiate_call",
                    "ticket_data": ticket_data,
                    "employee_data": employee_data,
                    "query": enhanced_query
                }
                
                # Add redirect context if this is a redirect
                if is_redirect:
                    vocal_input["redirect_context"] = redirect_context
                
                vocal_result = self.agents["vocal_assistant"].run(vocal_input)
                
                print(f"     📞 VOCAL ASSISTANT STEP: VocalAssistant call result: {vocal_result}")
                # Store full vocal_result, not just specific fields
                state["results"]["vocal_assistant"] = vocal_result
                state["results"]["vocal_action"] = vocal_result.get("action", "start_call")
                state["results"]["call_info"] = vocal_result.get("call_info", None)
                state["results"]["ticket_data"] = ticket_data  # Store for potential redirect
                
                # 🆕 NEW: Assign ticket and create notification if call initiated successfully
                if vocal_result.get("status") in ["call_initiated", "redirect_call_initiated"]:
                    print(f"     📋 VOCAL ASSISTANT STEP: Call initiated - processing assignment and notification...")
                    
                    # 🔧 DEBUG: Show detailed state information
                    print(f"     🔧 DEBUG ASSIGNMENT: State metadata keys: {list(state.get('metadata', {}).keys())}")
                    print(f"     🔧 DEBUG ASSIGNMENT: State metadata: {state.get('metadata', {})}")
                    print(f"     🔧 DEBUG ASSIGNMENT: Ticket data: {ticket_data}")
                    print(f"     🔧 DEBUG ASSIGNMENT: Employee data: {employee_data}")
                    print(f"     🔧 DEBUG ASSIGNMENT: Vocal result: {vocal_result}")
                    print(f"     🔧 DEBUG ASSIGNMENT: Is redirect: {is_redirect}")
                    
                    # 1. Assign ticket to employee (if we have a real ticket ID)
                    real_ticket_id = state["metadata"].get("ticket_id") or ticket_data.get("real_id")
                    employee_username = employee_data.get("username")
                    call_info = vocal_result.get("call_info", {})
                    call_ticket_id = call_info.get("ticket_id")
                    
                    print(f"     🔧 DEBUG ASSIGNMENT: real_ticket_id from metadata: {state['metadata'].get('ticket_id')}")
                    print(f"     🔧 DEBUG ASSIGNMENT: real_ticket_id from ticket_data: {ticket_data.get('real_id')}")
                    print(f"     🔧 DEBUG ASSIGNMENT: final real_ticket_id: {real_ticket_id}")
                    print(f"     🔧 DEBUG ASSIGNMENT: employee_username: {employee_username}")
                    print(f"     🔧 DEBUG ASSIGNMENT: call_ticket_id: {call_ticket_id}")
                    
                    if real_ticket_id and employee_username:
                        try:
                            print(f"     🔧 DEBUG ASSIGNMENT: Starting ticket assignment process...")
                            # Use imported ticket manager
                            if FRONT_MODULES_AVAILABLE and TicketManager:
                                ticket_manager = TicketManager()
                                print(f"     🔧 DEBUG ASSIGNMENT: TicketManager created successfully")
                                
                                # Check if ticket exists before assignment
                                print(f"     🔧 DEBUG ASSIGNMENT: Checking if ticket {real_ticket_id} exists...")
                                existing_ticket = ticket_manager.get_ticket_by_id(real_ticket_id)
                                print(f"     🔧 DEBUG ASSIGNMENT: Existing ticket: {existing_ticket}")
                                
                                if existing_ticket:
                                    print(f"     🔧 DEBUG ASSIGNMENT: Ticket found, current assigned_to: {existing_ticket.get('assigned_to', 'None')}")
                                    print(f"     🔧 DEBUG ASSIGNMENT: Calling assign_ticket({real_ticket_id}, {employee_username})")
                                    assignment_result = ticket_manager.assign_ticket(real_ticket_id, employee_username)
                                    print(f"     🔧 DEBUG ASSIGNMENT: Assignment result: {assignment_result}")
                                    
                                    # Verify assignment worked
                                    updated_ticket = ticket_manager.get_ticket_by_id(real_ticket_id)
                                    print(f"     🔧 DEBUG ASSIGNMENT: Updated ticket: {updated_ticket}")
                                    print(f"     🔧 DEBUG ASSIGNMENT: New assigned_to: {updated_ticket.get('assigned_to') if updated_ticket else 'TICKET_NOT_FOUND'}")
                                    
                                    print(f"     ✅ TICKET ASSIGNMENT: Assigned ticket {real_ticket_id} to {employee_username}")
                                else:
                                    print(f"     ❌ DEBUG ASSIGNMENT: Ticket {real_ticket_id} does not exist in database!")
                            else:
                                print(f"     ❌ DEBUG ASSIGNMENT: TicketManager not available - front modules not imported")
                                
                        except Exception as e:
                            print(f"     ❌ TICKET ASSIGNMENT: Failed to assign ticket: {e}")
                            import traceback
                            print(f"     ❌ TICKET ASSIGNMENT: Full traceback: {traceback.format_exc()}")
                    else:
                        print(f"     ⚠️ TICKET ASSIGNMENT: Missing ticket ID ({real_ticket_id}) or username ({employee_username})")
                    
                    # 2. Create call notification for employee
                    try:
                        print(f"     🔧 DEBUG NOTIFICATION: Starting notification creation...")
                        # Use imported database manager
                        if FRONT_MODULES_AVAILABLE and DatabaseManager:
                            db = DatabaseManager()
                            print(f"     🔧 DEBUG NOTIFICATION: DatabaseManager created successfully")
                            
                            print(f"     🔧 DEBUG NOTIFICATION: Call info for notification: {call_info}")
                            print(f"     🔧 DEBUG NOTIFICATION: Target employee: {employee_username}")
                            print(f"     🔧 DEBUG NOTIFICATION: Ticket ID: {call_info.get('ticket_id', 'unknown')}")
                            
                            notification_success = db.create_call_notification(
                                target_employee=employee_username,
                                ticket_id=call_info.get("ticket_id", "unknown"),
                                ticket_subject=call_info.get("ticket_subject", "Support Request"),
                                caller_name="System Redirect" if is_redirect else "User Request",
                                call_info=call_info
                            )
                            
                            print(f"     🔧 DEBUG NOTIFICATION: Notification creation result: {notification_success}")
                            
                            if notification_success:
                                print(f"     ✅ CALL NOTIFICATION: Created notification for {employee_username}")
                                
                                # Verify notification was created
                                pending_calls = db.get_pending_calls(employee_username)
                                print(f"     🔧 DEBUG NOTIFICATION: {employee_username} now has {len(pending_calls)} pending calls")
                            else:
                                print(f"     ⚠️ CALL NOTIFICATION: Failed to create notification for {employee_username}")
                        else:
                            print(f"     ❌ DEBUG NOTIFICATION: DatabaseManager not available - front modules not imported")
                            
                    except Exception as e:
                        print(f"     ❌ CALL NOTIFICATION: Error creating notification: {e}")
                        import traceback
                        print(f"     ❌ CALL NOTIFICATION: Full traceback: {traceback.format_exc()}")
                
                print(f"     ✅ VOCAL ASSISTANT STEP: Call initiated successfully")
                print(f"        - Result: {vocal_result.get('result', 'No result')}")
                print(f"        - Action: {vocal_result.get('action', 'No action')}")
                print(f"     ✅ VOCAL ASSISTANT STEP: Proceeding to redirect check...\n")
            else:
                print(f"     ⚠️ VOCAL ASSISTANT STEP: Vocal Assistant not available!")
                state["results"]["vocal_assistant"] = {"result": "Vocal Assistant not available", "action": "error", "status": "error"}
                state["results"]["vocal_action"] = "no_call"
        else:
            print(f"     ⚠️ VOCAL ASSISTANT STEP: No employee assigned for voice call")
            print(f"        - HR Action: {hr_action}")
            print(f"        - Employee Data: {'Available' if employee_data else 'None'}")
            state["results"]["vocal_assistant"] = {"result": "No employee assigned for voice call", "action": "no_assignment", "status": "error"}
            state["results"]["vocal_action"] = "no_call"
        
        return state

    @observe()
    def _maestro_final_step(self, state: WorkflowState) -> WorkflowState:
        """Final Maestro step - format employee referral response or voice call result."""
        print(f"\n     🎯 MAESTRO FINAL: Multi-agent collaboration completed - delivering results...")
        state = state.copy()
        state["current_step"] = "maestro_final"
        
        # Get query and results
        query = state.get("query", "")
        hr_result = state["results"].get("hr_agent", "")
        vocal_action = state["results"].get("vocal_action", "no_call")
        call_info = state["results"].get("call_info", None)
        
        # Check if this is post-redirect processing
        redirect_call_result = state["results"].get("redirect_call_result", None)
        conversation_data = state["results"].get("conversation_data", None)

        print(f"     🎯 MAESTRO FINAL: Processing final results...")
        print(f"        - Query: {query}")
        print(f"        - Vocal action: {vocal_action}")
        print(f"        - Has redirect result: {'Yes' if redirect_call_result else 'No'}")
        print(f"        - Has conversation data: {'Yes' if conversation_data else 'No'}")
        print(f"        - Call info available: {'Yes' if call_info else 'No'}")
        
        if redirect_call_result:
            print(f"     🎯 MAESTRO FINAL: Processing redirect call result...")
            # This is a redirect completion - format the redirect call result
            if conversation_data:
                print(f"     🎯 MAESTRO FINAL: Formatting redirect conversation data...")
                vocal_response = VocalResponse(conversation_data)
                if vocal_response.conversation_complete:
                    print(f"     ✅ MAESTRO FINAL: Redirect conversation completed successfully")
                    state["results"]["maestro_final"] = f"Ticket successfully redirected and resolved by {redirect_call_result.get('employee_name', 'redirected employee')}. Solution: {vocal_response.solution}"
                else:
                    print(f"     ⚠️ MAESTRO FINAL: Redirect conversation incomplete")
                    state["results"]["maestro_final"] = f"Ticket redirected to {redirect_call_result.get('employee_name', 'employee')} but conversation is incomplete."
            else:
                print(f"     ⚠️ MAESTRO FINAL: No conversation data from redirect")
                state["results"]["maestro_final"] = f"Ticket redirect initiated but no conversation data available."
        else:
            print(f"     🎯 MAESTRO FINAL: Processing normal workflow completion...")
            # Normal workflow completion
        print(f"        - Has call info: {bool(call_info)}")
        print(f"        - Has redirect result: {bool(redirect_call_result)}")
        print(f"        - Has conversation data: {bool(conversation_data)}")
        
        if redirect_call_result and conversation_data:
            print(f"     🎯 MAESTRO FINAL: Processing redirect call results...")
            # This is a redirect scenario - synthesize the final solution professionally
            raw_conversation = conversation_data.get('response', conversation_data.get('conversation_summary', 'Solution details recorded.'))
            
            print(f"     🎯 MAESTRO FINAL: Synthesizing professional solution from redirect conversation...")
            try:
                maestro_agent = self.agents.get("maestro")
                if maestro_agent:
                    synthesis_input = {
                        "query": query,
                        "stage": "synthesize",
                        "data_guardian_result": f"SCOPE_STATUS: IN_SCOPE\nINFORMATION_FOUND: YES\n\nRedirect Conversation Summary:\n{raw_conversation}\n\nThe above represents a completed conversation between the user and a redirected expert ({redirect_call_result.get('employee_name', 'redirected employee')}). Please synthesize this into a clean, professional support response."
                    }
                    synthesis_result = maestro_agent.run(synthesis_input)
                    if synthesis_result.get("status") == "success":
                        synthesized_response = synthesis_result.get("result", "")
                        if synthesized_response and len(synthesized_response.strip()) > 50:
                            final_response = synthesized_response
                            print(f"     ✅ MAESTRO FINAL: Professional redirect synthesis completed (length: {len(final_response)})")
                        else:
                            raise Exception("Synthesis result too short or empty")
                    else:
                        raise Exception(f"Synthesis failed: {synthesis_result.get('status')}")
                else:
                    raise Exception("MaestroAgent not available")
                    
            except Exception as e:
                print(f"     ⚠️ MAESTRO FINAL: Redirect synthesis failed ({e}), using fallback template")
                # Fallback to template if synthesis fails
                final_response = f"""Your ticket has been successfully redirected and resolved.

{hr_result}

Solution provided by the assigned expert:
{raw_conversation}

Your issue has been handled by the most appropriate team member."""
            print(f"     ✅ MAESTRO FINAL: Redirect solution formatted")
        elif vocal_action == "start_call" and call_info:
            print(f"     🎯 MAESTRO FINAL: Processing initial call initiation...")
            # Voice call initiated - provide call information
            final_response = f"""Your ticket has been assigned to {call_info.get('employee_name', 'an expert')} who will contact you shortly.

{hr_result}

A voice call is being initiated to discuss your issue in detail and provide a personalized solution."""
            print(f"     ✅ MAESTRO FINAL: Call initiation response formatted")
        elif vocal_action == "end_call":
            print(f"     🎯 MAESTRO FINAL: Processing completed call without redirect...")
            # Call was completed but no redirect was requested
            conversation_summary = state["results"].get("call_conversation_summary", "")
            if conversation_summary:
                print(f"     🎯 MAESTRO FINAL: Synthesizing professional solution from conversation...")
                # Use MaestroAgent to synthesize a professional response from the conversation
                try:
                    maestro_agent = self.agents.get("maestro")
                    if maestro_agent:
                        synthesis_input = {
                            "query": query,
                            "stage": "synthesize", 
                            "data_guardian_result": f"SCOPE_STATUS: IN_SCOPE\nINFORMATION_FOUND: YES\n\nConversation Summary:\n{conversation_summary}\n\nThe above represents a completed conversation between the user and a support representative. Please synthesize this into a clean, professional support response."
                        }
                        synthesis_result = maestro_agent.run(synthesis_input)
                        if synthesis_result.get("status") == "success":
                            synthesized_response = synthesis_result.get("result", "")
                            if synthesized_response and len(synthesized_response.strip()) > 50:
                                final_response = synthesized_response
                                print(f"     ✅ MAESTRO FINAL: Professional synthesis completed (length: {len(final_response)})")
                            else:
                                raise Exception("Synthesis result too short or empty")
                        else:
                            raise Exception(f"Synthesis failed: {synthesis_result.get('status')}")
                    else:
                        raise Exception("MaestroAgent not available")
                        
                except Exception as e:
                    print(f"     ⚠️ MAESTRO FINAL: Synthesis failed ({e}), using fallback template")
                    # Fallback to template if synthesis fails
                    final_response = f"""Your ticket has been resolved through a voice conversation.

{hr_result}

Solution details:
{conversation_summary}

Your issue has been addressed by our expert team member."""
            else:
                final_response = f"""Your ticket has been processed through a voice conversation.

{hr_result}

The assigned expert has addressed your issue. If you need further assistance, please don't hesitate to reach out."""
            print(f"     ✅ MAESTRO FINAL: Call completion response prepared")
        else:
            print(f"     🎯 MAESTRO FINAL: Processing standard HR referral...")
            # Standard HR referral response
            final_response = f"""I couldn't find a direct answer in our knowledge base for your request, but I can help connect you with the right expert.

{hr_result}

Please reach out to them directly - they'll be able to provide specialized assistance with your specific issue."""
            print(f"     ✅ MAESTRO FINAL: Standard referral response formatted")
        
        state["results"]["final_response"] = final_response
        state["results"]["synthesis"] = final_response  # Update synthesis for consistency
        
        print(f"     🎯 MAESTRO FINAL: Final response prepared (length: {len(final_response)})")
        print(f"     🎯 MAESTRO FINAL: Workflow completion successful! 🎉\n")
        
        return state
    
    # 🆕 NEW WORKFLOW STEPS for redirect functionality
    
    def _check_for_redirect(self, state: WorkflowState) -> str:
        """Check if vocal assistant conversation indicates redirect needed."""
        print(f"\n   🔍 REDIRECT CHECK: Starting redirect detection...")
        print(f"   🔍 REDIRECT CHECK: State keys: {list(state.get('results', {}).keys())}")
        
        # Get conversation data from call completion
        conversation_summary = state["results"].get("call_conversation_summary", "")
        conversation_data = state["results"].get("call_conversation_data", {})
        
        print(f"   🔍 REDIRECT CHECK: Conversation summary length: {len(conversation_summary) if conversation_summary else 0}")
        print(f"   🔍 REDIRECT CHECK: Conversation data keys: {list(conversation_data.keys()) if conversation_data else 'None'}")
         # Use conversation summary as primary source, fallback to conversation data
        response_text = conversation_summary
        if not response_text and conversation_data:
            response_text = conversation_data.get("conversation_summary", conversation_data.get("response", ""))
        
        # If still no response text, check vocal assistant result as fallback
        if not response_text:
            vocal_result = state["results"].get("vocal_assistant", {})
            if isinstance(vocal_result, dict):
                response_text = (vocal_result.get("response") or 
                               vocal_result.get("conversation_summary") or 
                               vocal_result.get("conversation", "") or
                               vocal_result.get("result", ""))

        print(f"   🔍 REDIRECT CHECK: Response text length: {len(response_text) if response_text else 0}")
        if response_text:
            print(f"   🔍 REDIRECT CHECK: Response preview: {response_text[:100]}...")
        else:
            print(f"   ⚠️ REDIRECT CHECK: No response text found!")
            return "complete"  # No conversation data, complete normally

        # 🔧 CRITICAL FIX: If response text is raw conversation, analyze it first
        if response_text and not ("REDIRECT_REQUESTED:" in response_text):
            print(f"   🔍 REDIRECT CHECK: Raw conversation detected, analyzing with AI...")
            
            # Get vocal assistant agent for conversation analysis
            vocal_agent = None
            if hasattr(self, 'agents') and 'vocal_assistant' in self.agents:
                vocal_agent = self.agents['vocal_assistant']
            
            if vocal_agent and hasattr(vocal_agent, '_analyze_conversation_for_redirect'):
                try:
                    analyzed_result = vocal_agent._analyze_conversation_for_redirect(response_text)
                    if analyzed_result and analyzed_result.get('redirect_requested') is not None:
                        print(f"   ✅ REDIRECT CHECK: AI analysis completed successfully")
                        # Use the analyzed result directly instead of parsing again
                        vocal_response = type('VocalResponse', (), {
                            'redirect_requested': analyzed_result.get('redirect_requested', False),
                            'redirect_employee_info': analyzed_result.get('redirect_employee_info', {}),
                            'conversation_complete': not analyzed_result.get('redirect_requested', False)
                        })()
                        
                        print(f"   🔍 REDIRECT CHECK: Redirect requested: {vocal_response.redirect_requested}")
                        print(f"   🔍 REDIRECT CHECK: Redirect info: {vocal_response.redirect_employee_info}")
                        print(f"   🔍 REDIRECT CHECK: Conversation complete: {vocal_response.conversation_complete}")
                        
                        if vocal_response.redirect_requested:
                            state["results"]["redirect_info"] = vocal_response.redirect_employee_info
                            print(f"   ✅ REDIRECT CHECK: REDIRECT DETECTED! Storing info and routing to redirect_detector")
                            print(f"   ✅ REDIRECT CHECK: Redirect info stored: {vocal_response.redirect_employee_info}")
                            return "redirect"
                        
                        print(f"   ✅ REDIRECT CHECK: No redirect requested, marking complete")
                        return "complete"
                    else:
                        print(f"   ⚠️ REDIRECT CHECK: AI analysis returned invalid result: {analyzed_result}")
                except Exception as e:
                    print(f"   ⚠️ REDIRECT CHECK: AI analysis error: {e}")
            else:
                print(f"   ⚠️ REDIRECT CHECK: No vocal agent available for AI analysis")

        conversation_data_for_analysis = {"response": response_text}
        print(f"   🔍 REDIRECT CHECK: Creating VocalResponse object...")
        vocal_response = VocalResponse(conversation_data_for_analysis)
        
        print(f"   🔍 REDIRECT CHECK: Redirect requested: {vocal_response.redirect_requested}")
        print(f"   🔍 REDIRECT CHECK: Redirect info: {vocal_response.redirect_employee_info}")
        print(f"   🔍 REDIRECT CHECK: Conversation complete: {vocal_response.conversation_complete}")
        
        if vocal_response.redirect_requested:
            state["results"]["redirect_info"] = vocal_response.redirect_employee_info
            print(f"   ✅ REDIRECT CHECK: REDIRECT DETECTED! Storing info and routing to redirect_detector")
            print(f"   ✅ REDIRECT CHECK: Redirect info stored: {vocal_response.redirect_employee_info}")
            return "redirect"
        
        print(f"   ✅ REDIRECT CHECK: No redirect requested, marking complete")
        return "complete"

    @observe()
    def _redirect_detector_step(self, state: WorkflowState) -> WorkflowState:
        """Analyze conversation for redirect request details."""
        state = state.copy()
        state["current_step"] = "redirect_detector"
        
        print(f"\n     🔄 REDIRECT DETECTOR: Analyzing redirect request...")
        
        # Get redirect info and ticket data
        redirect_info = state["results"].get("redirect_info", {})
        ticket_data = state["results"].get("ticket_data", {})
        
        print(f"     🔄 REDIRECT DETECTOR: Received redirect info: {redirect_info}")
        print(f"     🔄 REDIRECT DETECTOR: Ticket ID: {ticket_data.get('id', 'unknown')}")
        
        # 🆕 REDIRECT LOOP PREVENTION: Check redirect limits
        if not self._validate_redirect_limits(ticket_data):
            print(f"     🚨 REDIRECT DETECTOR: Redirect limit exceeded - escalating to manager...")
            
            # Mark as escalation instead of redirect
            state["results"]["escalation_required"] = True
            state["results"]["escalation_reason"] = "Maximum redirect limit exceeded"
            
            # TODO: Add escalation workflow
            print(f"     🚨 REDIRECT DETECTOR: Escalation marked - workflow will handle appropriately")
            
            return state
        
        # Check if we're trying to redirect to previous assignees (prevent ping-pong)
        redirect_history = ticket_data.get("redirect_history", [])
        requested_user = redirect_info.get("username", "").lower()
        
        if requested_user and requested_user in [user.lower() for user in redirect_history]:
            print(f"     � REDIRECT DETECTOR: Ping-pong redirect detected!")
            print(f"        - Requested user '{requested_user}' already in history: {redirect_history}")
            
            # Modify redirect info to exclude previous assignees
            redirect_info["exclude_usernames"] = redirect_history
            print(f"     🔄 REDIRECT DETECTOR: Added exclusion list: {redirect_history}")
        
        # Store enhanced redirect info for employee search
        state["results"]["enhanced_redirect_info"] = redirect_info
        
        print(f"     🔄 REDIRECT DETECTOR: Enhanced redirect info stored")
        print(f"     🔄 REDIRECT DETECTOR: Proceeding to employee search...\n")
        
        return state

    @observe()
    def _employee_searcher_step(self, state: WorkflowState) -> WorkflowState:
        """Search for employees matching redirect criteria."""
        state = state.copy()
        state["current_step"] = "employee_searcher"
        
        print(f"\n     🔍 EMPLOYEE SEARCHER: Finding matching employees...")
        
        redirect_info = state["results"].get("enhanced_redirect_info", {})
        print(f"     🔍 EMPLOYEE SEARCHER: Search criteria: {redirect_info}")
        
        # Use employee search tool to find matches
        if "employee_search_tool" in self.agents:
            print(f"     🔍 EMPLOYEE SEARCHER: Using EmployeeSearchTool...")
            search_results = self.agents["employee_search_tool"].search_employees_for_redirect(redirect_info)
            print(f"     🔍 EMPLOYEE SEARCHER: Raw search results count: {len(search_results)}")
            
            # Debug each candidate
            for i, candidate in enumerate(search_results):
                print(f"     🔍 EMPLOYEE SEARCHER: Candidate {i+1}: {candidate.get('full_name', 'Unknown')} (Score: {candidate.get('redirect_score', 0)})")
                print(f"        - Username: {candidate.get('username', 'None')}")
                print(f"        - Role: {candidate.get('role_in_company', 'None')}")  
                print(f"        - Match reasons: {candidate.get('match_reasons', [])}")
        else:
            print(f"     ⚠️ EMPLOYEE SEARCHER: EmployeeSearchTool not available!")
            search_results = []
        
        state["results"]["redirect_candidates"] = search_results
        
        print(f"     ✅ EMPLOYEE SEARCHER: Found {len(search_results)} potential employees for redirect")
        print(f"     ✅ EMPLOYEE SEARCHER: Proceeding to maestro selection...\n")
        
        return state

    @observe()
    def _maestro_redirect_selector_step(self, state: WorkflowState) -> WorkflowState:
        """Maestro selects best employee for redirection."""
        state = state.copy()
        state["current_step"] = "maestro_redirect_selector"
        
        print(f"\n     🎯 MAESTRO REDIRECT SELECTOR: Choosing best employee...")
        
        candidates = state["results"].get("redirect_candidates", [])
        redirect_info = state["results"].get("enhanced_redirect_info", {})
        
        print(f"     🎯 MAESTRO REDIRECT SELECTOR: Number of candidates: {len(candidates)}")
        print(f"     🎯 MAESTRO REDIRECT SELECTOR: Selection criteria: {redirect_info}")
        
        if "maestro" in self.agents and candidates:
            # Format candidates for Maestro selection
            candidates_text = "\n".join([
                f"- {emp.get('full_name', 'Unknown')} ({emp.get('username', '')}) - {emp.get('role_in_company', '')} - Score: {emp.get('redirect_score', 0)} - Reasons: {', '.join(emp.get('match_reasons', []))}"
                for emp in candidates
            ])
            
            print(f"     🎯 MAESTRO REDIRECT SELECTOR: Consulting Maestro for selection...")
            selection_result = self.agents["maestro"].run({
                "query": f"Select the best employee for redirect based on: {redirect_info}. Candidates:\n{candidates_text}",
                "stage": "redirect_selection"
            })
            print(f"     🎯 MAESTRO REDIRECT SELECTOR: Maestro selection result: {selection_result}")
            
            # For now, select the highest scoring candidate
            # TODO: Enhance Maestro to make intelligent selection
            selected_employee = candidates[0] if candidates else {}
            state["results"]["selected_redirect_employee"] = selected_employee
            
            print(f"     ✅ MAESTRO REDIRECT SELECTOR: Selected employee: {selected_employee.get('full_name', 'None')}")
            print(f"        - Username: {selected_employee.get('username', 'None')}")
            print(f"        - Role: {selected_employee.get('role_in_company', 'None')}")
            print(f"        - Score: {selected_employee.get('redirect_score', 0)}")
            
            # 🔧 CRITICAL FIX: Format data for vocal_assistant (same as HR assignment)
            if selected_employee:
                print(f"     🔧 MAESTRO REDIRECT SELECTOR: Formatting data for vocal_assistant...")
                
                # Get original ticket data 
                original_ticket = state["results"].get("ticket_data", {})
                
                # Format as HR assignment result (what vocal_assistant expects)
                state["results"]["hr_action"] = "assign"
                state["results"]["employee_data"] = selected_employee
                
                # Prepare redirect context for the new call
                redirect_context = {
                    "is_redirect": True,
                    "original_employee": state["results"].get("hr_agent", {}).get("employee", "Unknown"),
                    "redirect_reason": redirect_info.get("responsibilities", "Specialized expertise needed"),
                    "redirect_info": redirect_info
                }
                
                # Store redirect context for vocal assistant
                state["results"]["redirect_context"] = redirect_context
                
                print(f"     ✅ MAESTRO REDIRECT SELECTOR: Data formatted for vocal_assistant")
                print(f"        - HR Action: {state['results']['hr_action']}")
                print(f"        - Employee: {selected_employee.get('full_name', 'None')}")
                print(f"        - Redirect Context: {redirect_context['redirect_reason']}")
            else:
                print(f"     ❌ MAESTRO REDIRECT SELECTOR: No employee selected, cannot format data")
            
            print(f"     ✅ MAESTRO REDIRECT SELECTOR: Proceeding to vocal_assistant...\n")
        else:
            if not candidates:
                print(f"     ⚠️ MAESTRO REDIRECT SELECTOR: No candidates found!")
            if "maestro" not in self.agents:
                print(f"     ⚠️ MAESTRO REDIRECT SELECTOR: Maestro agent not available!")
        
        return state

    @observe()
    def _vocal_assistant_redirect_step(self, state: WorkflowState) -> WorkflowState:
        """Initiate call with redirected employee."""
        state = state.copy()
        state["current_step"] = "vocal_assistant_redirect"
        
        print(f"\n     📞 VOCAL ASSISTANT REDIRECT: Calling redirected employee...")
        
        new_employee = state["results"].get("selected_redirect_employee", {})
        original_ticket = state["results"].get("ticket_data", {})
        redirect_reason = state["results"].get("enhanced_redirect_info", {})
        
        print(f"     📞 VOCAL ASSISTANT REDIRECT: New employee: {new_employee.get('full_name', 'None')}")
        print(f"     📞 VOCAL ASSISTANT REDIRECT: Ticket ID: {original_ticket.get('id', 'Unknown')}")
        print(f"     📞 VOCAL ASSISTANT REDIRECT: Redirect reason: {redirect_reason}")
        
        if "vocal_assistant" in self.agents and new_employee:
            print(f"     📞 VOCAL ASSISTANT REDIRECT: Initiating redirect call...")
            redirect_result = self.agents["vocal_assistant"].run({
                "action": "initiate_redirect_call",
                "ticket_data": original_ticket,
                "employee_data": new_employee,
                "redirect_reason": redirect_reason
            })
            
            print(f"     📞 VOCAL ASSISTANT REDIRECT: Redirect call result: {redirect_result}")
            state["results"]["redirect_call_result"] = redirect_result
            
            # Parse the redirect call result for potential further redirects
            if redirect_result.get("status") == "success":
                redirect_conversation = redirect_result.get("conversation_data", {})
                print(f"     📞 VOCAL ASSISTANT REDIRECT: Got conversation data, checking for further redirects...")
                
                vocal_response = VocalResponse(redirect_conversation)
                
                # Update conversation data for final processing
                state["results"]["conversation_data"] = redirect_conversation
                
                # Check if this redirect call also requests another redirect
                if vocal_response.redirect_requested:
                    # For now, we'll end here to avoid infinite loops
                    # TODO: Could implement multi-level redirection with safeguards
                    print(f"     ⚠️ VOCAL ASSISTANT REDIRECT: Further redirect requested but stopping to prevent loops")
                else:
                    print(f"     ✅ VOCAL ASSISTANT REDIRECT: Redirect call successful, no further redirects")
            else:
                print(f"     ⚠️ VOCAL ASSISTANT REDIRECT: Redirect call failed or incomplete")
        else:
            if not new_employee:
                print(f"     ⚠️ VOCAL ASSISTANT REDIRECT: No employee selected for redirect!")
            if "vocal_assistant" not in self.agents:
                print(f"     ⚠️ VOCAL ASSISTANT REDIRECT: VocalAssistant not available!")
        
        print(f"     ✅ VOCAL ASSISTANT REDIRECT: Redirect step complete, proceeding to final maestro...\n")
        
        return state
    
    # 🆕 NEW WORKFLOW STEP: Call Completion Handler
    
    def _call_completion_handler_step(self, state: WorkflowState) -> WorkflowState:
        """Handle call completion and determine next steps."""
        state = state.copy()
        state["current_step"] = "call_completion_handler"
        
        print(f"\n     📞 CALL COMPLETION HANDLER: Analyzing call status...")
        
        # Get vocal assistant result
        vocal_result = state["results"].get("vocal_assistant", {})
        call_action = vocal_result.get("action", "")
        call_status = vocal_result.get("status", "")
        
        print(f"     📞 CALL COMPLETION HANDLER: Call action: {call_action}")
        print(f"     📞 CALL COMPLETION HANDLER: Call status: {call_status}")
        
        # Check if this is an actual call completion (end_call) vs call initiation
        if call_action == "end_call":
            print(f"     📞 CALL COMPLETION HANDLER: Call ended - checking for redirect...")
            state["results"]["call_completed"] = True
            # 🔧 FIXED: Set vocal_action for maestro_final to recognize end_call
            state["results"]["vocal_action"] = "end_call"
            
            # Extract conversation data for redirect analysis
            conversation_summary = vocal_result.get("conversation_summary", "")
            conversation_data = vocal_result.get("conversation_data", {})
            
            print(f"     📞 CALL COMPLETION HANDLER: Conversation summary available: {'Yes' if conversation_summary else 'No'}")
            print(f"     📞 CALL COMPLETION HANDLER: Conversation data available: {'Yes' if conversation_data else 'No'}")
            
            # Store conversation data for redirect analysis
            if conversation_summary or conversation_data:
                state["results"]["call_conversation_summary"] = conversation_summary
                state["results"]["call_conversation_data"] = conversation_data
                print(f"     📞 CALL COMPLETION HANDLER: Stored conversation data for redirect analysis")
            
        elif call_action == "start_call" or call_status == "call_initiated":
            print(f"     📞 CALL COMPLETION HANDLER: Call initiated - waiting for completion...")
            # Call was just started, not completed yet - workflow should complete here
            state["results"]["call_completed"] = False
            # 🔧 FIXED: Set vocal_action for maestro_final
            state["results"]["vocal_action"] = "start_call"
        else:
            print(f"     📞 CALL COMPLETION HANDLER: Unknown call state - treating as incomplete...")
            state["results"]["call_completed"] = False
        
        print(f"     📞 CALL COMPLETION HANDLER: Call completed: {state['results']['call_completed']}")
        print(f"     📞 CALL COMPLETION HANDLER: Processing complete...\n")
        
        return state

    def _check_call_completion(self, state: WorkflowState) -> str:
        """Conditional routing based on call completion status."""
        call_completed = state["results"].get("call_completed", False)
        
        print(f"   🔍 CALL ROUTING: Call completed: {call_completed}")
        
        if call_completed:
            print(f"   🔍 CALL ROUTING: Call ended - checking for redirect...")
            return self._check_for_redirect(state)
        else:
            print(f"   🔍 CALL ROUTING: Call ongoing or just initiated - completing workflow...")
            return "complete"
    
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
        
        # Try to run the graph workflow, fallback to simple execution
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state["results"]
        except Exception as e:
            print(f"⚠️ Graph execution failed: {e}")
            print("🔄 Falling back to manual workflow execution...")
            # Fallback: run agents manually in sequence
            # print(f"Running fallback workflow for: {query}")
            
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
    
    # 🆕 TICKET MANAGEMENT FUNCTIONS
    
    def _reset_ticket_assignment(self, ticket_data: Dict, redirect_info: Dict) -> Dict:
        """Reset ticket assignment fields for redirect while preserving history."""
        print(f"   🎫 TICKET RESET: Resetting assignment for ticket {ticket_data.get('id', 'unknown')}")
        
        current_assignee = ticket_data.get("assigned_to")
        redirect_count = ticket_data.get("redirect_count", 0)
        redirect_history = ticket_data.get("redirect_history", [])
        
        print(f"   🎫 TICKET RESET: Current assignee: {current_assignee}")
        print(f"   🎫 TICKET RESET: Current redirect count: {redirect_count}")
        
        # Update redirect history
        if current_assignee and current_assignee not in redirect_history:
            redirect_history.append(current_assignee)
        
        # Create reset ticket data
        reset_ticket = {
            **ticket_data,
            # Clear assignment fields
            "assigned_to": None,
            "assignment_status": "pending_reassignment",
            "assignment_date": None,
            "employee_solution": None,
            "completion_date": None,
            # Update redirect tracking
            "redirect_count": redirect_count + 1,
            "redirect_history": redirect_history,
            "redirect_reason": redirect_info.get("reason", "Employee requested reassignment"),
            "previous_assignee": current_assignee,
            "redirect_timestamp": datetime.now().isoformat(),
            "redirect_requested": True,
            "call_status": "redirect_pending"
        }
        
        print(f"   🎫 TICKET RESET: Updated redirect count: {reset_ticket['redirect_count']}")
        print(f"   🎫 TICKET RESET: Redirect history: {reset_ticket['redirect_history']}")
        print(f"   🎫 TICKET RESET: Reset completed successfully")
        
        return reset_ticket
    
    def _validate_redirect_limits(self, ticket_data: Dict) -> bool:
        """Check if ticket has exceeded redirect limits."""
        redirect_count = ticket_data.get("redirect_count", 0)
        max_redirects = ticket_data.get("max_redirects", 3)
        
        print(f"   🚨 REDIRECT LIMIT CHECK: Count {redirect_count}/{max_redirects}")
        
        if redirect_count >= max_redirects:
            print(f"   🚨 REDIRECT LIMIT EXCEEDED: Ticket has reached maximum redirects")
            return False
        
        print(f"   ✅ REDIRECT LIMIT OK: {max_redirects - redirect_count} redirects remaining")
        return True
    
    @observe()
    def process_end_call(self, end_call_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process END_CALL directly without going through the broken LangGraph routing.
        This bypasses the hardcoded entry point and state overwriting issues.
        """
        print(f"\n🔄 PROCESSING END_CALL DIRECTLY (bypassing broken graph routing)")
        print(f"🔄 END_CALL: Input state keys: {list(end_call_state.keys())}")
        
        try:
            # Convert input to proper WorkflowState format
            state: WorkflowState = {
                "messages": end_call_state.get("messages", []),
                "current_step": "call_completion_handler",
                "results": end_call_state.get("results", {}),
                "metadata": end_call_state.get("metadata", {}),
                "query": ""  # Empty query for END_CALL processing
            }
            
            print(f"🔄 END_CALL: Starting call completion handler...")
            
            # Step 1: Process call completion
            state = self._call_completion_handler_step(state)
            call_completed = state["results"].get("call_completed", False)
            
            print(f"🔄 END_CALL: Call completed: {call_completed}")
            
            if not call_completed:
                print(f"🔄 END_CALL: Call not completed, finishing workflow")
                # Call not completed, just finish
                state = self._maestro_final_step(state)
                return state["results"]
            
            # Step 2: Check for redirect
            print(f"🔄 END_CALL: Checking for redirect...")
            redirect_decision = self._check_for_redirect(state)
            
            if redirect_decision == "redirect":
                print(f"🔄 END_CALL: REDIRECT DETECTED - Processing redirect workflow")
                
                # Step 3a: Process redirect flow
                state = self._redirect_detector_step(state)
                state = self._employee_searcher_step(state)
                state = self._maestro_redirect_selector_step(state)
                state = self._vocal_assistant_step(state)  # 🔧 FIXED: Use regular vocal_assistant, not redirect version
                
                # 🔧 FIXED: Add missing call completion handler for redirect flow
                state = self._call_completion_handler_step(state)
                
            else:
                print(f"🔄 END_CALL: No redirect detected - completing normally")
            
            # 🔧 CHECK: Only continue to final processing if call is completed
            call_completed = state.get("results", {}).get("call_completed", True)
            if call_completed:
                print(f"🔄 END_CALL: Call completed - proceeding to final processing")
                # Step 4: Final processing
                state = self._maestro_final_step(state)
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
            import traceback
            print(f"❌ END_CALL: Traceback: {traceback.format_exc()}")
            
            # Return error state
            return {
                "error": f"END_CALL processing failed: {str(e)}",
                "status": "error"
            }
