#!/usr/bin/env python3
"""
Test the AI response integration in the ticket system.
"""

import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent
front_dir = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(front_dir))

from workflow_client import WorkflowClient
from tickets import TicketManager

def test_ai_response():
    """Test AI response for a sample ticket."""
    print("🧪 Testing AI response integration...")
    
    # Initialize workflow client
    client = WorkflowClient()
    
    if not client.is_ready():
        print("❌ Workflow client not ready")
        return
    
    # Test query
    query = "Support Ticket: Math Help\n\nDetails: What is 25 + 37?"
    
    print(f"📝 Testing query: {query}")
    
    # Get AI response
    result = client.process_message(query)
    
    print(f"🤖 AI result: {result}")
    
    # Extract response like the ticket system does
    response = None
    if result:
        if isinstance(result, dict):
            response = (result.get("result") or 
                      result.get("synthesis") or 
                      result.get("response") or 
                      result.get("answer") or
                      result.get("output"))
        elif isinstance(result, str):
            response = result
    
    if response:
        print(f"✅ Extracted response: {response}")
    else:
        print(f"❌ No response extracted from: {result}")
    
    # Test ticket manager
    print("\n📋 Testing ticket manager...")
    tm = TicketManager()
    
    # Create test ticket
    ticket_id = tm.create_ticket(
        user="test_user",
        category="Technical Issue", 
        priority="Medium",
        subject="Math Help",
        description="What is 25 + 37?"
    )
    
    print(f"🎫 Created ticket: {ticket_id}")
    
    # Update with AI response
    if response:
        tm.update_ticket_response(ticket_id, response)
        print(f"✅ Updated ticket with AI response")
        
        # Check ticket
        tickets = tm.get_user_tickets("test_user")
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                print(f"📄 Final ticket response: {ticket['response']}")
                break
    else:
        print("❌ No AI response to add to ticket")

if __name__ == "__main__":
    test_ai_response()
