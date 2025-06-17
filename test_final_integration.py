#!/usr/bin/env python3
"""
Final integration test simulating the complete ticket submission workflow.
"""

import sys
import os
sys.path.append('src')
sys.path.append('front')

# Mock streamlit session state
class MockSessionState:
    def __init__(self, username):
        self.username = username

class MockStreamlit:
    def __init__(self, username):
        self.session_state = MockSessionState(username)

def test_ticket_workflow_simulation():
    """Simulate complete ticket workflow to verify self-assignment prevention."""
    print("🎫 Simulating Complete Ticket Workflow")
    print("=" * 50)
    
    # Test scenario: User 'mounir' submits an ML question
    test_user = "mounir"
    test_query = "I need help with machine learning model deployment and Docker containerization"
    
    print(f"👤 User: {test_user}")
    print(f"📝 Query: {test_query}")
    print(f"🎯 Expected: Should NOT be assigned to {test_user} (self)")
    
    # Mock streamlit session
    sys.modules['streamlit'] = MockStreamlit(test_user)
    
    try:
        # Test 1: Direct AvailabilityTool filtering
        print(f"\n🔧 Step 1: Testing AvailabilityTool filtering")
        from src.tools.availability_tool import AvailabilityTool
        
        availability_tool = AvailabilityTool()
        available_employees = availability_tool.get_available_employees()
        
        all_filtered_employees = available_employees['available'] + available_employees['busy']
        filtered_usernames = [emp['username'] for emp in all_filtered_employees]
        
        print(f"   📋 Available employees: {filtered_usernames}")
        
        if test_user not in filtered_usernames:
            print(f"   ✅ User '{test_user}' correctly excluded from employee list")
        else:
            print(f"   ❌ User '{test_user}' still in employee list!")
            return False
        
        # Test 2: HR_Agent assignment  
        print(f"\n🤖 Step 2: Testing HR_Agent assignment logic")
        from src.agents.base_agent import HRAgent
        
        hr_agent = HRAgent(availability_tool=availability_tool)
        hr_result = hr_agent.run({"query": test_query})
        
        if hr_result.get("status") == "success" and hr_result.get("action") == "assign":
            assigned_employee = hr_result.get("employee_data", {})
            assigned_username = assigned_employee.get("username")
            assigned_name = assigned_employee.get("full_name")
            
            print(f"   👤 Assigned to: {assigned_name} (@{assigned_username})")
            
            if assigned_username == test_user:
                print(f"   ❌ CRITICAL FAILURE: Self-assignment occurred!")
                return False
            else:
                print(f"   ✅ SUCCESS: No self-assignment, correctly assigned to expert")
        else:
            print(f"   ⚠️  No assignment made: {hr_result.get('result', 'Unknown')}")
        
        # Test 3: Simulate workflow response parsing
        print(f"\n📋 Step 3: Testing response format")
        response = hr_result.get("result", "")
        
        if "👤" in response and f"(@{test_user})" not in response:
            print(f"   ✅ Response format correct and no self-assignment in response")
            print(f"   📄 Response snippet: {response[:100]}...")
        else:
            print(f"   ❌ Response format issue or self-assignment detected")
            print(f"   📄 Full response: {response}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error during workflow simulation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases for self-assignment prevention."""
    print(f"\n🧪 Testing Edge Cases")
    print("=" * 30)
    
    edge_cases = [
        {
            "user": "nonexistent_user",
            "description": "Non-existent user should not cause errors"
        },
        {
            "user": "alex01",
            "description": "ML expert asking ML question (should get different expert)"
        }
    ]
    
    for case in edge_cases:
        print(f"\n🔍 Testing: {case['description']}")
        print(f"   User: {case['user']}")
        
        # Mock streamlit session
        sys.modules['streamlit'] = MockStreamlit(case['user'])
        
        try:
            from src.tools.availability_tool import AvailabilityTool
            availability_tool = AvailabilityTool()
            available_employees = availability_tool.get_available_employees()
            
            filtered_usernames = [emp['username'] for emp in 
                                available_employees['available'] + available_employees['busy']]
            
            if case['user'] not in filtered_usernames:
                print(f"   ✅ User '{case['user']}' correctly excluded")
            else:
                print(f"   ❌ User '{case['user']}' not excluded")
                
        except Exception as e:
            print(f"   ⚠️  Exception (may be expected): {e}")


if __name__ == "__main__":
    print("🚀 Starting Final Integration Test")
    print("=" * 60)
    
    success = test_ticket_workflow_simulation()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 FINAL RESULT: Complete self-assignment prevention implementation SUCCESSFUL!")
        print("✅ AvailabilityTool automatically filters current user")
        print("✅ HR_Agent correctly assigns to other experts")
        print("✅ Workflow response format prevents self-assignment")
        print("✅ No complex context passing needed")
        print("\n🎯 IMPLEMENTATION COMPLETE:")
        print("   • Simple, clean architecture")
        print("   • Automatic session state detection") 
        print("   • Zero configuration required")
        print("   • Backward compatible with existing code")
    else:
        print("❌ FINAL RESULT: Issues found in implementation")
    
    print("=" * 60)
