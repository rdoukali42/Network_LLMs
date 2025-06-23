#!/usr/bin/env python3
"""
Real end-to-end redirect test with actual ticket assignment and notification.
This uses a real ticket ID and verifies the complete flow works.
"""

import sys
import os
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.append('front')

from tickets import TicketManager
from database import DatabaseManager

def test_real_end_to_end_redirect():
    """Test complete redirect flow with real ticket assignment and notification."""
    
    print("🚀 REAL END-TO-END REDIRECT TEST")
    print("=" * 50)
    
    # Initialize managers
    ticket_manager = TicketManager()
    db_manager = DatabaseManager()
    
    # Create a real test ticket
    print("1. 📋 Creating real test ticket...")
    ticket_id = ticket_manager.create_ticket(
        user="test_user",
        category="Technical Issue",
        priority="Medium", 
        subject="End-to-End Redirect Test",
        description="Testing complete redirect workflow with real assignment"
    )
    print(f"   ✅ Created ticket: {ticket_id}")
    
    try:
        from main import AISystem
        ai_system = AISystem()
        
        # Check Yacoub's status before
        yacoub_before = {
            "assigned": len(ticket_manager.get_assigned_tickets("yacoub")),
            "calls": len(db_manager.get_pending_calls("yacoub"))
        }
        print(f"📊 YACOUB BEFORE: {yacoub_before['assigned']} tickets, {yacoub_before['calls']} calls")
        
        # Realistic conversation redirecting to Yacoub
        redirect_conversation = """Employee: Hi! I'm working on your database connection issue.
You: I'm having trouble with PostgreSQL query optimization and connection pooling.
Employee: This looks like it needs deep database expertise. Yacoub would be perfect for this - he's our full-stack developer with extensive SQL and database optimization experience.
You: Can you redirect this to Yacoub?
Employee: Absolutely! I'll redirect this to Yacoub right away. He has the database knowledge you need."""
        
        print(f"📝 Test Conversation (redirecting to Yacoub):")
        print(f"   Target: Yacoub (database expertise)")
        print(f"   Length: {len(redirect_conversation)} characters")
        
        # END_CALL input with real ticket ID
        end_call_input = {
            "messages": [],
            "current_step": "call_completion_handler",
            "results": {
                "hr_agent": {
                    "action": "assign",
                    "employee": "sarah",
                    "employee_data": {
                        'username': 'sarah',
                        'full_name': 'Sarah Becker',
                        'role_in_company': 'QA Engineer'
                    }
                },
                "vocal_assistant": {
                    "action": "end_call",
                    "status": "call_completed",
                    "conversation_summary": redirect_conversation,
                    "conversation_data": {
                        "conversation_summary": redirect_conversation,
                        "call_duration": "completed"
                    },
                    "result": "Voice call completed",
                    "end_call_triggered": True
                }
            },
            "metadata": {
                "request_type": "voice",
                "event_type": "end_call",
                "ticket_id": ticket_id,  # REAL TICKET ID
                "employee_id": "sarah"
            }
        }
        
        print(f"\n2. 🔄 Processing redirect with real ticket {ticket_id}...")
        result = ai_system.workflow.process_end_call(end_call_input)
        
        print(f"\n3. 📊 Analyzing results...")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not dict'}")
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return False
        
        # Check redirect detection
        call_active = result.get("call_active", False)
        redirect_call_initiated = result.get("redirect_call_initiated", False)
        call_info = result.get("results", {}).get("call_info") if "results" in result else None
        
        print(f"   Call active: {call_active}")
        print(f"   Redirect initiated: {redirect_call_initiated}")
        print(f"   Call info: {call_info}")
        
        success = False
        
        if call_active and redirect_call_initiated and call_info:
            target_employee = call_info.get("employee_username", "")
            target_ticket = call_info.get("ticket_id", "")
            
            print(f"✅ REDIRECT DETECTED!")
            print(f"   Target employee: {call_info.get('employee_name')} ({target_employee})")
            print(f"   Target ticket: {target_ticket}")
            
            if target_employee.lower() == "yacoub" and target_ticket == ticket_id:
                print(f"✅ CORRECT TARGET AND TICKET!")
                success = True
            else:
                print(f"❌ Wrong target or ticket")
                
        # Check actual assignment and notification
        print(f"\n4. 🔍 Verifying assignment and notification...")
        
        # Check ticket assignment
        updated_ticket = ticket_manager.get_ticket_by_id(ticket_id)
        if updated_ticket and updated_ticket.get("assigned_to") == "yacoub":
            print(f"✅ TICKET ASSIGNED TO YACOUB!")
            print(f"   Assignment status: {updated_ticket.get('assignment_status')}")
            print(f"   Assignment date: {updated_ticket.get('assignment_date')}")
        else:
            print(f"❌ TICKET NOT ASSIGNED TO YACOUB!")
            if updated_ticket:
                print(f"   Current assignee: {updated_ticket.get('assigned_to', 'None')}")
            success = False
            
        # Check Yacoub's status after
        yacoub_after = {
            "assigned": len(ticket_manager.get_assigned_tickets("yacoub")),
            "calls": len(db_manager.get_pending_calls("yacoub"))
        }
        print(f"📊 YACOUB AFTER: {yacoub_after['assigned']} tickets, {yacoub_after['calls']} calls")
        
        # Verify notification
        if yacoub_after["calls"] > yacoub_before["calls"]:
            print(f"✅ NOTIFICATION SENT TO YACOUB!")
            print(f"   Gained {yacoub_after['calls'] - yacoub_before['calls']} new call(s)")
        else:
            print(f"❌ NO NOTIFICATION SENT TO YACOUB!")
            success = False
            
        # Show recent calls for verification
        recent_calls = db_manager.get_pending_calls("yacoub")
        if recent_calls:
            print(f"📞 Yacoub's recent calls:")
            for call in recent_calls[-2:]:  # Show last 2
                print(f"   - {call.get('ticket_subject', 'Unknown')} (Created: {call.get('created_at', 'Unknown')})")
        
        if success:
            print(f"\n🎉 REAL END-TO-END TEST PASSED!")
            print(f"   ✅ Redirect conversation analyzed correctly")
            print(f"   ✅ Yacoub identified as target employee")
            print(f"   ✅ Real ticket {ticket_id} assigned to Yacoub")
            print(f"   ✅ Call notification sent to Yacoub")
            print(f"   ✅ Complete workflow successful!")
        else:
            print(f"\n❌ END-TO-END TEST FAILED!")
            
        return success
        
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_real_end_to_end_redirect()
