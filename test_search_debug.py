#!/usr/bin/env python3
"""
Test EmployeeSearchTool to verify debug output.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from tools.employee_search_tool import EmployeeSearchTool

def test_employee_search_debug():
    """Test EmployeeSearchTool with debug output."""
    print("=" * 70)
    print("🔍 TESTING EmployeeSearchTool Debug Output")
    print("=" * 70)
    
    # Initialize the tool
    search_tool = EmployeeSearchTool()
    
    # Test case 1: Search by username
    print("\n📋 TEST 1: Search by Username")
    print("-" * 50)
    
    redirect_info = {
        "username": "alice",
        "role": "Database Administrator", 
        "responsibilities": "database management"
    }
    
    results = search_tool.search_employees_for_redirect(redirect_info)
    
    print(f"\n✅ Found {len(results)} matches")
    for i, result in enumerate(results[:3]):  # Show top 3
        print(f"   {i+1}. {result.get('full_name', 'Unknown')} (Score: {result.get('redirect_score', 0)})")
    
    # Test case 2: Search by role only
    print("\n📋 TEST 2: Search by Role")
    print("-" * 50)
    
    redirect_info2 = {
        "role": "DevOps Engineer",
        "responsibilities": "CI/CD, Docker"
    }
    
    results2 = search_tool.search_employees_for_redirect(redirect_info2)
    
    print(f"\n✅ Found {len(results2)} matches")
    for i, result in enumerate(results2[:3]):  # Show top 3
        print(f"   {i+1}. {result.get('full_name', 'Unknown')} (Score: {result.get('redirect_score', 0)})")
    
    print("\n" + "=" * 70)
    print("🔍 EmployeeSearchTool Debug Test Completed")
    print("=" * 70)

if __name__ == "__main__":
    test_employee_search_debug()
