#!/usr/bin/env python3
"""
Test the NEW redirect workflow that goes directly to vocal_assistant after redirect.
This tests with an existing employee in the database.
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_redirect_to_existing_employee():
    """Test redirect to an existing employee in the database."""
    
    print("🧪 TESTING REDIRECT TO EXISTING EMPLOYEE")
    print("=" * 60)
    
    try:
        from main import AISystem
        ai_system = AISystem()
        
        if not ai_system.workflow:
            print("❌ Workflow not initialized!")
            return False
            
        print("✅ AI System initialized successfully")
        
        # Use an existing employee from the database
        # Let's redirect to Yacoub (full-stack developer) who should handle database-related issues
        realistic_conversation = """You: I need help with a PostgreSQL database connection issue.
Employee: Hi! I'm Sarah from QA. I can try to help, but this seems like a backend development issue.
You: The connection string keeps timing out and I'm not sure about the configuration.
Employee: This is definitely more of a backend development task. I think Yacoub would be much better suited for this - he's our full-stack developer and has expertise with databases and SQL.
You: Can you redirect this to Yacoub then?
Employee: Absolutely! I'll redirect this to Yacoub right away. He has experience with database optimization and backend systems."""
        
        print(f"📝 Test Conversation (redirecting to Yacoub):")
        print(f"   Length: {len(realistic_conversation)} characters")
        print(f"   Contains 'Yacoub': {'Yacoub' in realistic_conversation}")
        print(f"   Contains 'redirect': {'redirect' in realistic_conversation.lower()}")
        
        # Create END_CALL input that should redirect to Yacoub
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
                    "conversation_summary": realistic_conversation,
                    "conversation_data": {
                        "conversation_summary": realistic_conversation,
                        "call_duration": "completed",
                        "full_conversation": realistic_conversation
                    },
                    "result": "Voice call completed with Sarah Becker",
                    "end_call_triggered": True
                }
            },
            "metadata": {
                "request_type": "voice",
                "event_type": "end_call",
                "ticket_id": "TEST001",
                "employee_id": "sarah"
            }
        }
        
        print(f"\n🔄 PROCESSING REDIRECT TO YACOUB...")
        result = ai_system.workflow.process_end_call(end_call_input)
        
        print(f"\n📊 RESULT ANALYSIS:")
        print(f"   Result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if "error" in result:
            print(f"❌ WORKFLOW ERROR: {result['error']}")
            return False
        
        # Check for redirect detection
        redirect_info = result.get("results", {}).get("redirect_info") if "results" in result else None
        
        # 🔧 NEW: Check if this is a redirect call initiation (new behavior)
        call_active = result.get("call_active", False)
        redirect_call_initiated = result.get("redirect_call_initiated", False)
        status = result.get("status", "")
        call_info = result.get("results", {}).get("call_info") if "results" in result else None
        
        print(f"   Redirect info: {redirect_info}")
        print(f"   Call active: {call_active}")
        print(f"   Redirect call initiated: {redirect_call_initiated}")
        print(f"   Status: {status}")
        print(f"   Call info: {call_info}")
        
        if redirect_info or (call_active and redirect_call_initiated):
            print(f"✅ REDIRECT DETECTED!")
            
            if redirect_info:
                print(f"   Redirect info: {redirect_info}")
            
            # Check if this is the new redirect call initiation behavior
            if call_info and call_info.get("employee_name"):
                print(f"✅ REDIRECT CALL INITIATED!")
                print(f"   New employee: {call_info.get('employee_name')}")
                print(f"   Username: {call_info.get('employee_username')}")
                
                if call_info.get('employee_username', '').lower() == 'yacoub':
                    print(f"✅ CORRECT EMPLOYEE SELECTED: Yacoub")
                    print(f"✅ CALL INITIATED WITH YACOUB!")
                    return True
                else:
                    print(f"❌ WRONG EMPLOYEE SELECTED: {call_info.get('employee_username')}")
                    return False
            
            # Fallback to old behavior check
            candidates = result.get("results", {}).get("redirect_candidates", []) if "results" in result else []
            yacoub_found = any(
                candidate.get('username', '').lower() == 'yacoub' 
                for candidate in candidates
            )
            
            if yacoub_found:
                print(f"✅ YACOUB FOUND AS CANDIDATE!")
                
                # Check if HR action was set for new call
                hr_action = result.get("hr_action")
                employee_data = result.get("employee_data", {})
                redirect_context = result.get("redirect_context", {})
                
                if hr_action == "assign" and employee_data:
                    print(f"✅ DATA FORMATTED FOR VOCAL_ASSISTANT!")
                    print(f"   HR Action: {hr_action}")
                    print(f"   New Employee: {employee_data.get('full_name', 'Unknown')}")
                    print(f"   Username: {employee_data.get('username', 'Unknown')}")
                    print(f"   Is Redirect: {redirect_context.get('is_redirect', False)}")
                    
                    if employee_data.get('username', '').lower() == 'yacoub':
                        print(f"✅ CORRECT EMPLOYEE SELECTED: Yacoub")
                        return True
                    else:
                        print(f"❌ WRONG EMPLOYEE SELECTED: {employee_data.get('username')}")
                        return False
                else:
                    print(f"❌ DATA NOT FORMATTED FOR VOCAL_ASSISTANT")
                    print(f"   HR Action: {hr_action}")
                    print(f"   Employee Data: {bool(employee_data)}")
                    return False
            else:
                print(f"❌ YACOUB NOT FOUND AS CANDIDATE")
                print(f"   Candidates: {[c.get('username') for c in candidates]}")
                return False
        else:
            print(f"❌ NO REDIRECT DETECTED!")
            return False
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 TESTING NEW REDIRECT WORKFLOW")
    print("Testing redirect that should call vocal_assistant with new employee")
    print("=" * 70)
    
    success = test_redirect_to_existing_employee()
    
    if success:
        print(f"\n🎉 TEST PASSED!")
        print(f"   ✅ Redirect detected correctly")
        print(f"   ✅ Existing employee found (Yacoub)")
        print(f"   ✅ Data formatted for vocal_assistant")
        print(f"   ✅ Ready for new call initiation")
    else:
        print(f"\n❌ TEST FAILED!")
        print(f"   The new redirect workflow needs debugging")
    
    exit(0 if success else 1)
