#!/usr/bin/env python3
"""
Ticket Schema Enhancement Script
Adds redirect-related fields to existing tickets in tickets.json
"""

import json
import os
from datetime import datetime

def enhance_ticket_schema():
    """Add redirect fields to existing tickets."""
    
    print("📋 Enhancing ticket schema with redirect fields...")
    
    tickets_file = "front/tickets.json"
    
    # Load existing tickets
    try:
        with open(tickets_file, 'r') as f:
            tickets = json.load(f)
        print(f"✅ Loaded {len(tickets)} existing tickets")
    except Exception as e:
        print(f"❌ Error loading tickets: {e}")
        return
    
    # Enhanced schema fields for redirect functionality
    enhanced_fields = {
        "redirect_count": 0,
        "max_redirects": 3,
        "redirect_history": [],
        "redirect_reason": None,
        "previous_assignee": None,
        "redirect_timestamp": None,
        "call_status": "not_initiated",  # not_initiated, initiated, in_progress, ended, completed
        "conversation_data": None,
        "redirect_requested": False
    }
    
    # Add new fields to each ticket (if they don't exist)
    updated_count = 0
    for ticket in tickets:
        ticket_updated = False
        for field, default_value in enhanced_fields.items():
            if field not in ticket:
                ticket[field] = default_value
                ticket_updated = True
        
        if ticket_updated:
            updated_count += 1
    
    # Save enhanced tickets
    try:
        with open(tickets_file, 'w') as f:
            json.dump(tickets, f, indent=2)
        
        print(f"✅ Enhanced {updated_count} tickets with redirect fields")
        print(f"✅ Schema enhancement completed successfully")
        
        # Show sample enhanced ticket structure
        if tickets:
            print(f"\n📋 Sample Enhanced Ticket Fields:")
            sample_ticket = tickets[0]
            for field in enhanced_fields.keys():
                print(f"   • {field}: {sample_ticket.get(field, 'Not found')}")
            
    except Exception as e:
        print(f"❌ Error saving enhanced tickets: {e}")

if __name__ == "__main__":
    enhance_ticket_schema()
