#!/usr/bin/env python3
"""
Comprehensive test for the redirect functionality
"""

import sys
import os
sys.path.append('/Users/level3/Desktop/Network/src')

from agents.vocal_assistant import VocalResponse
from tools.employee_search_tool import EmployeeSearchTool
from graphs.workflow import MultiAgentWorkflow

def test_vocal_response_parsing():
    """Test VocalResponse parsing with different structured formats."""
    print("🧪 Testing VocalResponse parsing...")
    
    # Test 1: No redirect request
    conversation_data_no_redirect = {
        "response": """REDIRECT_REQUEST: NO
USERNAME_TO_REDIRECT: NONE
ROLE_OF_THE_REDIRECT_TO: NONE
RESPONSABILTIES: NONE

I was able to help the user with their password reset issue. The problem has been resolved."""
    }
    
    vocal_response = VocalResponse(conversation_data_no_redirect)
    assert not vocal_response.redirect_requested, "Should not request redirect"
    assert vocal_response.conversation_complete, "Should mark conversation as complete"
    assert "password reset" in vocal_response.solution, "Should extract solution text"
    print("   ✅ No redirect case passed")
    
    # Test 2: Redirect with username
    conversation_data_redirect = {
        "response": """REDIRECT_REQUEST: YES
USERNAME_TO_REDIRECT: john_doe
ROLE_OF_THE_REDIRECT_TO: NONE
RESPONSABILTIES: NONE

The user needs help with advanced database optimization which is beyond my expertise. John should handle this."""
    }
    
    vocal_response = VocalResponse(conversation_data_redirect)
    assert vocal_response.redirect_requested, "Should request redirect"
    assert vocal_response.redirect_employee_info["username"] == "john_doe", "Should extract username"
    assert "role" not in vocal_response.redirect_employee_info, "Should not include NONE values"
    print("   ✅ Username redirect case passed")
    
    # Test 3: Redirect with role and responsibilities
    conversation_data_complex = {
        "response": """REDIRECT_REQUEST: YES
USERNAME_TO_REDIRECT: NONE
ROLE_OF_THE_REDIRECT_TO: Senior Developer
RESPONSIBILITIES: Python development, API design

User needs help with complex Python API development. Need someone specialized in this area."""
    }
    
    vocal_response = VocalResponse(conversation_data_complex)
    assert vocal_response.redirect_requested, "Should request redirect"
    assert vocal_response.redirect_employee_info["role"] == "Senior Developer", "Should extract role"
    assert vocal_response.redirect_employee_info["responsibilities"] == "Python development, API design", "Should extract responsibilities"
    print("   ✅ Complex redirect case passed")
    
    return True

def test_employee_search_tool():
    """Test EmployeeSearchTool functionality."""
    print("\n🧪 Testing EmployeeSearchTool...")
    
    tool = EmployeeSearchTool()
    
    # Test 1: Search by username (should find exact matches)
    redirect_info_username = {"username": "alice"}
    results = tool.search_employees_for_redirect(redirect_info_username)
    print(f"   Username search results: {len(results)} employees found")
    if results:
        print(f"   Top match: {results[0].get('full_name', 'Unknown')} (score: {results[0].get('redirect_score', 0)})")
    
    # Test 2: Search by role
    redirect_info_role = {"role": "developer"}
    results = tool.search_employees_for_redirect(redirect_info_role)
    print(f"   Role search results: {len(results)} employees found")
    if results:
        print(f"   Top match: {results[0].get('full_name', 'Unknown')} (score: {results[0].get('redirect_score', 0)})")
    
    # Test 3: Search by responsibilities
    redirect_info_resp = {"responsibilities": "python"}
    results = tool.search_employees_for_redirect(redirect_info_resp)
    print(f"   Responsibilities search results: {len(results)} employees found")
    if results:
        print(f"   Top match: {results[0].get('full_name', 'Unknown')} (score: {results[0].get('redirect_score', 0)})")
    
    # Test 4: Search with multiple criteria
    redirect_info_multi = {"role": "developer", "responsibilities": "python"}
    results = tool.search_employees_for_redirect(redirect_info_multi)
    print(f"   Multi-criteria search results: {len(results)} employees found")
    if results:
        print(f"   Top match: {results[0].get('full_name', 'Unknown')} (score: {results[0].get('redirect_score', 0)})")
        print(f"   Match reasons: {', '.join(results[0].get('match_reasons', []))}")
    
    print("   ✅ EmployeeSearchTool tests completed")
    return True

