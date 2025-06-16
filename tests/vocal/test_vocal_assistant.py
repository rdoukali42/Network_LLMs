#!/usr/bin/env python3
"""
Test script to verify vocal_assistant.py Anna implementation
"""
import sys
import os
sys.path.append('/Users/level3/Desktop/Network/src')
sys.path.append('/Users/level3/Desktop/Network/src/agents')

from vocal_assistant import GeminiChat

def test_vocal_assistant_anna():
    """Test Anna's implementation in vocal_assistant.py."""
    
    # Initialize Anna from vocal_assistant
    chat = GeminiChat()
    
    # Mock data
    ticket_data = {
        'user': 'Mike Thompson',
        'description': 'Printer not responding to print jobs',
        'priority': 'Medium',
        'subject': 'Printer Connectivity Issue'
    }
    
    employee_data = {
        'full_name': 'Alex Rivera',
        'role_in_company': 'Hardware Technician',
        'expertise': 'Printers and Network Hardware'
    }
    
    print("=== Testing vocal_assistant.py Implementation ===")
    
    # Test initial conversation
    response1 = chat.chat(
        message="Hi, this is Alex.",
        ticket_data=ticket_data,
        employee_data=employee_data,
        is_employee=True,
        conversation_history=[]
    )
    print(f"Anna: {response1}")
    
    # Test follow-up
    conversation_history = [
        ("Employee", "Hi, this is Alex."),
        ("Anna", response1)
    ]
    
    response2 = chat.chat(
        message="Oh printer issues! I usually start by checking the network connection and driver status.",
        ticket_data=ticket_data,
        employee_data=employee_data,
        is_employee=True,
        conversation_history=conversation_history
    )
    print(f"\nAnna: {response2}")
    
    print("\n=== vocal_assistant.py test complete ===")

if __name__ == "__main__":
    test_vocal_assistant_anna()
