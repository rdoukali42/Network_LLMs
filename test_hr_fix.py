#!/usr/bin/env python3
"""
Quick test to verify the HR_Agent fix is working correctly.
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

def test_different_scenarios():
    """Test different user scenarios to verify assignment logic."""
    
    test_cases = [
        {
            "user": "mounir",
            "query": "which model should I use for a classification problem?",
            "expected_domain": "ML",
            "expected_role": "Machine Learning Engineer"
        },
        {
            "user": "alex01", 
            "query": "I need help with UI design and user experience",
            "expected_domain": "UI/UX",
            "expected_role": "UI/UX Designer"
        },
        {
            "user": "melanie",
            "query": "I need help with deep learning and neural networks",
            "expected_domain": "ML",
            "expected_role": "Machine Learning Engineer"
        }
    ]
    
    print("🧪 TESTING IMPROVED HR_AGENT ASSIGNMENT")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test['expected_domain']} Question")
        print(f"   User: {test['user']}")
        print(f"   Query: {test['query']}")
        print(f"   Expected: {test['expected_role']}")
        
        # Mock streamlit session
        sys.modules['streamlit'] = MockStreamlit(test['user'])
        
        try:
            from src.agents.base_agent import HRAgent
            from src.tools.availability_tool import AvailabilityTool
            
            availability_tool = AvailabilityTool()
            hr_agent = HRAgent(availability_tool=availability_tool)
            
            result = hr_agent.run({"query": test['query']})
            
            if result.get("status") == "success" and result.get("action") == "assign":
                assigned_employee = result.get("employee_data", {})
                assigned_name = assigned_employee.get("full_name")
                assigned_role = assigned_employee.get("role_in_company") 
                assigned_username = assigned_employee.get("username")
                
                print(f"   ✅ Assigned: {assigned_name} (@{assigned_username})")
                print(f"   📋 Role: {assigned_role}")
                
                # Check if assignment makes sense
                if test['expected_domain'] == "ML" and "machine learning" in assigned_role.lower():
                    print(f"   🎯 PERFECT: ML question correctly assigned to ML expert!")
                elif test['expected_domain'] == "UI/UX" and ("ui" in assigned_role.lower() or "ux" in assigned_role.lower()):
                    print(f"   🎯 PERFECT: UI/UX question correctly assigned to UI/UX expert!")
                else:
                    print(f"   ⚠️  Assignment may not be optimal")
                
                # Verify no self-assignment
                if assigned_username == test['user']:
                    print(f"   ❌ ERROR: Self-assignment detected!")
                else:
                    print(f"   ✅ No self-assignment (good)")
                    
            else:
                print(f"   ❌ No assignment: {result.get('result', 'Unknown')}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    test_different_scenarios()
    
    print("\n" + "=" * 50)
    print("🎉 HR_AGENT ASSIGNMENT FIX VERIFICATION COMPLETE")
    print("=" * 50)
