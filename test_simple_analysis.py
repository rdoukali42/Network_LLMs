#!/usr/bin/env python3
"""
Simple test to see what conversation analysis produces.
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_analysis():
    """Test conversation analysis directly."""
    
    try:
        from agents.vocal_assistant import VocalResponse
        
        # Test with a conversation that clearly contains redirect
        test_conversation = """You: Can you redirect this to Mike then?
Employee: Absolutely! I'll redirect this conversation to Mike right away. He'll be able to help you with the PostgreSQL connection timeout issue."""
        
        print(f"📝 Test: {test_conversation}")
        
        # Test the VocalResponse parser directly
        vocal_response = VocalResponse({"response": test_conversation})
        print(f"Redirect requested: {vocal_response.redirect_requested}")
        print(f"Redirect info: {vocal_response.redirect_employee_info}")
        
        # Test with simulated AI output format
        simulated_ai_output = """REDIRECT_REQUESTED: True
USERNAME_TO_REDIRECT: Mike
ROLE_OF_THE_REDIRECT_TO: Database Specialist
RESPONSIBILITIES: PostgreSQL performance issues"""
        
        print(f"\n📝 Simulated AI Output: {simulated_ai_output}")
        vocal_response2 = VocalResponse({"response": simulated_ai_output})
        print(f"Redirect requested: {vocal_response2.redirect_requested}")
        print(f"Redirect info: {vocal_response2.redirect_employee_info}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis()
