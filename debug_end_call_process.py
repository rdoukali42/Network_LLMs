#!/usr/bin/env python3
"""
Debug the END_CALL button process step by step
"""

import os
import sys
import json
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

def debug_end_call_process():
    """Debug what happens when END_CALL button is pressed"""
    print("🔍 DEBUGGING END_CALL PROCESS")
    print("=" * 60)
    
    # Step 1: Initialize system
    print("\n1. 🚀 Initializing system...")
    try:
        from main import AISystem
        from agents.vocal_assistant import VocalAssistantAgent, VocalResponse
        from front.database import db_manager
        
        system = AISystem()
        print("✅ System initialized")
        print(f"   Available agents: {list(system.agents.keys())}")
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False
    
    # Step 2: Create test scenario
    print("\n2. 📋 Creating test scenario...")
    test_ticket = {
        "id": "DEBUG_TICKET_001",
        "subject": "Database Performance Issue", 
        "description": "Our database is running slow, need help with optimization",
        "user": "test_user",
        "assigned_to": "yacoub",
        "status": "in_call"
    }
    
    test_employee = {
        "id": "6",
        "username": "yacoub",
        "full_name": "Yacoub Hossam",
        "email": "yacoub@company.com",
        "role_in_company": "Backend Developer",
        "expertise": "database optimization, SQL, .NET"
    }
    
    print(f"✅ Test ticket created: {test_ticket['id']}")
    print(f"✅ Test employee: {test_employee['full_name']} ({test_employee['username']})")
    
    # Step 3: Simulate conversation with redirect request
    print("\n3. 💬 Simulating conversation with redirect request...")
    conversation_data = {
        "conversation_summary": "Employee: I think this database issue would be better handled by our DevOps team. They have more experience with infrastructure optimization. REDIRECT_REQUESTED: True",
        "call_duration": "5 minutes"
    }
    
    print(f"✅ Conversation data prepared")
    print(f"   Summary: {conversation_data['conversation_summary'][:100]}...")
    
    # Step 4: Test VocalResponse parsing FIRST
    print("\n4. 🤖 Testing VocalResponse parsing...")
    vocal_response = VocalResponse({"response": conversation_data["conversation_summary"]})
    print(f"   🔍 Raw conversation: {conversation_data['conversation_summary']}")
    print(f"   🔍 Redirect requested: {vocal_response.redirect_requested}")
    print(f"   🔍 Redirect info: {vocal_response.redirect_employee_info}")
    print(f"   🔍 Conversation complete: {vocal_response.conversation_complete}")
    
    if not vocal_response.redirect_requested:
        print("❌ VocalResponse parsing failed - redirect not detected!")
        print("   This is why the redirect isn't working!")
        return False
    else:
        print("✅ VocalResponse parsing working - redirect detected")
    
    # Step 5: Test VocalAssistant end_call action
    print("\n5. 📞 Testing VocalAssistant END_CALL action...")
    try:
        vocal_agent = system.agents.get("vocal_assistant")
        if not vocal_agent:
            print("❌ VocalAssistant not found in system!")
            return False
        
        end_call_result = vocal_agent.run({
            "action": "end_call",
            "ticket_data": test_ticket,
            "employee_data": test_employee,
            "conversation_data": conversation_data,
            "conversation_summary": conversation_data["conversation_summary"]
        })
        
        print(f"✅ VocalAssistant end_call result:")
        print(f"   Status: {end_call_result.get('status')}")
        print(f"   Action: {end_call_result.get('action')}")
        print(f"   Conversation summary: {end_call_result.get('conversation_summary', 'None')[:100]}...")
        print(f"   Result keys: {list(end_call_result.keys())}")
        
    except Exception as e:
        print(f"❌ VocalAssistant end_call failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Test workflow state after end_call
    print("\n6. 🔄 Testing workflow state after end_call...")
    try:
        # Create workflow state as it would be after vocal_assistant step
        workflow_state = {
            "results": {
                "vocal_assistant": end_call_result,
                "ticket_data": test_ticket,
                "employee_data": test_employee,
                "hr_action": "assign"
            }
        }
        
        print(f"✅ Workflow state created")
        print(f"   Vocal assistant result type: {type(workflow_state['results']['vocal_assistant'])}")
        print(f"   Vocal assistant keys: {list(workflow_state['results']['vocal_assistant'].keys())}")
        
        # Test call completion handler
        workflow = system.workflow
        updated_state = workflow._call_completion_handler_step(workflow_state)
        
        print(f"✅ Call completion handler result:")
        print(f"   Call completed: {updated_state['results'].get('call_completed')}")
        print(f"   Current step: {updated_state.get('current_step')}")
        
    except Exception as e:
        print(f"❌ Call completion handler failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 7: Test redirect check routing
    print("\n7. 🔍 Testing redirect check routing...")
    try:
        routing_result = workflow._check_call_completion(updated_state)
        print(f"✅ Routing result: {routing_result}")
        
        if routing_result == "redirect":
            print("✅ Correctly routed to redirect flow!")
        elif routing_result == "complete":
            print("❌ Incorrectly routed to completion - this is the problem!")
            
            # Debug why it's going to complete
            call_completed = updated_state["results"].get("call_completed", False)
            print(f"   Call completed flag: {call_completed}")
            
            if call_completed:
                # Test the redirect check specifically
                redirect_check_result = workflow._check_for_redirect(updated_state)
                print(f"   Redirect check result: {redirect_check_result}")
            else:
                print("   Call not marked as completed - that's why no redirect check!")
        else:
            print(f"❌ Unknown routing result: {routing_result}")
            
    except Exception as e:
        print(f"❌ Redirect check routing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 8: Test full workflow execution
    print("\n8. 🚀 Testing full workflow execution...")
    try:
        # Create a proper workflow input that simulates end_call
        workflow_input = {
            "query": test_ticket["description"],
            "action": "end_call",
            "ticket_data": test_ticket,
            "employee_data": test_employee,
            "conversation_data": conversation_data
        }
        
        print(f"   Workflow input keys: {list(workflow_input.keys())}")
        
        # Note: The workflow doesn't directly accept end_call as input
        # We need to simulate the state after a call has been made
        print("   Simulating workflow state after call completion...")
        
        simulated_state = {
            "messages": [{"content": test_ticket["description"], "type": "user"}],
            "current_step": "call_completion_handler",
            "results": {
                "vocal_assistant": end_call_result,
                "ticket_data": test_ticket,
                "employee_data": test_employee,
                "hr_action": "assign",
                "call_completed": True  # Force call to be marked as completed
            },
            "metadata": workflow_input,
            "query": test_ticket["description"]
        }
        
        # Test routing from this state
        routing = workflow._check_call_completion(simulated_state)
        print(f"✅ Simulated routing result: {routing}")
        
        if routing == "redirect":
            print("✅ Would route to redirect flow!")
            
            # Test the redirect detection
            redirect_result = workflow._check_for_redirect(simulated_state)
            print(f"   Redirect detection result: {redirect_result}")
            
        else:
            print(f"❌ Would route to: {routing}")
            
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("🎯 DEBUG SUMMARY")
    print("=" * 60)
    print("✅ VocalResponse parsing: Working")
    print("✅ VocalAssistant end_call: Working") 
    print("✅ Call completion handler: Working")
    print("🔍 Redirect routing: Depends on call_completed flag")
    print("\n💡 Key insight: The issue might be in how the workflow")
    print("   determines if a call is actually completed vs initiated.")
    
    return True

if __name__ == "__main__":
    try:
        success = debug_end_call_process()
        if success:
            print("\n🎉 Debug completed successfully!")
        else:
            print("\n💥 Debug failed - see errors above")
    except Exception as e:
        print(f"\n💥 Debug script failed: {e}")
        import traceback
        traceback.print_exc()
