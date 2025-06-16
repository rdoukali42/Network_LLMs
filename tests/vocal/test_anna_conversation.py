#!/usr/bin/env python3
"""
Test script to verify Anna's conversation flow improvements
"""
import sys
import os
sys.path.append('/Users/level3/Desktop/Network/src')
sys.path.append('/Users/level3/Desktop/Network/front')

from vocal_components import GeminiChat

def test_anna_conversation():
    """Test Anna's conversation awareness and natural flow."""
    
    # Initialize Anna
    chat = GeminiChat()
    
    # Mock ticket and employee data
    ticket_data = {
        'user': 'John Smith',
        'description': 'Email client not syncing properly with Exchange server',
        'priority': 'High',
        'subject': 'Email Sync Issue'
    }
    
    employee_data = {
        'full_name': 'Sarah Johnson',
        'role_in_company': 'IT Support Specialist',
        'expertise': 'Email Systems and Exchange Server'
    }
    
    # Test 1: Initial conversation (should introduce herself)
    print("=== TEST 1: Initial Introduction ===")
    response1 = chat.chat(
        message="Hello?",
        ticket_data=ticket_data,
        employee_data=employee_data,
        is_employee=True,
        conversation_history=[]
    )
    print(f"Anna: {response1}")
    
    # Build conversation history
    conversation_history = [
        ("Employee", "Hello?"),
        ("Anna", response1)
    ]
    
    # Test 2: Employee provides some input (Anna should acknowledge it)
    print("\n=== TEST 2: Employee Response - Anna Should Acknowledge ===")
    response2 = chat.chat(
        message="Oh, email sync issues. I've seen this before. Usually it's a problem with the authentication settings.",
        ticket_data=ticket_data,
        employee_data=employee_data,
        is_employee=True,
        conversation_history=conversation_history
    )
    print(f"Anna: {response2}")
    
    # Update conversation history
    conversation_history.extend([
        ("Employee", "Oh, email sync issues. I've seen this before. Usually it's a problem with the authentication settings."),
        ("Anna", response2)
    ])
    
    # Test 3: Employee gives more technical details (Anna should ask follow-up)
    print("\n=== TEST 3: Technical Details - Anna Should Ask Follow-up ===")
    response3 = chat.chat(
        message="Yes, they need to check their OAuth settings and maybe update the server configuration.",
        ticket_data=ticket_data,
        employee_data=employee_data,
        is_employee=True,
        conversation_history=conversation_history
    )
    print(f"Anna: {response3}")
    
    # Test 4: Check if Anna maintains friendly, conversational tone
    conversation_history.extend([
        ("Employee", "Yes, they need to check their OAuth settings and maybe update the server configuration."),
        ("Anna", response3)
    ])
    
    print("\n=== TEST 4: Detailed Solution - Anna Should Be Encouraging ===")
    response4 = chat.chat(
        message="First, they should go to Account Settings, then Server Settings, and update the authentication method to OAuth 2.0. Then restart the email client.",
        ticket_data=ticket_data,
        employee_data=employee_data,
        is_employee=True,
        conversation_history=conversation_history
    )
    print(f"Anna: {response4}")
    
    print("\n=== CONVERSATION FLOW TEST COMPLETE ===")
    print("Check if Anna:")
    print("1. ✓ Introduced herself naturally in first response")
    print("2. ✓ Acknowledged employee input in subsequent responses")
    print("3. ✓ Asked follow-up questions based on employee expertise")
    print("4. ✓ Used friendly, encouraging language")
    print("5. ✓ Built on the conversation instead of restarting")

if __name__ == "__main__":
    test_anna_conversation()
