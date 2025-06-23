#!/usr/bin/env python3
"""
Debug the VocalResponse parsing to see why redirect info is empty
"""

import os
import sys

# Add src to path for imports
sys.path.append('src')

def debug_vocal_response_parsing():
    """Debug why redirect info is empty"""
    print("🔍 DEBUGGING VOCAL RESPONSE PARSING")
    print("=" * 50)
    
    try:
        from agents.vocal_assistant import VocalResponse
        
        # Test different conversation formats
        test_cases = [
            {
                "name": "Simple redirect request",
                "text": "Employee: I think this would be better handled by our DevOps team. REDIRECT_REQUESTED: True"
            },
            {
                "name": "Structured redirect request",
                "text": """REDIRECT_REQUEST: YES
USERNAME_TO_REDIRECT: omar
ROLE_OF_THE_REDIRECT_TO: DevOps Engineer
RESPONSIBILITIES: infrastructure, deployment, monitoring

I think this database issue would be better handled by our DevOps team."""
            },
            {
                "name": "Mixed format",
                "text": """Employee: I think this database issue would be better handled by our DevOps team. 
REDIRECT_REQUESTED: True
They have more experience with infrastructure optimization."""
            },
            {
                "name": "No redirect info",
                "text": "Employee: Here's the solution to your database problem. The issue is with indexing."
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. 🧪 Testing: {test_case['name']}")
            print(f"   Text: {test_case['text'][:100]}...")
            
            conversation_data = {"response": test_case["text"]}
            vocal_response = VocalResponse(conversation_data)
            
            print(f"   ✅ Redirect requested: {vocal_response.redirect_requested}")
            print(f"   ✅ Redirect info: {vocal_response.redirect_employee_info}")
            print(f"   ✅ Conversation complete: {vocal_response.conversation_complete}")
            print(f"   ✅ Solution: {vocal_response.solution[:50]}..." if vocal_response.solution else "   ✅ Solution: None")
            
            if vocal_response.redirect_requested and not vocal_response.redirect_employee_info:
                print(f"   ⚠️ ISSUE: Redirect detected but no employee info extracted!")
            elif vocal_response.redirect_requested and vocal_response.redirect_employee_info:
                print(f"   ✅ SUCCESS: Redirect detected with employee info!")
            
        # Test the _extract_solution_text method
        print(f"\n🔍 Testing solution extraction...")
        test_response = VocalResponse({"response": "Here's the solution to your problem. It should work fine."})
        print(f"   Solution extracted: '{test_response.solution}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Parsing debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_vocal_response_parsing()
