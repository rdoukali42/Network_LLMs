"""
Workflow utility functions and validation helpers.
"""
from typing import Dict, Any
from datetime import datetime
from langfuse import observe


class WorkflowUtils:
    """Utility functions for workflow operations."""
    
    @staticmethod
    def validate_redirect_limits(ticket_data: Dict) -> bool:
        """Check if ticket has exceeded redirect limits."""
        redirect_count = ticket_data.get("redirect_count", 0)
        max_redirects = ticket_data.get("max_redirects", 3)
        
        print(f"   🚨 REDIRECT LIMIT CHECK: Count {redirect_count}/{max_redirects}")
        
        if redirect_count >= max_redirects:
            print(f"   🚨 REDIRECT LIMIT EXCEEDED: Ticket has reached maximum redirects")
            return False
        
        print(f"   ✅ REDIRECT LIMIT OK: {max_redirects - redirect_count} redirects remaining")
        return True
    
    @staticmethod
    def reset_ticket_assignment(ticket_data: Dict, redirect_info: Dict) -> Dict:
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
