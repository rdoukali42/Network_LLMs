#!/usr/bin/env python3
"""
Test to verify that END_CALL now returns maestro final answer instead of fallback solution.
"""

import sys
import os
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.append('front')

def test_end_call_maestro_final():
    """Test that END_CALL returns maestro final answer, not fallback."""
    
    print("🧪 TESTING END_CALL MAESTRO FINAL FIX")
    print("=" * 50)
    
    try:
        from main import AISystem
        ai_system = AISystem()
        
        # Test END_CALL with a clear solution
        end_call_input = {
            'messages': [],
            'current_step': 'call_completion_handler',
            'results': {
                'hr_agent': {'action': 'assign', 'employee': 'patrick'},
                'vocal_assistant': {
                    'action': 'end_call',
                    'status': 'call_completed',
                    'conversation_summary': 'User: I need help with PostgreSQL connection pooling. The connections are timing out and affecting our application performance.\nEmployee: I can help with that. Let me check your configuration. It looks like your connection pool settings are too low for your current load.\nUser: How can we fix this?\nEmployee: I\'ll update the max_connections parameter in your postgresql.conf file and restart the service. This should resolve the timeout issues.\nUser: Great! Can you also show me how to monitor this in the future?\nEmployee: Absolutely. I\'ll set up monitoring alerts and show you the dashboard. You can track connection usage and performance metrics.\nUser: Perfect, thank you so much! Everything is working smoothly now.\nEmployee: You\'re welcome! The system should perform much better. Feel free to reach out if you need any assistance.',
                    'result': 'Call completed successfully'
                }
            },
            'metadata': {'ticket_id': 'test_456', 'employee_id': 'patrick'}
        }
        
        print("📞 Processing END_CALL with solution conversation...")
        result = ai_system.workflow.process_end_call(end_call_input)
        
        # Check what type of response we got
        final_response = result.get('final_response', '')
        vocal_action = result.get('vocal_action', 'unknown')
        
        print(f"\n📊 RESULTS:")
        print(f"   Vocal action: {vocal_action}")
        print(f"   Response length: {len(final_response)}")
        
        # Check for synthesized professional response format
        has_professional_format = any(marker in final_response for marker in [
            "Subject:", "Dear", "support ticket", "resolved", "Sincerely"
        ])
        
        # Check for raw conversation data (bad)
        has_raw_conversation = any(marker in final_response for marker in [
            "Employee: I have solved", "messages:", "conversation_summary"
        ])
        
        # Check for fallback (bad)
        is_fallback = "I couldn't find a direct answer" in final_response
        
        if has_professional_format and not has_raw_conversation and not is_fallback:
            print(f"✅ SUCCESS: Got professionally synthesized response!")
            print(f"   Professional format: ✅")
            print(f"   No raw conversation: ✅")
            print(f"   Not a fallback: ✅")
            print(f"   Response type: Professionally Synthesized")
            
            # Show the actual response
            print(f"\n📝 SYNTHESIZED RESPONSE:")
            print(f"   {final_response}")
            
            return True
            
        elif 'voice conversation' in final_response and 'Solution details:' in final_response:
            print(f"⚠️ PARTIAL: Got template format (not synthesized) but contains conversation")
            print(f"   Response type: Template Format")
            print(f"   Response: {final_response}")
            return False
            
        elif is_fallback:
            print(f"❌ ISSUE: Still getting HR referral instead of conversation solution")
            print(f"   Response type: HR Fallback")
            print(f"   Response: {final_response}")
            return False
            
        elif has_raw_conversation:
            print(f"❌ ISSUE: Raw conversation data detected in response")
            print(f"   Response type: Raw Conversation")
            print(f"   Response: {final_response}")
            return False
            
        else:
            print(f"⚠️ UNEXPECTED: Unknown response format")
            print(f"   Response type: Unknown")
            print(f"   Response: {final_response}")
            return False
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_end_call_maestro_final()
    print(f"\n🎯 RESULT: {'PASSED' if success else 'FAILED'}")
    
    if success:
        print(f"✅ END_CALL now returns Maestro Final answer!")
        print(f"✅ No more fallback solutions!")
        print(f"✅ Conversation details properly formatted!")
    else:
        print(f"❌ Still having issues with END_CALL processing")
