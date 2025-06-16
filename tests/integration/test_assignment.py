#!/usr/bin/env python3
"""
Simple test to verify ticket assignment functionality.
"""

import sys
import json
from pathlib import Path

sys.path.append('front')
from tickets import TicketManager

def test_assignment_functionality():
    """Test the assignment functionality without AI workflow."""
    print("🧪 Testing Ticket Assignment Functionality")
    print("=" * 50)
    
    # Initialize ticket manager
    ticket_manager = TicketManager()
    
    # Create a test ticket
    print("1. Creating test ticket...")
    ticket_id = ticket_manager.create_ticket(
        user="test_user",
        category="Technical Issue", 
        priority="Medium",
        subject="ML Model Deployment Help",
        description="I need help deploying my machine learning model to production"
    )
    print(f"✅ Created ticket: {ticket_id}")
    
    # Test assignment
    print("\n2. Assigning ticket to Alex Johnson...")
    ticket_manager.assign_ticket(ticket_id, "alex01")
    print("✅ Ticket assigned")
    
    # Verify assignment
    print("\n3. Verifying assignment...")
    ticket = ticket_manager.get_ticket_by_id(ticket_id)
    if ticket:
        print(f"Assigned to: {ticket.get('assigned_to')}")
        print(f"Assignment status: {ticket.get('assignment_status')}")
        print(f"Ticket status: {ticket.get('status')}")
    
    # Test employee solution
    print("\n4. Adding employee solution...")
    solution = "To deploy your ML model, you can use Docker containers with Flask API. Here's a step-by-step guide..."
    ticket_manager.update_employee_solution(ticket_id, solution)
    print("✅ Solution added")
    
    # Verify solution
    print("\n5. Verifying solution...")
    ticket = ticket_manager.get_ticket_by_id(ticket_id)
    if ticket:
        print(f"Employee solution: {ticket.get('employee_solution')[:50]}...")
        print(f"Assignment status: {ticket.get('assignment_status')}")
        print(f"Ticket status: {ticket.get('status')}")
    
    # Test getting assigned tickets
    print("\n6. Getting assigned tickets for alex01...")
    assigned_tickets = ticket_manager.get_assigned_tickets("alex01")
    print(f"Number of assigned tickets: {len(assigned_tickets)}")
    
    for ticket in assigned_tickets:
        print(f"  - [{ticket['id']}] {ticket['subject']} - {ticket.get('assignment_status', 'unknown')}")
    
    print("\n✅ Assignment functionality test completed!")

if __name__ == "__main__":
    test_assignment_functionality()
