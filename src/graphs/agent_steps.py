"""
Agent step implementations for the workflow.
"""
from typing import Dict, Any
from langfuse import observe
from .workflow_state import WorkflowState

# Import front modules for ticket management and notifications
try:
    from front.tickets.ticket_manager import TicketManager
    from front.database import DatabaseManager
    FRONT_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AGENT_STEPS: Could not import front modules: {e}")
    TicketManager = None
    DatabaseManager = None
    FRONT_MODULES_AVAILABLE = False


class AgentSteps:
    """Agent step implementations for the multi-agent workflow."""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
    
    @observe()
    def maestro_preprocess_step(self, state: WorkflowState) -> WorkflowState:
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
    def data_guardian_step(self, state: WorkflowState) -> WorkflowState:
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
    def maestro_synthesize_step(self, state: WorkflowState) -> WorkflowState:
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
    
    @observe()
    def hr_agent_step(self, state: WorkflowState) -> WorkflowState:
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
            
            # Handle new Pydantic response format - status is a StatusEnum object
            status = hr_result.get("status")
            status_check = status and (str(status) == "StatusEnum.SUCCESS" or status.value == "success")
            
            if status_check:
                # Extract information from new structured response
                matched_employees = hr_result.get("matched_employees", [])
                recommended_assignment = hr_result.get("recommended_assignment")
                
                if matched_employees and recommended_assignment:
                    # Get the recommended employee data
                    recommended_employee = next(
                        (emp for emp in matched_employees if emp["employee_id"] == recommended_assignment), 
                        matched_employees[0] if matched_employees else None
                    )
                    
                    if recommended_employee:
                        state["results"]["hr_agent"] = hr_result.get("response", "Employee assigned successfully")
                        state["results"]["hr_action"] = "assign"
                        state["results"]["employee_data"] = recommended_employee
                        state["results"]["hr_response"] = hr_result
                    else:
                        state["results"]["hr_agent"] = "No suitable employees available at the moment"
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
    def vocal_assistant_step(self, state: WorkflowState) -> WorkflowState:
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
        
        print(f"     📞 VOCAL ASSISTANT STEP: HR action: {hr_action}")
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
                    # Use real ticket ID from metadata, not temp ID
                    real_ticket_id = state["metadata"].get("ticket_id", "unknown")
                    ticket_data = {
                        "id": real_ticket_id,
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
                
                # Assign ticket and create notification if call initiated successfully
                if vocal_result.get("status") in ["call_initiated", "redirect_call_initiated"]:
                    print(f"     📋 VOCAL ASSISTANT STEP: Call initiated - processing assignment and notification...")
                    
                    # 1. Assign ticket to employee (if we have a real ticket ID)
                    real_ticket_id = state["metadata"].get("ticket_id") or ticket_data.get("real_id")
                    employee_username = employee_data.get("username")
                    call_info = vocal_result.get("call_info", {})
                    call_ticket_id = call_info.get("ticket_id")
                    
                    if real_ticket_id and employee_username:
                        if FRONT_MODULES_AVAILABLE:
                            try:
                                db_manager = DatabaseManager()
                                db_manager.assign_ticket_to_employee(real_ticket_id, employee_username)
                                print(f"     ✅ VOCAL ASSISTANT STEP: Ticket {real_ticket_id} assigned to {employee_username}")
                            except Exception as e:
                                print(f"     ⚠️ VOCAL ASSISTANT STEP: Failed to assign ticket: {e}")
                        else:
                            print(f"     ⚠️ VOCAL ASSISTANT STEP: Database modules not available for ticket assignment")
                    else:
                        print(f"     ⚠️ VOCAL ASSISTANT STEP: Missing ticket ID or employee username for assignment")
                    
                    # 2. Create call notification for employee
                    try:
                        if FRONT_MODULES_AVAILABLE:
                            ticket_manager = TicketManager()
                            notification_result = ticket_manager.create_call_notification(
                                employee_username=employee_username,
                                ticket_data=ticket_data,
                                call_info=call_info
                            )
                            print(f"     ✅ VOCAL ASSISTANT STEP: Call notification created: {notification_result}")
                        else:
                            print(f"     ⚠️ VOCAL ASSISTANT STEP: TicketManager not available for notification")
                            
                    except Exception as e:
                        print(f"     ⚠️ VOCAL ASSISTANT STEP: Failed to create call notification: {e}")
                
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
    def maestro_final_step(self, state: WorkflowState) -> WorkflowState:
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
                        final_response = synthesis_result.get("result", raw_conversation)
                        print(f"     ✅ MAESTRO FINAL: Professional redirect solution synthesized")
                    else:
                        raise Exception(f"Synthesis failed: {synthesis_result.get('error', 'Unknown error')}")
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
                            "data_guardian_result": f"SCOPE_STATUS: IN_SCOPE\nINFORMATION_FOUND: YES\n\nCall Conversation Summary:\n{conversation_summary}\n\nThe above represents a completed voice conversation with our expert. Please synthesize this into a clean, professional support response."
                        }
                        synthesis_result = maestro_agent.run(synthesis_input)
                        if synthesis_result.get("status") == "success":
                            final_response = synthesis_result.get("result", conversation_summary)
                            print(f"     ✅ MAESTRO FINAL: Professional call solution synthesized")
                        else:
                            raise Exception(f"Synthesis failed: {synthesis_result.get('error', 'Unknown error')}")
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
