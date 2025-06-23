"""
Call completion and management handlers.
"""
from typing import Dict, Any
from langfuse import observe
from .workflow_state import WorkflowState

# Import redirect functionality
from src.agents.vocal_assistant import VocalResponse


class CallHandler:
    """Handles call completion and management operations."""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
    
    @observe()
    def call_completion_handler_step(self, state: WorkflowState) -> WorkflowState:
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
            # Set vocal_action for maestro_final to recognize end_call
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
            # Set vocal_action for maestro_final
            state["results"]["vocal_action"] = "start_call"
        else:
            print(f"     📞 CALL COMPLETION HANDLER: Unknown call state - treating as incomplete...")
            state["results"]["call_completed"] = False
        
        print(f"     📞 CALL COMPLETION HANDLER: Call completed: {state['results']['call_completed']}")
        print(f"     📞 CALL COMPLETION HANDLER: Processing complete...\n")
        
        return state
    
    def check_call_completion(self, state: WorkflowState) -> str:
        """Conditional routing based on call completion status."""
        call_completed = state["results"].get("call_completed", False)
        
        print(f"   🔍 CALL ROUTING: Call completed: {call_completed}")
        
        if call_completed:
            print(f"   🔍 CALL ROUTING: Call ended - checking for redirect...")
            return self.check_for_redirect(state)
        else:
            print(f"   🔍 CALL ROUTING: Call ongoing or just initiated - completing workflow...")
            return "complete"
    
    def check_for_redirect(self, state: WorkflowState) -> str:
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

        # If response text is raw conversation, analyze it first
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
                    else:
                        print(f"   ⚠️ REDIRECT CHECK: AI analysis returned invalid result")
                        return "complete"
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
