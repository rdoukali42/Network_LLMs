#!/usr/bin/env python3
"""
Test the updated assignment functionality with HR response parsing.
"""

import sys
sys.path.append('front')

from tickets import TicketManager
from database import db_manager

def test_updated_assignment():
    """Test the updated assignment functionality."""
    print("🧪 Testing Updated Assignment with HR Response Parsing")
    print("=" * 60)
    
    ticket_manager = TicketManager()
    
    # Simulate HR response like what we saw
    hr_response = '''I couldn't find a direct answer in our knowledge base for your request, but I can help connect you with the right expert.

👤 Alex Johnson (@alex01) 🏢 Role: Machine Learning Engineer 💼 Expertise: Python, Deep Learning, NLP, PyTorch, MLOps 📋 Responsibilities: Develop and optimize ML models

Deploy models to production

Maintain ML pipelines

Collaborate on data strategy 🟢 Status: Available

This employee has the expertise to help with your request.

Please reach out to them directly - they'll be able to provide specialized assistance with your specific issue.'''
    
    # Create test ticket
    ticket_id = ticket_manager.create_ticket(
        user="test_user",
        category="Technical Issue",
        priority="Medium", 
        subject="ML Model Deployment",
        description="I need help deploying machine learning models"
    )
    print(f"1. Created ticket: {ticket_id}")
    
    # Simulate the parsing logic from process_ticket_with_ai
    print("2. Testing HR response parsing...")
    
    if "👤" in hr_response and "(@" in hr_response and "🏢 Role:" in hr_response:
        username_match = hr_response.split("(@")[1].split(")")[0] if "(@" in hr_response else None
        print(f"   Detected HR referral")
        print(f"   Extracted username: {username_match}")
        
        if username_match:
            # Verify employee exists
            employee = db_manager.get_employee_by_username(username_match)
            if employee:
                print(f"   Employee found: {employee['full_name']}")
                
                # Assign ticket
                ticket_manager.assign_ticket(ticket_id, username_match)
                print(f"   ✅ Ticket assigned to {employee['full_name']}")
                
                # Create assignment message
                assignment_response = f"Your ticket has been assigned to {employee['full_name']} ({employee['role_in_company']}). They will work on your request and provide a solution soon."
                ticket_manager.update_ticket_response(ticket_id, assignment_response)
                print(f"   ✅ Assignment message created")
                
                # Verify assignment
                ticket = ticket_manager.get_ticket_by_id(ticket_id)
                print(f"3. Verification:")
                print(f"   Status: {ticket['status']}")
                print(f"   Assigned to: {ticket['assigned_to']}")
                print(f"   Assignment status: {ticket['assignment_status']}")
                print(f"   Response: {ticket['response'][:50]}...")
                
            else:
                print(f"   ❌ Employee not found: {username_match}")
        else:
            print(f"   ❌ No username extracted")
    else:
        print("   Not an HR referral response")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_updated_assignment()
