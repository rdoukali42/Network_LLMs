"""
Call completion and management handlers.
"""
from typing import Dict, Any
from langfuse import observe
from .workflow_state import WorkflowState

# Import redirect functionality  
try:
    from ..agents.vocal_assistant import VocalResponse
except ImportError:
    try:
        from agents.vocal_assistant import VocalResponse
    except ImportError:
        # Fallback for testing - create a mock VocalResponse
        class VocalResponse:
            def __init__(self, conversation_data):
                self.redirect_requested = False
                self.redirect_employee_info = {}


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
            print(f"     📞 CALL COMPLETION HANDLER: 🔧 FIXED: Call initiated - NOT COMPLETED")
            print(f"     📞 CALL COMPLETION HANDLER: 🔧 FIXED: Workflow will stop here to prevent premature ticket completion")
            # Call was just started, not completed yet - workflow should stop here
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
        """🔧 FIXED: Conditional routing based on call completion status."""
        call_completed = state["results"].get("call_completed", False)
        
        print(f"   🔍 CALL ROUTING: Call completed: {call_completed}")
        
        if call_completed:
            print(f"   🔍 CALL ROUTING: Call ended - checking for redirect...")
            return self.check_for_redirect(state)
        else:
            print(f"   🔍 CALL ROUTING: 🔧 FIXED: Call just initiated - stopping workflow (no premature completion)...")
            return "call_waiting"
    
    def check_for_redirect(self, state: WorkflowState) -> str:
        """🆕 ENHANCED: Check if vocal assistant conversation indicates redirect needed."""
        print(f"\n   🔍 REDIRECT CHECK: Starting enhanced redirect detection...")
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

        print(f"   🔍 REDIRECT CHECK: Final response text length: {len(response_text) if response_text else 0}")
        if response_text:
            print(f"   🔍 REDIRECT CHECK: Response preview: {response_text[:200]}...")
            print(f"   🔍 REDIRECT CHECK: 🔧 DEBUG: Looking for redirect keywords in conversation...")
            
            # Quick keyword check for debugging
            redirect_keywords = ["redirect", "transfer", "forward", "sarah", "another person", "someone else"]
            found_keywords = [kw for kw in redirect_keywords if kw.lower() in response_text.lower()]
            print(f"   🔍 REDIRECT CHECK: 🔧 DEBUG: Found redirect keywords: {found_keywords}")
        else:
            print(f"   ⚠️ REDIRECT CHECK: No response text found!")
            return "complete"  # No conversation data, complete normally

        # 🆕 ENHANCED: Apply AI analysis to response_text (same as vocal assistant)
        print(f"   🔍 REDIRECT CHECK: Applying AI analysis to response text...")
        
        # Get vocal assistant agent for AI analysis
        vocal_agent = None
        if hasattr(self, 'agents') and 'vocal_assistant' in self.agents:
            vocal_agent = self.agents['vocal_assistant']
            print(f"   🔍 REDIRECT CHECK: Found vocal assistant agent for AI analysis")
        
        if vocal_agent and hasattr(vocal_agent, 'gemini'):
            try:
                print(f"   🤖 REDIRECT CHECK: Generating AI-structured response from raw conversation...")
                
                analysis_prompt = f"""
Analyze this voice call conversation to detect if there was a redirect request.

CONVERSATION:
{response_text}

Look for patterns where:
1. Someone says they want to redirect, forward, transfer the call/ticket
2. Someone mentions another person's name to redirect to
3. Someone says another person would be better suited to handle this

If a redirect is requested, extract:
- The name/username of the person to redirect to
- Any role or department mentioned
- The reason for redirect

RESPOND IN THIS EXACT FORMAT:
REDIRECT_REQUESTED: [True/False]
USERNAME_TO_REDIRECT: [name or NONE]
ROLE_OF_THE_REDIRECT_TO: [role/department or NONE]
RESPONSIBILITIES: [reason for redirect or NONE]

EXAMPLES:
- "redirect the call to Sarah" → REDIRECT_REQUESTED: True, USERNAME_TO_REDIRECT: sarah
- "forward to DevOps team" → REDIRECT_REQUESTED: True, ROLE_OF_THE_REDIRECT_TO: DevOps
- "John would be better for this" → REDIRECT_REQUESTED: True, USERNAME_TO_REDIRECT: john

Be precise and only extract what is clearly mentioned.
Only return REDIRECT_REQUESTED: True if there is an explicit redirect request in the conversation.
"""
                
                # Use Gemini to analyze and generate structured response
                ai_structured_response = vocal_agent.gemini.chat(
                    analysis_prompt,
                    {},  # No ticket data needed for analysis
                    {},  # No employee data needed for analysis
                    is_employee=False
                )
                
                print(f"   🤖 REDIRECT CHECK: AI generated structured response ({len(ai_structured_response)} chars)")
                print(f"   🤖 REDIRECT CHECK: AI response preview: {ai_structured_response[:200]}...")
                
                # Now check if AI found redirect markers
                if "REDIRECT_REQUESTED: True" in ai_structured_response:
                    print(f"   ✅ REDIRECT CHECK: AI confirmed redirect request!")
                    
                    # Extract redirect info from AI-structured text
                    redirect_info = self._extract_structured_redirect_info(ai_structured_response)
                    print(f"   ✅ REDIRECT CHECK: Extracted redirect info: {redirect_info}")
                    
                    state["results"]["redirect_info"] = redirect_info
                    return "redirect"
                else:
                    print(f"   ❌ REDIRECT CHECK: AI analysis found no redirect")
                    return "complete"
                    
            except Exception as e:
                print(f"   ⚠️ REDIRECT CHECK: AI analysis failed: {e}")
                # Fall through to legacy methods
        else:
            print(f"   ⚠️ REDIRECT CHECK: Vocal assistant AI not available for analysis")
        
        # 🆕 FALLBACK: Check if redirect markers already exist (pre-processed)
        if "REDIRECT_REQUESTED:" in response_text:
            print(f"   🔍 REDIRECT CHECK: Structured redirect markers found!")
            print(f"   🔍 REDIRECT CHECK: Using pre-processed redirect data...")
            
            # Extract structured redirect information
            if "REDIRECT_REQUESTED: True" in response_text:
                print(f"   ✅ REDIRECT CHECK: Pre-processed redirect confirmed!")
                
                # Extract redirect info from structured text
                redirect_info = self._extract_structured_redirect_info(response_text)
                print(f"   ✅ REDIRECT CHECK: Extracted redirect info: {redirect_info}")
                
                state["results"]["redirect_info"] = redirect_info
                return "redirect"
            else:
                print(f"   ❌ REDIRECT CHECK: Pre-processed redirect declined")
                return "complete"

        # 🆕 ENHANCED: If no structured markers, analyze raw conversation with vocal assistant
        print(f"   🔍 REDIRECT CHECK: No structured markers - analyzing raw conversation...")
        print(f"   🔍 REDIRECT CHECK: 🔧 DEBUG: Available agents: {list(self.agents.keys()) if hasattr(self, 'agents') and self.agents else 'None'}")
        
        # Get vocal assistant agent for conversation analysis
        vocal_agent = None
        if hasattr(self, 'agents') and 'vocal_assistant' in self.agents:
            vocal_agent = self.agents['vocal_assistant']
            print(f"   🔍 REDIRECT CHECK: Found vocal assistant agent")
        else:
            print(f"   ⚠️ REDIRECT CHECK: No vocal assistant agent available")
            print(f"   🔍 REDIRECT CHECK: 🔧 DEBUG: Trying alternative agent access methods...")
            
            # Try alternative ways to get the vocal assistant
            if hasattr(self, 'agents'):
                for agent_name, agent in self.agents.items():
                    if 'vocal' in agent_name.lower() or hasattr(agent, '_analyze_conversation_for_redirect'):
                        vocal_agent = agent
                        print(f"   🔍 REDIRECT CHECK: Found alternative vocal agent: {agent_name}")
                        break
        
        if vocal_agent and hasattr(vocal_agent, '_analyze_conversation_for_redirect'):
            try:
                print(f"   🔍 REDIRECT CHECK: Calling enhanced AI analysis...")
                analyzed_result = vocal_agent._analyze_conversation_for_redirect(response_text)
                print(f"   🔍 REDIRECT CHECK: AI analysis result: {analyzed_result}")
                
                if analyzed_result and analyzed_result.get('redirect_requested'):
                    print(f"   ✅ REDIRECT CHECK: AI detected redirect!")
                    redirect_info = analyzed_result.get('redirect_employee_info', {})
                    state["results"]["redirect_info"] = redirect_info
                    print(f"   ✅ REDIRECT CHECK: Stored redirect info: {redirect_info}")
                    return "redirect"
                else:
                    print(f"   ❌ REDIRECT CHECK: AI analysis found no redirect")
                    return "complete"
                    
            except Exception as e:
                print(f"   ⚠️ REDIRECT CHECK: AI analysis error: {e}")
                import traceback
                print(f"   ⚠️ REDIRECT CHECK: Full traceback: {traceback.format_exc()}")
        else:
            print(f"   ⚠️ REDIRECT CHECK: Vocal agent method not available")

        # 🆕 ENHANCED: Fallback to old VocalResponse parsing (legacy compatibility)
        print(f"   🔍 REDIRECT CHECK: Trying legacy VocalResponse parsing...")
        try:
            conversation_data_for_analysis = {"response": response_text}
            vocal_response = VocalResponse(conversation_data_for_analysis)
            
            print(f"   🔍 REDIRECT CHECK: Legacy - Redirect requested: {vocal_response.redirect_requested}")
            print(f"   🔍 REDIRECT CHECK: Legacy - Redirect info: {vocal_response.redirect_employee_info}")
            
            if vocal_response.redirect_requested:
                state["results"]["redirect_info"] = vocal_response.redirect_employee_info
                print(f"   ✅ REDIRECT CHECK: Legacy method detected redirect!")
                return "redirect"
        except Exception as e:
            print(f"   ⚠️ REDIRECT CHECK: Legacy parsing error: {e}")
        
        print(f"   ❌ REDIRECT CHECK: All methods failed - no redirect detected")
        return "complete"

    def _extract_structured_redirect_info(self, response_text: str) -> Dict[str, Any]:
        """Extract redirect information from structured response text."""
        redirect_info = {}
        
        try:
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith("USERNAME_TO_REDIRECT:"):
                    username = line.split(":", 1)[1].strip()
                    if username != "NONE":
                        redirect_info["username"] = username
                elif line.startswith("ROLE_OF_THE_REDIRECT_TO:"):
                    role = line.split(":", 1)[1].strip()
                    if role != "NONE":
                        redirect_info["role"] = role
                elif line.startswith("RESPONSIBILITIES:"):
                    responsibilities = line.split(":", 1)[1].strip()
                    if responsibilities != "NONE":
                        redirect_info["responsibilities"] = responsibilities
                        
            print(f"   🔍 _extract_structured_redirect_info: Extracted: {redirect_info}")
            return redirect_info
            
        except Exception as e:
            print(f"   ⚠️ _extract_structured_redirect_info: Error: {e}")
            return {}
