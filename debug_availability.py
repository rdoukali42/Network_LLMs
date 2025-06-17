#!/usr/bin/env python3
"""
Debug script to check employee availability status.
"""

import sys
import os
sys.path.append('src')
sys.path.append('front')

from front.database import db_manager


def debug_employee_availability():
    """Debug employee availability status."""
    print("🔍 Debugging Employee Availability Status")
    print("=" * 50)
    
    # Get all employees
    all_employees = db_manager.get_all_employees()
    print(f"📊 Total employees: {len(all_employees)}")
    
    for emp in all_employees:
        print(f"\n👤 {emp['full_name']} (@{emp['username']})")
        print(f"   Role: {emp['role_in_company']}")
        print(f"   Status: {emp.get('availability_status', 'NOT SET')}")
        print(f"   Active: {emp.get('is_active', 'NOT SET')}")
    
    # Check availability statuses
    print(f"\n📋 Employee Status Summary:")
    statuses = {}
    for emp in all_employees:
        status = emp.get('availability_status', 'Offline')
        statuses[status] = statuses.get(status, 0) + 1
    
    for status, count in statuses.items():
        print(f"   {status}: {count} employees")


if __name__ == "__main__":
    debug_employee_availability()
