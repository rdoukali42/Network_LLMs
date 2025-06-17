#!/usr/bin/env python3
"""
Test script to verify the simple self-assignment prevention fix.
Tests that AvailabilityTool automatically excludes current user from employee lists.
"""

import sys
import os
sys.path.append('src')
sys.path.append('front')

# Mock streamlit session state
class MockSessionState:
    def __init__(self):
        self.username = "mounir"

class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState()

# Mock streamlit
sys.modules['streamlit'] = MockStreamlit()

from src.tools.availability_tool import AvailabilityTool
from front.database import db_manager


def test_automatic_user_filtering():
    """Test that AvailabilityTool automatically filters out current user."""
    print("🧪 Testing Automatic User Filtering in AvailabilityTool")
    print("=" * 60)
    
    try:
        # Get all employees first
        all_employees = db_manager.get_all_employees()
        print(f"📊 Total employees in database: {len(all_employees)}")
        
        # Find test user
        test_user = None
        for emp in all_employees:
            if emp['username'] == 'mounir':
                test_user = emp
                break
        
        if test_user:
            print(f"✅ Found test user: {test_user['full_name']} (username: {test_user['username']})")
        else:
            print("❌ Test user 'mounir' not found in database")
            return False
        
        # Test AvailabilityTool with mocked session state
        availability_tool = AvailabilityTool()
        
        # Get available employees (should automatically exclude 'mounir')
        available_employees = availability_tool.get_available_employees()
        
        # Check if mounir is excluded
        filtered_usernames = [emp['username'] for emp in 
                            available_employees['available'] + available_employees['busy']]
        
        print(f"📋 Available employees after filtering: {len(filtered_usernames)}")
        print(f"📋 Usernames in filtered list: {filtered_usernames}")
        
        if 'mounir' not in filtered_usernames:
            print("✅ SUCCESS: Current user 'mounir' is automatically excluded from employee list")
            print("✅ Self-assignment prevention working correctly!")
            return True
        else:
            print("❌ FAILURE: Current user 'mounir' is still in the employee list")
            print("❌ Self-assignment prevention not working")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_users():
    """Test filtering with different users."""
    print("\n🧪 Testing Different User Scenarios")
    print("=" * 40)
    
    # Test with different mock users
    test_users = ['alex01', 'melanie', 'mounir']
    
    for username in test_users:
        print(f"\n🔍 Testing with user: {username}")
        
        # Update mock session state
        import streamlit as st
        st.session_state.username = username
        
        availability_tool = AvailabilityTool()
        available_employees = availability_tool.get_available_employees()
        
        filtered_usernames = [emp['username'] for emp in 
                            available_employees['available'] + available_employees['busy']]
        
        if username not in filtered_usernames:
            print(f"  ✅ User '{username}' correctly excluded from list")
        else:
            print(f"  ❌ User '{username}' still in list - filtering failed")


def test_fallback_behavior():
    """Test fallback behavior when streamlit is not available."""
    print("\n🧪 Testing Fallback Behavior")
    print("=" * 30)
    
    # Temporarily remove streamlit mock
    original_st = sys.modules.get('streamlit')
    if 'streamlit' in sys.modules:
        del sys.modules['streamlit']
    
    try:
        from src.tools.availability_tool import AvailabilityTool
        availability_tool = AvailabilityTool()
        
        # Test with explicit exclude_username (fallback mode)
        available_employees = availability_tool.get_available_employees(exclude_username='mounir')
        filtered_usernames = [emp['username'] for emp in 
                            available_employees['available'] + available_employees['busy']]
        
        if 'mounir' not in filtered_usernames:
            print("✅ Fallback exclude_username parameter working correctly")
        else:
            print("❌ Fallback exclude_username parameter not working")
            
    except Exception as e:
        print(f"❌ Error during fallback test: {e}")
    finally:
        # Restore streamlit mock
        if original_st:
            sys.modules['streamlit'] = original_st


if __name__ == "__main__":
    print("🚀 Starting Simple Self-Assignment Prevention Tests")
    print("=" * 70)
    
    success = test_automatic_user_filtering()
    test_different_users()
    test_fallback_behavior()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 OVERALL RESULT: Simple self-assignment prevention is working!")
        print("✅ AvailabilityTool automatically filters current user from employee lists")
        print("✅ No complex context passing needed")
    else:
        print("❌ OVERALL RESULT: Issues found with self-assignment prevention")
    
    print("=" * 70)
