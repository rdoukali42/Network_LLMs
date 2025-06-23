#!/usr/bin/env python3
"""
Test specific to Patrick to see why he's not receiving assignments/notifications.
"""

import sys
import json
from pathlib import Path

sys.path.append('front')
from tickets import TicketManager
from database import DatabaseManager

def test_patrick_assignment():
    """Test Patrick assignment and notifications specifically."""
    print("🧪 Testing Patrick Assignment and Notifications")
    print("=" * 60)
    
    # Initialize managers
    ticket_manager = TicketManager()
    db_manager = DatabaseManager()
    
    # 1. Check if Patrick exists in the system
    print("1. Checking Patrick in employee database...")
    patrick = db_manager.get_employee_by_username("patrick")
    if patrick:
        print(f"   ✅ Found Patrick: {patrick['full_name']} ({patrick['role_in_company']})")
        print(f"   📧 Username: {patrick['username']}")
    else:
        print("   ❌ Patrick not found in database!")
        return
    
    # 2. Create a test ticket
    print("\n2. Creating test ticket...")
    ticket_id = ticket_manager.create_ticket(
        user="test_user",
        category="Technical Issue",
        priority="Medium",
        subject="Test Patrick Assignment",
        description="Testing Patrick assignment in redirect flow"
    )
    print(f"   ✅ Created ticket: {ticket_id}")
    
    # 3. Test direct assignment (same as original flow)
    print("\n3. Testing direct assignment to Patrick...")
    try:
        ticket_manager.assign_ticket(ticket_id, "patrick")
        print("   ✅ Assignment function called successfully")
        
        # Verify assignment
        ticket = ticket_manager.get_ticket_by_id(ticket_id)
        if ticket:
            print(f"   📋 Assigned to: {ticket.get('assigned_to')}")
            print(f"   📋 Assignment status: {ticket.get('assignment_status')}")
            print(f"   📋 Assignment date: {ticket.get('assignment_date')}")
        else:
            print("   ❌ Could not retrieve ticket after assignment")
            
    except Exception as e:
        print(f"   ❌ Assignment failed: {e}")
        return
    
    # 4. Test call notification creation
    print("\n4. Testing call notification creation...")
    try:
        call_info = {
            "ticket_id": ticket_id,
            "employee_name": patrick['full_name'],
            "employee_username": "patrick",
            "ticket_subject": "Test Patrick Assignment",
            "call_status": "redirected_incoming"
        }
        
        success = db_manager.create_call_notification(
            target_employee="patrick",
            ticket_id=ticket_id,
            ticket_subject="Test Patrick Assignment",
            caller_name="System Redirect",
            call_info=call_info
        )
        
        if success:
            print("   ✅ Call notification created successfully")
        else:
            print("   ❌ Call notification creation failed")
            
    except Exception as e:
        print(f"   ❌ Notification creation failed: {e}")
        return
    
    # 5. Check pending calls for Patrick
    print("\n5. Checking pending calls for Patrick...")
    try:
        pending_calls = db_manager.get_pending_calls("patrick")
        print(f"   📞 Patrick has {len(pending_calls)} pending calls")
        
        for call in pending_calls:
            print(f"   📞 Call: {call['ticket_subject']} (ID: {call['id']})")
            print(f"       Status: {call['status']}")
            print(f"       Created: {call['created_at']}")
            
    except Exception as e:
        print(f"   ❌ Error checking pending calls: {e}")
    
    # 6. Check assigned tickets for Patrick
    print("\n6. Checking assigned tickets for Patrick...")
    try:
        assigned_tickets = ticket_manager.get_assigned_tickets("patrick")
        print(f"   📋 Patrick has {len(assigned_tickets)} assigned tickets")
        
        for ticket in assigned_tickets:
            print(f"   📋 Ticket: {ticket['subject']} (ID: {ticket['id']})")
            print(f"       Status: {ticket['status']}")
            print(f"       Assignment Status: {ticket.get('assignment_status')}")
            
    except Exception as e:
        print(f"   ❌ Error checking assigned tickets: {e}")
    
    print("\n✅ Patrick assignment test completed!")

if __name__ == "__main__":
    test_patrick_assignment()
