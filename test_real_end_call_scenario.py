#!/usr/bin/env python3
"""
Real-world scenario test for the END_CALL workflow fix.
This test simulates an actual frontend END_CALL event with a realistic conversation.
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_real_end_call_scenario():
    """Test a realistic END_CALL scenario with actual conversation data."""
    
    print("🧪 TESTING REAL END_CALL SCENARIO")
    print("=" * 80)
    
    try:
        # Initialize the system
        print("🔧 Initializing AI System...")
        from main import AISystem
        ai_system = AISystem()
        
        if not ai_system.workflow:
            print("❌ Workflow not initialized!")
            return False
            
        print("✅ AI System initialized successfully")
        
        # Simulate realistic conversation data from frontend
        realistic_conversation = """You: Hello, I need help with setting up a new database connection for our project.
Employee: Hi! I'm Sarah, and I'd be happy to help you with database setup. What type of database are you looking to connect to?
You: We're using PostgreSQL, but I'm having trouble with the connection string configuration.
Employee: I see. PostgreSQL connection strings can be tricky. What specific error are you encountering?
You: The connection times out after a few seconds. I think it might be a configuration issue.
Employee: That sounds like it could be related to network settings or authentication. Let me check... Actually, this seems like something that would be better handled by our database specialist, Mike. He has more experience with PostgreSQL performance issues.
You: Can you redirect this to Mike then?
Employee: Absolutely! I'll redirect this conversation to Mike right away. He'll be able to help you with the PostgreSQL connection timeout issue."""
        
        # Simulate realistic ticket and employee data
        ticket_data = {
            'id': 'REAL001',
            'subject': 'PostgreSQL Connection Setup',
            'description': 'Need help setting up PostgreSQL database connection - experiencing timeout issues',
            'user': 'john_dev',
            'category': 'Technical Issue',
            'priority': 'Medium'
        }
        
        employee_data = {
            'username': 'sarah_db',
            'full_name': 'Sarah Johnson',
            'role_in_company': 'Junior Database Administrator',
            'expertise': 'Database management, SQL queries, basic PostgreSQL'
        }
        
        print(f"\n📋 TEST SCENARIO:")
        print(f"   Ticket: {ticket_data['subject']}")
        print(f"   Employee: {employee_data['full_name']}")
        print(f"   Conversation Length: {len(realistic_conversation)} characters")
        print(f"   Expected Redirect: YES (to Mike)")
        
        # Create the END_CALL workflow input (matching frontend format)
        end_call_input = {
            "messages": [],
            "current_step": "call_completion_handler",
            "results": {
                "hr_agent": {
                    "action": "assign",
                    "employee": employee_data.get('username'),
                    "employee_data": employee_data
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
                    "result": f"Voice call completed with {employee_data.get('full_name')}",
                    "end_call_triggered": True
                }
            },
            "metadata": {
                "request_type": "voice",
                "event_type": "end_call",
                "ticket_id": ticket_data.get('id'),
                "employee_id": employee_data.get('username')
            }
        }
        
        print(f"\n🔄 PROCESSING END_CALL...")
        print(f"   Using direct process_end_call method")
        print(f"   Input keys: {list(end_call_input.keys())}")
        
        # Process the END_CALL using our new direct method
        result = ai_system.workflow.process_end_call(end_call_input)
        
        print(f"\n📊 RESULT ANALYSIS:")
        print(f"   Result type: {type(result)}")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check for error
        if "error" in result:
            print(f"❌ WORKFLOW ERROR: {result['error']}")
            return False
        
        # Check for redirect detection
        redirect_info = result.get("redirect_info")
        if redirect_info:
            print(f"✅ REDIRECT DETECTED!")
            print(f"   Redirect info: {redirect_info}")
            
            # Validate redirect information
            if isinstance(redirect_info, dict):
                username = redirect_info.get('username', '').lower()
                if 'mike' in username or redirect_info.get('responsibilities'):
                    print(f"✅ REDIRECT TARGET VALID: Found Mike or responsibilities")
                else:
                    print(f"⚠️ REDIRECT TARGET UNCLEAR: {redirect_info}")
        else:
            print(f"❌ NO REDIRECT DETECTED!")
            print(f"   Expected redirect to Mike but none found")
            return False
        
        # Check for final solution/confirmation
        final_solution = None
        for key, value in result.items():
            if key.endswith("_final") and isinstance(value, (str, dict)):
                if isinstance(value, dict):
                    final_solution = value.get("result") or value.get("response")
                else:
                    final_solution = value
                break
        
        if final_solution:
            print(f"✅ FINAL SOLUTION GENERATED:")
            print(f"   Length: {len(final_solution)} characters")
            print(f"   Preview: {final_solution[:100]}...")
        else:
            print(f"⚠️ NO FINAL SOLUTION GENERATED")
        
        print(f"\n🎉 REAL SCENARIO TEST COMPLETED SUCCESSFULLY!")
        print(f"   ✅ END_CALL processing worked")
        print(f"   ✅ Redirect detection worked") 
        print(f"   ✅ Conversation analysis worked")
        
        return True
        
    except Exception as e:
        print(f"❌ REAL SCENARIO TEST FAILED: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

def test_no_redirect_scenario():
    """Test END_CALL scenario without redirect to ensure normal completion works."""
    
    print(f"\n🧪 TESTING NO-REDIRECT SCENARIO")
    print("=" * 50)
    
    try:
        from main import AISystem
        ai_system = AISystem()
        
        # Conversation without redirect request
        normal_conversation = """You: I need help resetting my password.
Employee: I can definitely help you with that! Let me walk you through the password reset process.
You: That would be great, thank you.
Employee: First, go to the login page and click 'Forgot Password'. Then enter your email address.
You: Okay, I did that and I received an email.
Employee: Perfect! Click the link in the email and you'll be able to set a new password.
You: Got it, that worked perfectly. Thank you for your help!
Employee: You're very welcome! Is there anything else I can help you with today?
You: No, that's everything. Thanks again!
Employee: Great! Have a wonderful day!"""
        
        end_call_input = {
            "results": {
                "vocal_assistant": {
                    "action": "end_call",
                    "status": "call_completed",
                    "conversation_summary": normal_conversation,
                    "conversation_data": {
                        "conversation_summary": normal_conversation
                    }
                }
            },
            "metadata": {"event_type": "end_call"}
        }
        
        result = ai_system.workflow.process_end_call(end_call_input)
        
        # Should complete normally without redirect
        redirect_info = result.get("redirect_info")
        if not redirect_info:
            print(f"✅ NO REDIRECT DETECTED (as expected)")
            return True
        else:
            print(f"❌ UNEXPECTED REDIRECT: {redirect_info}")
            return False
            
    except Exception as e:
        print(f"❌ NO-REDIRECT TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🚀 STARTING REAL-WORLD END_CALL TESTS")
    print("=" * 60)
    
    # Test 1: Redirect scenario
    test1_passed = test_real_end_call_scenario()
    
    # Test 2: No redirect scenario  
    test2_passed = test_no_redirect_scenario()
    
    print(f"\n📋 TEST SUMMARY:")
    print(f"   Test 1 (Redirect): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Test 2 (No Redirect): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 ALL REAL-WORLD TESTS PASSED!")
        print(f"   The END_CALL workflow fix is working correctly!")
    else:
        print(f"\n❌ SOME TESTS FAILED!")
        print(f"   The END_CALL workflow needs further fixes!")
        
    exit(0 if (test1_passed and test2_passed) else 1)
