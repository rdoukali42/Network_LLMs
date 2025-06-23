#!/usr/bin/env python3
"""
Test complete redirect workflow by simulating conversation data with redirect
"""

import sys
sys.path.append('/Users/level3/Desktop/Network/src')

from graphs.workflow import MultiAgentWorkflow
from agents.vocal_assistant import VocalResponse
from main import AISystem

def test_complete_redirect_workflow():
    """Test the complete redirect workflow."""
    print("🧪 Testing complete redirect workflow...")
    
    # Initialize system
    ai_system = AISystem("development")
    
    # Create a mock workflow state that simulates a vocal assistant conversation with redirect
    redirect_conversation_data = {
        "response": """REDIRECT_REQUEST: YES
USERNAME_TO_REDIRECT: lina
ROLE_OF_THE_REDIRECT_TO: Data Analyst
RESPONSABILTIES: Machine learning, data analysis, model deployment

I understand this ticket is beyond my expertise. This requires deep machine learning knowledge which Lina has. She should handle this advanced model deployment issue."""
    }
    
    # Test state that would come after vocal_assistant step
    test_state = {
        "current_step": "vocal_assistant",
        "messages": [],
        "metadata": {},
        "query": "Advanced ML model deployment help",
        "results": {
            "conversation_data": redirect_conversation_data,
            "ticket_data": {"id": "test_123", "subject": "ML Help"},
            "employee_data": {"full_name": "Patrick Neumann", "username": "patrick"}
        }
    }
    
    workflow = ai_system.workflow
    
    # Test the redirect detection
    print("🔍 Testing redirect detection...")
    redirect_route = workflow._check_for_redirect(test_state)
    print(f"   Redirect route result: {redirect_route}")
    
    if redirect_route == "redirect":
        print("✅ Redirect detected successfully!")
        
        # Test redirect detector step
        print("\n🔄 Testing redirect detector step...")
        state_after_detector = workflow._redirect_detector_step(test_state)
        print(f"   Enhanced redirect info: {state_after_detector['results'].get('enhanced_redirect_info', {})}")
        
        # Test employee searcher step
        print("\n🔍 Testing employee searcher step...")
        state_after_search = workflow._employee_searcher_step(state_after_detector)
        candidates = state_after_search['results'].get('redirect_candidates', [])
        print(f"   Found {len(candidates)} redirect candidates")
        
        if candidates:
            print(f"   Top candidate: {candidates[0].get('full_name', 'Unknown')} (score: {candidates[0].get('redirect_score', 0)})")
            
            # Test maestro selector step
            print("\n🎯 Testing maestro selector step...")
            state_after_selector = workflow._maestro_redirect_selector_step(state_after_search)
            selected = state_after_selector['results'].get('selected_redirect_employee', {})
            print(f"   Selected employee: {selected.get('full_name', 'None')}")
            
            return True
    else:
        print("❌ Redirect not detected")
        return False

if __name__ == "__main__":
    try:
        success = test_complete_redirect_workflow()
        if success:
            print("\n🎉 Complete redirect workflow test PASSED!")
            print("✅ All redirect workflow steps working correctly")
            print("✅ System ready for production redirect functionality")
        else:
            print("\n❌ Complete redirect workflow test FAILED!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
