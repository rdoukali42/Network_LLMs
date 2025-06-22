"""
TicketManager class for handling ticket CRUD operations using a JSON file.
This version is refactored for the optimized_project.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class TicketManager:
    """Manages ticket operations using a JSON file."""

    def __init__(self, project_root_path: Path, tickets_file_name: str = "tickets.json"):
        """
        Initializes the TicketManager.
        Args:
            project_root_path: The absolute path to the 'optimized_project' root.
            tickets_file_name: The name of the JSON file to store tickets.
                               This file will be located in `project_root_path / "data_management" / tickets_file_name`.
        """
        self.project_root = project_root_path
        # Store tickets.json within the data_management directory for clarity, or a dedicated data dir
        self.tickets_file_path = self.project_root / "data_management" / tickets_file_name
        self._ensure_tickets_file()

    def _ensure_tickets_file(self):
        """Ensure tickets file exists."""
        if not self.tickets_file_path.exists():
            self.tickets_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tickets_file_path, 'w') as f:
                json.dump([], f)

    def load_tickets(self) -> List[Dict[str, Any]]:
        """Load all tickets from storage."""
        if not self.tickets_file_path.exists():
            return []
        try:
            with open(self.tickets_file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is empty or corrupted, return empty list
            return []

    def save_tickets(self, tickets: List[Dict[str, Any]]):
        """Save tickets to storage."""
        with open(self.tickets_file_path, 'w') as f:
            json.dump(tickets, f, indent=2, default=str) # Use default=str for datetime objects

    def create_ticket(self, user: str, category: str, priority: str, subject: str, description: str) -> str:
        """Create a new ticket."""
        tickets = self.load_tickets()

        ticket_id = str(uuid.uuid4())[:8] # Short UUID for readability
        new_ticket = {
            "id": ticket_id,
            "user": user, # Username of the ticket creator
            "category": category,
            "priority": priority,
            "subject": subject,
            "description": description,
            "status": "Open", # Initial status
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "response": None, # AI or initial response
            "response_at": None,
            "assigned_to": None, # Username of assigned employee
            "assignment_status": None, # e.g., "assigned", "in_progress", "completed"
            "assignment_date": None,
            "employee_solution": None, # Solution provided by employee
            "completion_date": None
        }

        tickets.append(new_ticket)
        self.save_tickets(tickets)
        return ticket_id

    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific ticket by ID."""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                return ticket
        return None

    def get_user_tickets(self, username: str) -> List[Dict[str, Any]]:
        """Get all tickets for a specific user."""
        tickets = self.load_tickets()
        return [t for t in tickets if t["user"] == username]

    def get_assigned_tickets(self, employee_username: str) -> List[Dict[str, Any]]:
        """Get tickets assigned to an employee."""
        tickets = self.load_tickets()
        return [t for t in tickets if t.get("assigned_to") == employee_username]

    def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields of a ticket.
        Ensures 'updated_at' is always modified.
        """
        tickets = self.load_tickets()
        ticket_found = False
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                for key, value in updates.items():
                    ticket[key] = value
                ticket["updated_at"] = datetime.now().isoformat()
                ticket_found = True
                break

        if ticket_found:
            self.save_tickets(tickets)
        return ticket_found

    def update_ticket_response(self, ticket_id: str, response_text: str):
        """Update ticket with AI response."""
        updates = {
            "response": response_text,
            "response_at": datetime.now().isoformat(),
            "status": "Responded"
        }
        return self.update_ticket(ticket_id, updates)

    def assign_ticket(self, ticket_id: str, employee_username: str):
        """Assign ticket to an employee."""
        updates = {
            "assigned_to": employee_username,
            "assignment_status": "assigned",
            "assignment_date": datetime.now().isoformat(),
            "status": "Assigned"
        }
        return self.update_ticket(ticket_id, updates)

    def update_employee_solution(self, ticket_id: str, solution: str):
        """Update ticket with employee solution."""
        updates = {
            "employee_solution": solution,
            "assignment_status": "completed", # Or "solved_by_employee"
            "completion_date": datetime.now().isoformat(),
            "status": "Solved"
        }
        return self.update_ticket(ticket_id, updates)

    def update_assignment_status(self, ticket_id: str, assignment_status: str) -> bool:
        """Update the assignment status of a ticket (e.g., 'in_progress')."""
        # Ensure this status is valid if you have a predefined list
        return self.update_ticket(ticket_id, {"assignment_status": assignment_status})

# Example Usage (for testing or if this module is run directly):
if __name__ == '__main__':
    # This assumes the script is run from within optimized_project/data_management
    project_root = Path(__file__).resolve().parent.parent
    tm = TicketManager(project_root_path=project_root)

    # Test creating a ticket
    # new_id = tm.create_ticket("test_user", "General", "Medium", "Test Subject", "This is a test ticket.")
    # print(f"Created ticket with ID: {new_id}")

    # Test loading tickets
    all_tickets = tm.load_tickets()
    print(f"\nLoaded {len(all_tickets)} tickets:")
    # for t in all_tickets:
    #     print(f"  ID: {t['id']}, Subject: {t['subject']}, Status: {t['status']}")

    # Example: get a specific ticket
    # if all_tickets:
    #     some_ticket_id = all_tickets[0]['id']
    #     ticket = tm.get_ticket_by_id(some_ticket_id)
    #     print(f"\nDetails for ticket {some_ticket_id}: {ticket}")

    # print(f"\nTickets file is at: {tm.tickets_file_path}")
