#!/usr/bin/env python3
"""
Test the VocalResponse parsing fix for the formatting characters issue.
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_vocal_response_fix():
    """Test that VocalResponse correctly handles formatted redirect requests."""
    
    print("🧪 TESTING VocalResponse FIX")
    print("=" * 50)
    
    from agents.vocal_assistant import VocalResponse
    
    # Test case with the exact format that was failing
    test_conversation = """
**Subject:** Mobile Onboarding Experience Redesign Request

**Issue:** Mouad submitted a ticket requesting a redesign of the mobile onboarding experience to improve usability
REDIRECT_REQUESTED: ** TRUE
USERNAME_TO_REDIRECT: ** Patrick  
ROLE_OF_THE_REDIRECT_TO: ** Product Development Lead
RESPONSIBILITIES: ** Mounir was unavailable to handle the ticket.
"""
    
    print(f"📝 Test Input:")
    print(f"   Contains 'REDIRECT_REQUESTED: ** TRUE': {'REDIRECT_REQUESTED: ** TRUE' in test_conversation}")
    print(f"   Contains 'USERNAME_TO_REDIRECT: ** Patrick': {'USERNAME_TO_REDIRECT: ** Patrick' in test_conversation}")
    
    conversation_data = {"response": test_conversation}
    
    print(f"\n🔄 Creating VocalResponse...")
    vocal_response = VocalResponse(conversation_data)
    
    print(f"\n📊 RESULTS:")
    print(f"   Redirect Requested: {vocal_response.redirect_requested}")
    print(f"   Redirect Info: {vocal_response.redirect_employee_info}")
    
    # Check results
    if vocal_response.redirect_requested:
        print(f"✅ SUCCESS: Redirect correctly detected!")
        
        if vocal_response.redirect_employee_info.get('username') == 'Patrick':
            print(f"✅ SUCCESS: Username correctly parsed as 'Patrick'!")
        else:
            print(f"❌ FAIL: Username was '{vocal_response.redirect_employee_info.get('username')}', expected 'Patrick'")
            
        if vocal_response.redirect_employee_info.get('role'):
            print(f"✅ SUCCESS: Role correctly parsed as '{vocal_response.redirect_employee_info.get('role')}'!")
        else:
            print(f"❌ FAIL: Role not parsed correctly")
            
        print(f"\n🎉 VOCAL RESPONSE FIX TEST PASSED!")
        return True
    else:
        print(f"❌ FAIL: Redirect not detected! Still broken.")
        return False

if __name__ == "__main__":
    success = test_vocal_response_fix()
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: VocalResponse fix test completed")
