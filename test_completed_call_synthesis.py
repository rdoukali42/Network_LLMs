#!/usr/bin/env python3
"""
Test completed call with professional synthesis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graphs.workflow import MultiAgentWorkflow

def test_completed_call_synthesis():
    """Test that a completed call gets professionally synthesized"""
    print("🧪 TESTING COMPLETED CALL SYNTHESIS")
    print("=" * 50)
    
    # Initialize the system
    try:
        print("✅ Initializing system...")
        workflow = MultiAgentWorkflow()
        print("✅ Workflow initialized")
        
        # Test state with completed call (no redirect)
        test_state = {
            "messages": ["Test conversation"],
            "current_step": "end_call",
            "results": {
                "hr_agent": "Based on your request, I'll connect you with our IT support specialist who can help with database issues.",
                "vocal_assistant": {
                    "agent": "VocalAssistant",
                    "status": "call_completed", 
                    "action": "end_call",
                    "conversation_summary": "User: I need help with PostgreSQL connection pooling. The connections are timing out.\nEmployee: I see the issue. Your connection pool settings are too low. I'll update the max_connections parameter and restart the service.\nUser: Great, that worked! Thank you so much.\nEmployee: You're welcome! The system should perform much better now. Is there anything else?\nUser: No, that's perfect. Thanks again!\nEmployee: My pleasure. Have a great day!",
                    "conversation_data": {
                        "conversation_summary": "User reported PostgreSQL connection pooling issues with timeouts. Employee diagnosed low connection pool settings, updated max_connections parameter, and restarted service. Issue resolved successfully. User confirmed fix worked.",
                        "call_duration": "8 minutes"
                    }
                }
            },
            "metadata": {
                "request_type": "voice",
                "event_type": "end_call",
                "ticket_id": "test_synthesis_123",
                "employee_id": "sarah"
            }
        }
        
        print("📞 Processing completed call with conversation...")
        
        # Process the completed call directly
        result = workflow._handle_end_call(test_state)
        
        print(f"\n📊 RESULTS:")
        final_response = result["results"].get("final_response", "")
        synthesis = result["results"].get("synthesis", "")
        
        print(f"   Final response length: {len(final_response)}")
        print(f"   Synthesis length: {len(synthesis)}")
        
        # Check for professional synthesis
        has_professional_format = any(marker in final_response for marker in [
            "Support Ticket", "Thank you", "resolved", "issue", "support"
        ])
        
        # Check for unwanted raw data
        has_raw_conversation = any(marker in final_response for marker in [
            "User:", "Employee:", "conversation_summary:", "call_duration"
        ])
        
        # Check for template structure (old way)
        has_template = "voice conversation" in final_response and "Solution details:" in final_response
        
        print(f"   Professional format: {'✅' if has_professional_format else '❌'}")
        print(f"   No raw conversation: {'✅' if not has_raw_conversation else '❌'}")
        print(f"   Not using old template: {'✅' if not has_template else '❌'}")
        
        if has_professional_format and not has_raw_conversation and not has_template:
            print(f"✅ SUCCESS: Got professionally synthesized response!")
            print(f"\n📝 SYNTHESIZED RESPONSE:")
            print(f"{'='*60}")
            print(final_response)
            print(f"{'='*60}")
            return True
        else:
            print(f"❌ ISSUE: Response not properly synthesized")
            print(f"\n📝 ACTUAL RESPONSE:")
            print(f"{'='*60}")
            print(final_response)
            print(f"{'='*60}")
            return False
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_completed_call_synthesis()
    print(f"\n🎯 RESULT: {'PASSED' if success else 'FAILED'}")
    
    if success:
        print(f"✅ Completed calls now return professionally synthesized responses!")
        print(f"✅ No more raw conversation dumps!")
        print(f"✅ MaestroAgent synthesis working correctly!")
    else:
        print(f"❌ Still having issues with call completion synthesis")
