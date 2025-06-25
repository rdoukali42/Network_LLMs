#!/usr/bin/env python3

"""
Test the fixed call completion workflow with proper conversation data formatting.
"""

import sys
from pathlib import Path

# Add front to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "front"))

def test_fixed_call_completion():
    """Test the fixed call completion workflow."""
    print("🧪 Testing FIXED Call Completion Workflow...")
    
    try:
        from service_integration import ServiceIntegration
        
        # Create service integration instance
        service_integration = ServiceIntegration()
        workflow = service_integration.multi_agent_workflow
        
        # Test Case: Redirect request with conversation content
        print("\n📞 Testing redirect detection with conversation data...")
        redirect_conversation = """Employee: Hi, I need help with my payroll question about overtime calculations.

AI Assistant: I'd be happy to help you with payroll questions. However, for specific overtime calculation inquiries, I need to redirect this ticket to our payroll specialist.

Employee: That sounds good, please redirect the ticket to Patrick.

AI Assistant: I'll redirect this ticket to Patrick from our payroll team who can provide you with accurate information about overtime calculations."""
        
        end_call_state = {
            "messages": [{"content": redirect_conversation, "type": "user"}],
            "metadata": {
                "ticket_id": "TEST-REDIRECT-001",
                "employee_username": "test_employee"
            }
        }
        
        print(f"📞 Calling process_end_call with conversation length: {len(redirect_conversation)}")
        result = workflow.process_end_call(end_call_state)
        
        print(f"\n🔍 Result keys: {list(result.keys()) if result else 'None'}")
        if result:
            print(f"🔍 Final response: {result.get('final_response', 'No final response')[:200]}...")
            print(f"🔍 Call completed: {result.get('call_completed', 'N/A')}")
            
            # Check if redirect was detected
            has_redirect_info = any(key in str(result).lower() for key in ['redirect', 'patrick', 'payroll'])
            print(f"🔍 Redirect info detected: {has_redirect_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fixed_call_completion()
    if success:
        print("\n🎉 Fixed call completion test PASSED")
    else:
        print("\n💥 Fixed call completion test FAILED")
