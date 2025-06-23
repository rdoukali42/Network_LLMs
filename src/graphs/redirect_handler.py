"""
Redirect detection, employee search, and routing handlers.
"""
from typing import Dict, Any
from langfuse import observe
from .workflow_state import WorkflowState
from .workflow_utils import WorkflowUtils


class RedirectHandler:
    """Handles redirect detection, employee search, and routing operations."""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
    
    @observe()
    def redirect_detector_step(self, state: WorkflowState) -> WorkflowState:
        """Analyze conversation for redirect request details."""
        state = state.copy()
        state["current_step"] = "redirect_detector"
        
        print(f"\n     🔄 REDIRECT DETECTOR: Analyzing redirect request...")
        
        # Get redirect info and ticket data
        redirect_info = state["results"].get("redirect_info", {})
        ticket_data = state["results"].get("ticket_data", {})
        
        print(f"     🔄 REDIRECT DETECTOR: Received redirect info: {redirect_info}")
        print(f"     🔄 REDIRECT DETECTOR: Ticket ID: {ticket_data.get('id', 'unknown')}")
        
        # Redirect loop prevention: Check redirect limits
        if not WorkflowUtils.validate_redirect_limits(ticket_data):
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
            print(f"     🔄 REDIRECT DETECTOR: Ping-pong redirect detected!")
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
    def employee_searcher_step(self, state: WorkflowState) -> WorkflowState:
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
    def maestro_redirect_selector_step(self, state: WorkflowState) -> WorkflowState:
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
            
            # Format data for vocal_assistant (same as HR assignment)
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
