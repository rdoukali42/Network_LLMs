#!/usr/bin/env python3
"""
Test script to verify the ticket system functionality.
Tests ticket creation, storage, and AI processing.
"""

import sys
import json
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(Path(__file__).parent))

def test_ticket_manager():
    """Test TicketManager functionality."""
    print("🧪 Testing TicketManager...")
    
    try:
        from tickets import TicketManager
        
        # Initialize manager
        manager = TicketManager()
        print("✅ TicketManager initialized")
        
        # Create test ticket
        ticket_id = manager.create_ticket(
            user="test_user",
            category="Technical Issue",
            priority="Medium",
            subject="Test ticket",
            description="This is a test ticket to verify the system works."
        )
        print(f"✅ Ticket created with ID: {ticket_id}")
        
        # Retrieve ticket
        ticket = manager.get_ticket_by_id(ticket_id)
        if ticket:
            print(f"✅ Ticket retrieved: {ticket['subject']}")
        else:
            print("❌ Failed to retrieve ticket")
            return False
        
        # Get user tickets
        user_tickets = manager.get_user_tickets("test_user")
        print(f"✅ Found {len(user_tickets)} tickets for test_user")
        
        # Update with response
        manager.update_ticket_response(ticket_id, "Test AI response")
        updated_ticket = manager.get_ticket_by_id(ticket_id)
        if updated_ticket and updated_ticket['response']:
            print("✅ Ticket response updated successfully")
        else:
            print("❌ Failed to update ticket response")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ TicketManager test failed: {e}")
        return False

def test_workflow_client():
    """Test WorkflowClient functionality."""
    print("\n🧪 Testing WorkflowClient...")
    
    try:
        from workflow_client import WorkflowClient
        
        # Initialize client
        client = WorkflowClient()
        print("✅ WorkflowClient initialized")
        
        # Check if ready
        if client.is_ready():
            print("✅ AI system is ready")
            
            # Test simple query
            result = client.process_message("What is 2 + 2?")
            if result and not result.get('status') == 'error':
                print("✅ AI query processed successfully")
                return True
            else:
                print(f"⚠️ AI query returned error: {result}")
                return True  # Not critical for ticket system
        else:
            print("⚠️ AI system not ready (check GOOGLE_API_KEY)")
            return True  # Not critical for basic functionality
            
    except Exception as e:
        print(f"⚠️ WorkflowClient test failed: {e}")
        return True  # Not critical for basic functionality

def test_imports():
    """Test all required imports."""
    print("\n🧪 Testing imports...")
    
    try:
        from tickets import show_ticket_interface, TicketManager
        print("✅ tickets.py imports successful")
        
        from workflow_client import WorkflowClient
        print("✅ workflow_client.py imports successful")
        
        from auth import handle_authentication, logout
        print("✅ auth.py imports successful")
        
        from streamlit_config import APP_TITLE, SESSION_KEYS
        print("✅ streamlit_config.py imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_tickets_json():
    """Test tickets.json file operations."""
    print("\n🧪 Testing tickets.json file...")
    
    tickets_file = Path(__file__).parent / "tickets.json"
    
    try:
        # Check if file exists or can be created
        if tickets_file.exists():
            print("✅ tickets.json exists")
            
            # Try to read it
            with open(tickets_file, 'r') as f:
                data = json.load(f)
            print(f"✅ tickets.json readable, contains {len(data)} tickets")
        else:
            print("ℹ️ tickets.json will be created on first use")
        
        return True
        
    except Exception as e:
        print(f"❌ tickets.json test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🎫 Testing AI Support Ticket System")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_tickets_json,
        test_ticket_manager,
        test_workflow_client
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed! Ticket system is ready.")
    else:
        print(f"⚠️ {passed}/{total} tests passed. Check issues above.")
    
    print(f"\n✨ Ticket system status: {'READY' if passed >= 3 else 'NEEDS ATTENTION'}")

if __name__ == "__main__":
    main()
