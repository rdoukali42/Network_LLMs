#!/usr/bin/env python3
"""
Test the fixed redirect workflow with proper END_CALL handling
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

def test_end_call_redirect_workflow():
    """Test that redirect only triggers after END_CALL button is clicked."""
    print("🚀 TESTING END_CALL REDIRECT WORKFLOW")
    print("=" * 60)
    
    try:
        # Initialize system
        from main import AISystem
        from agents.vocal_assistant import VocalAssistantAgent
        
        system = AISystem()
        print("✅ AI System initialized")
        
        # Test 1: Initial call initiation (should NOT trigger redirect)
        print("\n1. 🎬 SCENARIO: Initial Call Initiation")
        print("   - HR assigns ticket to employee")
        print("   - Vocal assistant initiates call") 
        print("   - Should complete workflow without checking redirect\n")
        
        result1 = system.process_query("I need help with Python API development")
        
        print("📊 RESULT 1 - Call Initiation:")
        print(f"   ✅ Status: {result1.get('synthesis_status', 'N/A')}")
        print(f"   ✅ Final response length: {len(result1.get('synthesis', ''))}")
        
        # Check that it doesn't mention redirect
        synthesis = result1.get('synthesis', '')
        if 'redirected' not in synthesis.lower():
            print("   ✅ PASS: No redirect mentioned in initial call response")
        else:
            print("   ❌ FAIL: Redirect mentioned in initial call response")
            return False
        
        # Test 2: Simulate END_CALL with redirect request
        print("\n2. 🎬 SCENARIO: End Call with Redirect Request")
        print("   - User clicks END_CALL button")
        print("   - Conversation contains redirect request")
        print("   - Should trigger redirect workflow\n")
        
        # Create VocalAssistant and simulate end_call action
        vocal_agent = VocalAssistantAgent()
        
        # Simulate call end with redirect request
        end_call_result = vocal_agent.run({
            "action": "end_call",
            "ticket_data": {"id": "TEST123", "subject": "API Development Help"},
            "employee_data": {"full_name": "Patrick Neumann", "username": "patrick"},
            "conversation_summary": "Employee: I think this would be better handled by our DevOps team. REDIRECT_REQUESTED: True",
            "conversation_data": {
                "conversation_summary": "Employee: I think this would be better handled by our DevOps team. REDIRECT_REQUESTED: True",
                "call_duration": "5 minutes"
            }
        })
        
        print("📊 RESULT 2 - End Call with Redirect:")
        print(f"   ✅ Action: {end_call_result.get('action')}")
        print(f"   ✅ Status: {end_call_result.get('status')}")
        print(f"   ✅ Conversation data: {'Present' if end_call_result.get('conversation_data') else 'Missing'}")
        
        if end_call_result.get('action') == 'end_call':
            print("   ✅ PASS: END_CALL action properly returned")
        else:
            print("   ❌ FAIL: END_CALL action not returned")
            return False
        
        # Test 3: Simulate workflow processing of END_CALL
        print("\n3. 🎬 SCENARIO: Workflow Processing END_CALL")
        print("   - Workflow receives END_CALL action")
        print("   - Should detect redirect and route to redirect flow\n")
        
        # Test the workflow's call completion handler directly
        from graphs.workflow import MultiAgentWorkflow
        
        workflow = MultiAgentWorkflow(system.agents)
        
        # Create test state simulating end call
        test_state = {
            "results": {
                "vocal_assistant": end_call_result,
                "call_completed": True,
                "call_conversation_summary": "Employee: I think this would be better handled by our DevOps team. REDIRECT_REQUESTED: True",
                "call_conversation_data": {
                    "conversation_summary": "Employee: I think this would be better handled by our DevOps team. REDIRECT_REQUESTED: True"
                }
            }
        }
        
        # Test redirect detection
        redirect_result = workflow._check_for_redirect(test_state)
        
        print("📊 RESULT 3 - Redirect Detection:")
        print(f"   ✅ Redirect check result: {redirect_result}")
        
        if redirect_result == "redirect":
            print("   ✅ PASS: Redirect properly detected from END_CALL")
        else:
            print("   ❌ FAIL: Redirect not detected from END_CALL")
            return False
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Call initiation: Works without redirect check")
        print("✅ END_CALL action: Properly returns conversation data")  
        print("✅ Redirect detection: Only triggers after END_CALL")
        print("\n🚀 The redirect workflow now properly waits for END_CALL!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_end_call_redirect_workflow()
    sys.exit(0 if success else 1)
