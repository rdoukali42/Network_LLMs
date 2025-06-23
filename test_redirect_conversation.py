#!/usr/bin/env python3
"""
Test the redirect functionality by simulating a conversation where Patrick requests redirect
"""

import sys
sys.path.append('/Users/level3/Desktop/Network/src')

from agents.vocal_assistant import VocalAssistantAgent, VocalResponse
from config.config_loader import ConfigLoader

def test_redirect_conversation():
    """Test VocalAssistant with redirect scenario."""
    print("🧪 Testing VocalAssistant redirect conversation...")
    
    # Create VocalAssistant
    config = ConfigLoader().load_config("development")
    vocal_assistant = VocalAssistantAgent(config=config)
    
    # Mock ticket and employee data
    ticket_data = {
        "id": "test_ticket_001",
        "user": "tristan",
        "subject": "Advanced ML Model Deployment",
        "description": "I need help with advanced Python machine learning model deployment and scaling",
        "priority": "High"
    }
    
    employee_data = {
        "full_name": "Patrick Neumann",
        "username": "patrick",
        "role_in_company": "Developer",
        "expertise": "Python",
        "email": "patrick@company.com"
    }
    
    # Simulate a conversation where Patrick says he can't handle this and wants to redirect
    conversation_messages = [
        ("Anna", "Hi Patrick! I'm Anna, your AI assistant. I have a ticket here from Tristan about advanced Python machine learning model deployment and scaling. Can you help with this?"),
        ("Patrick", "Hi Anna! I looked at this ticket, but honestly, this is way beyond my expertise. I only know basic Python development. This requires someone with deep machine learning knowledge, specifically someone who knows about model deployment and scaling in production environments. I think you should redirect this to Lina - she's our Data Analyst and has much more experience with ML models."),
    ]
    
    # Simulate Anna's response to Patrick's redirect request
    user_message = conversation_messages[-1][1]  # Patrick's message about redirecting
    
    print(f"👤 Patrick: {user_message}")
    print("\n🤖 Anna's response:")
    
    # Get Anna's response using the chat method
    response = vocal_assistant.gemini.chat(
        user_message,
        ticket_data,
        employee_data,
        is_employee=True,
        conversation_history=conversation_messages
    )
    
    print(response)
    print("\n" + "="*50)
    
    # Test parsing the response
    print("\n🔍 Testing VocalResponse parsing...")
    conversation_data = {"response": response}
    vocal_response = VocalResponse(conversation_data)
    
    print(f"Redirect Requested: {vocal_response.redirect_requested}")
    if vocal_response.redirect_requested:
        print(f"Redirect Info: {vocal_response.redirect_employee_info}")
        print("✅ Redirect detected successfully!")
    else:
        print("❌ Redirect not detected")
    
    return vocal_response.redirect_requested

if __name__ == "__main__":
    try:
        success = test_redirect_conversation()
        if success:
            print("\n🎉 Redirect functionality test PASSED!")
            print("✅ VocalAssistant can detect and format redirect requests")
        else:
            print("\n❌ Redirect functionality test FAILED!")
            print("❌ VocalAssistant did not detect redirect request")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
