#!/usr/bin/env python3
"""
Test redirect with a REAL ticket ID to verify assignment works.
"""

import sys
sys.path.append('front')
from tickets import TicketManager
from database import DatabaseManager

def test_real_ticket_assignment():
    """Test assignment with a real ticket that exists in the system."""
    print("🧪 TESTING REAL TICKET ASSIGNMENT")
    print("=" * 60)
    
    tm = TicketManager()
    db = DatabaseManager()
    
    # Get a real ticket that exists
    all_tickets = tm.load_tickets()
    test_ticket = None
    for ticket in all_tickets:
        if ticket['status'] in ['Open', 'Responded'] and ticket.get('assigned_to') != 'patrick':
            test_ticket = ticket
            break
    
    if not test_ticket:
        print("❌ No suitable test ticket found!")
        return
        
    real_ticket_id = test_ticket['id']
    print(f"📋 Using real ticket: {real_ticket_id}")
    print(f"   Subject: {test_ticket['subject']}")
    print(f"   Current assigned_to: {test_ticket.get('assigned_to', 'None')}")
    print(f"   Status: {test_ticket['status']}")
    
    # Check Patrick's current state
    patrick_tickets_before = len(tm.get_assigned_tickets('patrick'))
    patrick_calls_before = len(db.get_pending_calls('patrick'))
    print(f"\n📊 PATRICK BEFORE:")
    print(f"   Assigned tickets: {patrick_tickets_before}")
    print(f"   Pending calls: {patrick_calls_before}")
    
    # Test 1: Assign the real ticket to Patrick
    print(f"\n🔧 TEST 1: Assigning real ticket {real_ticket_id} to Patrick...")
    try:
        result = tm.assign_ticket(real_ticket_id, 'patrick')
        print(f"   Assignment result: {result}")
        
        # Verify assignment
        updated_ticket = tm.get_ticket_by_id(real_ticket_id)
        if updated_ticket:
            print(f"   ✅ Ticket now assigned to: {updated_ticket.get('assigned_to')}")
            print(f"   ✅ Assignment status: {updated_ticket.get('assignment_status')}")
        else:
            print(f"   ❌ Could not retrieve updated ticket")
            
    except Exception as e:
        print(f"   ❌ Assignment failed: {e}")
        return
    
    # Test 2: Create notification for Patrick
    print(f"\n🔧 TEST 2: Creating notification for Patrick...")
    try:
        call_info = {
            "ticket_id": real_ticket_id,
            "employee_name": "Patrick Neumann",
            "employee_username": "patrick", 
            "ticket_subject": test_ticket['subject'],
            "call_status": "redirected_incoming"
        }
        
        notification_result = db.create_call_notification(
            target_employee='patrick',
            ticket_id=real_ticket_id,
            ticket_subject=test_ticket['subject'],
            caller_name='System Redirect Test',
            call_info=call_info
        )
        
        print(f"   Notification result: {notification_result}")
        
    except Exception as e:
        print(f"   ❌ Notification failed: {e}")
    
    # Check Patrick's state after
    patrick_tickets_after = len(tm.get_assigned_tickets('patrick'))
    patrick_calls_after = len(db.get_pending_calls('patrick'))
    print(f"\n📊 PATRICK AFTER:")
    print(f"   Assigned tickets: {patrick_tickets_after} (was {patrick_tickets_before})")
    print(f"   Pending calls: {patrick_calls_after} (was {patrick_calls_before})")
    
    # Show Patrick's current assignments
    print(f"\n📋 PATRICK'S CURRENT ASSIGNMENTS:")
    patrick_tickets = tm.get_assigned_tickets('patrick')
    for ticket in patrick_tickets[-3:]:
        print(f"   - {ticket['id']}: {ticket['subject']} (Status: {ticket.get('assignment_status')})")
        
    # Show Patrick's current calls
    print(f"\n📞 PATRICK'S CURRENT CALLS:")
    patrick_calls = db.get_pending_calls('patrick')
    for call in patrick_calls[-3:]:
        print(f"   - {call['ticket_subject']} (Created: {call['created_at']})")
    
    print(f"\n🎉 TEST SUMMARY:")
    if patrick_tickets_after > patrick_tickets_before:
        print("✅ Patrick received real ticket assignment!")
    else:
        print("❌ Patrick did not receive ticket assignment")
        
    if patrick_calls_after > patrick_calls_before:
        print("✅ Patrick received call notification!")
    else:
        print("❌ Patrick did not receive call notification")

if __name__ == "__main__":
    test_real_ticket_assignment()
