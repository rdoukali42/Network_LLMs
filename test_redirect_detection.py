#!/usr/bin/env python3
"""
Test script to verify enhanced redirect detection functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.vocal_assistant import VocalAssistantAgent
from src.integrations.llm_client import LLMClient
from src.config.config_loader import ConfigLoader


def test_redirect_detection():
    """Test the enhanced redirect detection methods."""
    print("🧪 Testing Enhanced Redirect Detection")
    print("=" * 50)
    
    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    
    # Initialize LLM client
    llm_client = LLMClient(config)
    
    # Initialize vocal assistant
    vocal_assistant = VocalAssistantAgent(config)
    
    # Test cases
    test_cases = [
        {
            "name": "Explicit redirect request",
            "conversation": "Hi, I need help with payroll. Can you please redirect me to Sarah from HR?",
            "expected": True
        },
        {
            "name": "Transfer request",
            "conversation": "This is a technical issue. Please transfer me to John in IT.",
            "expected": True
        },
        {
            "name": "Forward request", 
            "conversation": "Forward this request to the manager, please.",
            "expected": True
        },
        {
            "name": "No redirect",
            "conversation": "Thank you for helping me with my question. That resolved everything.",
            "expected": False
        },
        {
            "name": "Structured headers (pre-processed)",
            "conversation": """REDIRECT_REQUESTED: True
USERNAME_TO_REDIRECT: sarah
ROLE_OF_THE_REDIRECT_TO: HR Specialist
RESPONSIBILITIES: Human Resources matters

ORIGINAL_CONVERSATION:
User asked to speak with Sarah from HR about benefits.""",
            "expected": True
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"📝 Input: {test_case['conversation'][:100]}...")
        
        try:
            result = vocal_assistant._analyze_conversation_for_redirect(test_case['conversation'])
            
            detected = result.get('redirect_requested', False)
            method = result.get('detection_method', 'unknown')
            employee_info = result.get('redirect_employee_info', {})
            
            print(f"🔍 Result: {detected}")
            print(f"🔍 Method: {method}")
            print(f"🔍 Employee Info: {employee_info}")
            
            if detected == test_case['expected']:
                print(f"✅ PASS - Expected: {test_case['expected']}, Got: {detected}")
            else:
                print(f"❌ FAIL - Expected: {test_case['expected']}, Got: {detected}")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            print(f"📊 Traceback: {traceback.format_exc()}")
    
    print(f"\n🏁 Testing complete!")


if __name__ == "__main__":
    test_redirect_detection()
