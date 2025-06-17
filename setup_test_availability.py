#!/usr/bin/env python3
"""
Setup script to set some employees as available for testing.
"""

import sys
import os
sys.path.append('src')
sys.path.append('front')

from front.database import db_manager


def setup_test_availability():
    """Set some employees as available for testing."""
    print("🔧 Setting up test employee availability")
    print("=" * 45)
    
    # Set specific employees as available
    test_employees = [
        ('alex01', 'Available'),
        ('melanie', 'Available'), 
        ('mounir', 'Available'),
        ('yacoub', 'Busy'),
        ('alice_johnson', 'Available')
    ]
    
    for username, status in test_employees:
        success = db_manager.update_employee_status(username, status)
        if success:
            print(f"✅ Set {username} to {status}")
        else:
            print(f"❌ Failed to update {username}")
    
    print("\n📊 Updated Employee Status:")
    all_employees = db_manager.get_all_employees()
    for emp in all_employees:
        status = emp.get('availability_status', 'Offline')
        print(f"   {emp['username']}: {status}")


if __name__ == "__main__":
    setup_test_availability()
