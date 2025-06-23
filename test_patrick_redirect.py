#!/usr/bin/env python3
"""
Test redirect workflow specifically to Patrick to ensure he receives assignment and notification.
"""

import sys
sys.path.append('src')
sys.path.append('front')

from tickets import TicketManager
from database import DatabaseManager

def test_redirect_to_patrick():
    """Test redirect workflow with Patrick as the target employee by simulating the result."""
    print("🧪 TESTING REDIRECT TO PATRICK")
    print("=" * 60)
    
    # Managers for checking results
    ticket_manager = TicketManager()
    db_manager = DatabaseManager()
    
    print("✅ Managers initialized")
    
    # Check Patrick's status before redirect
    tickets_before = len(ticket_manager.get_assigned_tickets("patrick"))
    calls_before = len(db_manager.get_pending_calls("patrick"))
    print(f"📊 BEFORE TEST:")
    print(f"   Patrick's assigned tickets: {tickets_before}")
    print(f"   Patrick's pending calls: {calls_before}")
    
    # Test 1: Create a ticket assignment to Patrick (simulating redirect assignment)
    print("\n🔄 TEST 1: Creating ticket assignment for Patrick...")
    try:
        # Create a test ticket
        ticket_id = ticket_manager.create_ticket(
            user="test_user_redirect",
            category="Product Strategy",
            priority="High",
            subject="Mobile App Roadmap Planning",
            description="Need help with product roadmap planning and feature prioritization for mobile app"
        )
        print(f"   ✅ Created test ticket: {ticket_id}")
        
        # Assign it to Patrick (this is what happens in the redirect flow)
        ticket_manager.assign_ticket(ticket_id, "patrick")
        print(f"   ✅ Assigned ticket to Patrick")
        
        # Verify assignment
        ticket = ticket_manager.get_ticket_by_id(ticket_id)
        if ticket and ticket.get('assigned_to') == 'patrick':
            print(f"   ✅ Ticket assignment verified: {ticket['assigned_to']}")
        else:
            print(f"   ❌ Ticket assignment failed")
            
    except Exception as e:
        print(f"   ❌ Ticket assignment error: {e}")
    
    # Test 2: Create a call notification for Patrick (simulating redirect notification)
    print("\n🔄 TEST 2: Creating call notification for Patrick...")
    try:
        call_info = {
            "ticket_id": ticket_id,
            "employee_name": "Patrick Neumann", 
            "employee_username": "patrick",
            "ticket_subject": "Mobile App Roadmap Planning",
            "call_status": "redirected_incoming",
            "redirect_reason": "Product strategy expertise needed"
        }
        
        success = db_manager.create_call_notification(
            target_employee="patrick",
            ticket_id=ticket_id,
            ticket_subject="Mobile App Roadmap Planning",
            caller_name="System Redirect",
            call_info=call_info
        )
        
        if success:
            print(f"   ✅ Call notification created for Patrick")
        else:
            print(f"   ❌ Call notification creation failed")
            
    except Exception as e:
        print(f"   ❌ Call notification error: {e}")
    
    # Check Patrick's status after our tests
    tickets_after = len(ticket_manager.get_assigned_tickets("patrick"))
    calls_after = len(db_manager.get_pending_calls("patrick"))
    print(f"\n📊 AFTER TESTS:")
    print(f"   Patrick's assigned tickets: {tickets_after} (was {tickets_before})")
    print(f"   Patrick's pending calls: {calls_after} (was {calls_before})")
    
    # Verify Patrick received both
    if tickets_after > tickets_before:
        print("✅ PATRICK RECEIVED NEW TICKET ASSIGNMENT!")
    else:
        print("❌ Patrick did not receive new ticket assignment")
        
    if calls_after > calls_before:
        print("✅ PATRICK RECEIVED NEW CALL NOTIFICATION!")
    else:
        print("❌ Patrick did not receive new call notification")
    
    # Show Patrick's latest assignments and notifications
    print(f"\n📋 PATRICK'S LATEST ASSIGNMENTS:")
    assigned_tickets = ticket_manager.get_assigned_tickets("patrick")
    for ticket in assigned_tickets[-3:]:  # Show last 3 tickets
        print(f"   - {ticket['subject']} (ID: {ticket['id']}, Status: {ticket.get('assignment_status', 'unknown')})")
    
    print(f"\n📞 PATRICK'S PENDING CALLS:")
    pending_calls = db_manager.get_pending_calls("patrick")
    for call in pending_calls[-3:]:  # Show last 3 calls
        print(f"   - {call['ticket_subject']} (Created: {call['created_at']}, Status: {call['status']})")
    
    # Test summary
    print(f"\n🎉 TEST SUMMARY:")
    if tickets_after > tickets_before and calls_after > calls_before:
        print("✅ TEST PASSED: Patrick can receive both assignments and notifications!")
        print("✅ The redirect workflow should work correctly for Patrick")
    else:
        print("❌ TEST FAILED: Patrick is not receiving assignments or notifications properly")
        print("❌ There may be an issue with the redirect workflow for Patrick")

if __name__ == "__main__":
    test_redirect_to_patrick()
