"""
Ticket Manager class for handling ticket CRUD operations.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Ticket storage file
TICKETS_FILE = Path(__file__).parent.parent / "tickets.json"


class TicketManager:
    """Manages ticket operations."""
    
    def __init__(self):
        self.ensure_tickets_file()
    
    def ensure_tickets_file(self):
        """Ensure tickets file exists."""
        if not TICKETS_FILE.exists():
            with open(TICKETS_FILE, 'w') as f:
                json.dump([], f)
    
    def load_tickets(self) -> List[Dict]:
        """Load all tickets from storage."""
        try:
            with open(TICKETS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_tickets(self, tickets: List[Dict]):
        """Save tickets to storage."""
        with open(TICKETS_FILE, 'w') as f:
            json.dump(tickets, f, indent=2, default=str)
    
    def create_ticket(self, user: str, category: str, priority: str, subject: str, description: str) -> str:
        """Create a new ticket."""
        tickets = self.load_tickets()
        
        ticket_id = str(uuid.uuid4())[:8]
        ticket = {
            "id": ticket_id,
            "user": user,
            "category": category,
            "priority": priority,
            "subject": subject,
            "description": description,
            "status": "Open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "response": None,
            "response_at": None,
            "assigned_to": None,
            "assignment_status": None,
            "assignment_date": None,
            "employee_solution": None,
            "completion_date": None
        }
        
        tickets.append(ticket)
        self.save_tickets(tickets)
        return ticket_id
    
    def get_user_tickets(self, user: str) -> List[Dict]:
        """Get all tickets for a specific user."""
        tickets = self.load_tickets()
        return [t for t in tickets if t["user"] == user]
    
    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict]:
        """Get a specific ticket by ID."""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                return ticket
        return None
    
    def update_ticket_response(self, ticket_id: str, response: str):
        """Update ticket with AI response."""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                ticket["response"] = response
                ticket["response_at"] = datetime.now().isoformat()
                ticket["status"] = "Responded"
                ticket["updated_at"] = datetime.now().isoformat()
                break
        self.save_tickets(tickets)
    
    def assign_ticket(self, ticket_id: str, employee_username: str):
        """Assign ticket to an employee."""
        print(f"🎯 TICKET_MANAGER DEBUG: assign_ticket called with ticket_id='{ticket_id}', username='{employee_username}'")
        
        tickets = self.load_tickets()
        print(f"🎯 TICKET_MANAGER DEBUG: Loaded {len(tickets)} tickets from storage")
        
        ticket_found = False
        for i, ticket in enumerate(tickets):
            print(f"🎯 TICKET_MANAGER DEBUG: Checking ticket {i}: ID='{ticket.get('id', 'NO_ID')}' vs target='{ticket_id}'")
            if ticket["id"] == ticket_id:
                print(f"🎯 TICKET_MANAGER DEBUG: Found matching ticket at index {i}")
                print(f"🎯 TICKET_MANAGER DEBUG: Current ticket data: {ticket}")
                print(f"🎯 TICKET_MANAGER DEBUG: Current assigned_to: '{ticket.get('assigned_to', 'None')}'")
                
                ticket["assigned_to"] = employee_username
                ticket["assignment_status"] = "assigned"
                ticket["assignment_date"] = datetime.now().isoformat()
                ticket["status"] = "Assigned"
                ticket["updated_at"] = datetime.now().isoformat()
                
                print(f"🎯 TICKET_MANAGER DEBUG: Updated ticket data: {ticket}")
                ticket_found = True
                break
                
        if not ticket_found:
            print(f"❌ TICKET_MANAGER DEBUG: Ticket with ID '{ticket_id}' not found!")
            print(f"❌ TICKET_MANAGER DEBUG: Available ticket IDs: {[t.get('id', 'NO_ID') for t in tickets]}")
            return False
            
        print(f"🎯 TICKET_MANAGER DEBUG: Saving {len(tickets)} tickets back to storage")
        self.save_tickets(tickets)
        print(f"✅ TICKET_MANAGER DEBUG: Successfully assigned ticket {ticket_id} to {employee_username}")
        return True
    
    def update_employee_solution(self, ticket_id: str, solution: str):
        """Update ticket with employee solution."""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                ticket["employee_solution"] = solution
                ticket["assignment_status"] = "completed"
                ticket["completion_date"] = datetime.now().isoformat()
                ticket["status"] = "Solved"
                ticket["updated_at"] = datetime.now().isoformat()
                break
        self.save_tickets(tickets)
    
    def get_assigned_tickets(self, employee_username: str) -> List[Dict]:
        """Get tickets assigned to an employee."""
        tickets = self.load_tickets()
        return [t for t in tickets if t.get("assigned_to") == employee_username]
