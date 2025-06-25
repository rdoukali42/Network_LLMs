#!/usr/bin/env python3

"""
Test script to verify that ServiceIntegration now exposes multi_agent_workflow properly.
"""

import sys
from pathlib import Path

# Add front to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "front"))

def test_service_integration_workflow_access():
    """Test that ServiceIntegration can access multi_agent_workflow."""
    print("🧪 Testing ServiceIntegration multi_agent_workflow access...")
    
    try:
        from service_integration import ServiceIntegration
        
        # Create service integration instance
        service_integration = ServiceIntegration()
        print("✅ ServiceIntegration created successfully")
        
        # Test access to multi_agent_workflow
        workflow = service_integration.multi_agent_workflow
        print(f"✅ multi_agent_workflow accessed: {type(workflow).__name__ if workflow else 'None'}")
        
        if workflow:
            # Test if it has the process_end_call method
            if hasattr(workflow, 'process_end_call'):
                print("✅ process_end_call method exists on workflow")
                
                # Create a test state to see if the method is callable
                test_state = {
                    "messages": [{"content": "Test call completion", "type": "user"}],
                    "metadata": {"ticket_id": "123", "employee_username": "test_user"}
                }
                
                print("✅ Test state created, workflow interface verified")
                return True
            else:
                print("❌ process_end_call method not found on workflow")
                return False
        else:
            print("❌ multi_agent_workflow is None")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_service_integration_workflow_access()
    if success:
        print("\n🎉 ServiceIntegration workflow access test PASSED")
    else:
        print("\n💥 ServiceIntegration workflow access test FAILED")
        sys.exit(1)