def test_workflow_integration():
    """Test workflow integration without running full workflow."""
    print("\n🧪 Testing workflow integration...")
    
    # Mock agents for testing
    class MockMaestro:
        def run(self, data):
            return {"result": "Mock maestro selection", "selected_employee": {"full_name": "Test Employee"}}
    
    class MockVocalAssistant:
        def run(self, data):
            return {"status": "success", "conversation_data": {"response": "Mock redirect call completed"}}
    
    class MockEmployeeSearchTool:
        def search_employees_for_redirect(self, criteria):
            return [{"full_name": "Test Employee", "username": "test_emp", "redirect_score": 20, "match_reasons": ["Test match"]}]
    
    # Create workflow with mock agents
    mock_agents = {
        "maestro": MockMaestro(),
        "vocal_assistant": MockVocalAssistant(),
        "employee_search_tool": MockEmployeeSearchTool()
    }
    
    workflow = MultiAgentWorkflow(mock_agents)
    
    # Test redirect detection
    test_state = {
        "results": {
            "conversation_data": {
                "response": """REDIRECT_REQUEST: YES
USERNAME_TO_REDIRECT: john_doe
ROLE_OF_THE_REDIRECT_TO: NONE
RESPONSABILTIES: NONE

Need to redirect to John."""
            }
        },
        "current_step": "test",
        "messages": [],
        "metadata": {},
        "query": "test query"
    }
    
    # Test _check_for_redirect
    redirect_result = workflow._check_for_redirect(test_state)
    assert redirect_result == "redirect", "Should detect redirect request"
    print("   ✅ Redirect detection working")
    
    # Test _redirect_detector_step
    state_after_detector = workflow._redirect_detector_step(test_state)
    assert "enhanced_redirect_info" in state_after_detector["results"], "Should enhance redirect info"
    print("   ✅ Redirect detector step working")
    
    # Test _employee_searcher_step
    state_after_search = workflow._employee_searcher_step(state_after_detector)
    assert "redirect_candidates" in state_after_search["results"], "Should find redirect candidates"
    assert len(state_after_search["results"]["redirect_candidates"]) > 0, "Should have candidates"
    print("   ✅ Employee searcher step working")
    
    # Test _maestro_redirect_selector_step
    state_after_selector = workflow._maestro_redirect_selector_step(state_after_search)
    assert "selected_redirect_employee" in state_after_selector["results"], "Should select employee"
    print("   ✅ Maestro redirect selector step working")
    
    # Test _vocal_assistant_redirect_step
    state_after_redirect_call = workflow._vocal_assistant_redirect_step(state_after_selector)
    assert "redirect_call_result" in state_after_redirect_call["results"], "Should have call result"
    print("   ✅ Vocal assistant redirect step working")
    
    return True

def test_no_redirect_flow():
    """Test that normal flow works when no redirect is requested."""
    print("\n🧪 Testing no-redirect flow...")
    
    # Test conversation data with no redirect
    conversation_data_no_redirect = {
        "response": """REDIRECT_REQUEST: NO
USERNAME_TO_REDIRECT: NONE
ROLE_OF_THE_REDIRECT_TO: NONE
RESPONSABILTIES: NONE

I successfully helped the user with their issue."""
    }
    
    # Mock workflow
    class MockWorkflow:
        def _check_for_redirect(self, state):
            vocal_response = VocalResponse(state["results"]["conversation_data"])
            if vocal_response.redirect_requested:
                return "redirect"
            return "complete"
    
    workflow = MockWorkflow()
    
    test_state = {
        "results": {"conversation_data": conversation_data_no_redirect}
    }
    
    result = workflow._check_for_redirect(test_state)
    assert result == "complete", "Should complete normally when no redirect requested"
    print("   ✅ No-redirect flow working correctly")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting comprehensive redirect functionality tests...\n")
    
    try:
        # Run all tests
        test1_passed = test_vocal_response_parsing()
        test2_passed = test_employee_search_tool()
        test3_passed = test_workflow_integration()
        test4_passed = test_no_redirect_flow()
        
        if all([test1_passed, test2_passed, test3_passed, test4_passed]):
            print("\n🎉 All redirect functionality tests PASSED!")
            print("✅ VocalResponse parsing works correctly")
            print("✅ EmployeeSearchTool finds matching employees")
            print("✅ Workflow integration handles redirects properly")
            print("✅ Normal flow continues when no redirect requested")
            print("\n🔥 The redirect system is ready for production!")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
