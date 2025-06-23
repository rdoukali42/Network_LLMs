#!/usr/bin/env python3
"""
Test VocalResponse parsing to verify debug output.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from agents.vocal_assistant import VocalResponse

def test_vocal_response_debug():
    """Test VocalResponse parsing with debug output."""
    print("=" * 60)
    print("🔍 TESTING VocalResponse Debug Output")
    print("=" * 60)
    
    # Test case 1: Redirect request
    print("\n📋 TEST 1: Redirect Request")
    print("-" * 40)
    
    conversation_data = {
        "response": """
REDIRECT_REQUEST: YES
USERNAME_TO_REDIRECT: alice
ROLE_OF_THE_REDIRECT_TO: Database Administrator
RESPONSIBILITIES: Database management, SQL optimization

I think Alice would be better suited to help you with this database optimization issue.
She has extensive experience with SQL performance tuning and database architecture.
"""
    }
    
    vocal_response = VocalResponse(conversation_data)
    
    print(f"✅ Redirect requested: {vocal_response.redirect_requested}")
    print(f"✅ Redirect info: {vocal_response.redirect_employee_info}")
    
    # Test case 2: No redirect
    print("\n📋 TEST 2: No Redirect")
    print("-" * 40)
    
    conversation_data2 = {
        "response": """
Here's the solution to your issue:

1. First, update your database configuration
2. Run the optimization script
3. Monitor the performance metrics

This should resolve your database performance problem.
"""
    }
    
    vocal_response2 = VocalResponse(conversation_data2)
    
    print(f"✅ Redirect requested: {vocal_response2.redirect_requested}")
    print(f"✅ Conversation complete: {vocal_response2.conversation_complete}")
    print(f"✅ Solution length: {len(vocal_response2.solution)}")
    
    print("\n" + "=" * 60)
    print("🔍 VocalResponse Debug Test Completed")
    print("=" * 60)

if __name__ == "__main__":
    test_vocal_response_debug()
