#!/usr/bin/env python3
"""
Final verification by simulating a real ticket submission.
"""

import sys
import os
sys.path.append('src')
sys.path.append('front')

# Mock streamlit session state for ticket submission
class MockSessionState:
    def __init__(self):
        self.username = "mounir"
        self.ticket_manager = None
        self.workflow_client = None

class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState()

# Mock streamlit
sys.modules['streamlit'] = MockStreamlit()

from front.database import db_manager
from front.tickets.ticket_manager import TicketManager
from front.workflow_client import WorkflowClient

def test_ticket_submission():
    """Test the complete ticket submission workflow."""
    print("🎫 TESTING COMPLETE TICKET WORKFLOW")
    print("=" * 45)
    
    # Initialize components
    ticket_manager = TicketManager()
    workflow_client = WorkflowClient()
    
    # Test ticket
    test_subject = "ML Model Selection"
    test_description = "which model should I use for a classification problem with imbalanced data?"
    test_user = "mounir"
    
    print(f"👤 User: {test_user}")
    print(f"📝 Subject: {test_subject}")  
    print(f"📄 Description: {test_description}")
    print(f"🎯 Expected: Should assign to Alex Johnson (ML Engineer), NOT to mounir")
    
    # Create ticket
    ticket_id = ticket_manager.create_ticket(
        user=test_user,
        subject=test_subject,
        description=test_description,
        category="Technical Issue",
        priority="Medium"
    )
    
    print(f"\n🆔 Created ticket: {ticket_id}")
    
    # Process with AI workflow
    query = f"Support Ticket: {test_subject}\n\nDetails: {test_description}"
    
    try:
        print(f"\n🤖 Processing with AI workflow...")
        result = workflow_client.process_message(query)
        
        print(f"📊 Workflow Result:")
        print(f"   Status: {result.get('status')}")
        
        response = result.get('result', '')
        print(f"   Response: {response[:200]}...")
        
        # Check if it's an assignment response
        if "👤" in response and "(@" in response:
            # Parse assignment 
            if "(@alex01)" in response:
                print(f"\n✅ SUCCESS: Correctly assigned to Alex Johnson (ML Engineer)")
                print(f"✅ No self-assignment - mounir not assigned to himself")
            elif "(@mounir)" in response:
                print(f"\n❌ FAILURE: Self-assignment detected - mounir assigned to himself")
            else:
                print(f"\n⚠️  Assigned to someone else (not ideal but acceptable)")
        else:
            print(f"\n📝 Got regular AI response (no assignment needed)")
            
    except Exception as e:
        print(f"\n❌ Error during workflow: {e}")
    
    # Clean up - delete test ticket
    try:
        tickets = ticket_manager.load_tickets()
        tickets = [t for t in tickets if t['id'] != ticket_id]
        ticket_manager.save_tickets(tickets)
        print(f"\n🗑️  Cleaned up test ticket {ticket_id}")
    except:
        pass


if __name__ == "__main__":
    test_ticket_submission()
    print("\n🎉 WORKFLOW TEST COMPLETE!")
