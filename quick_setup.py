#!/usr/bin/env python3
import sys
import os
sys.path.append('front')
from database import db_manager

# Set employees as available for testing
test_employees = [
    ('alex01', 'Available'),
    ('melanie', 'Available'), 
    ('mounir', 'Available'),
    ('yacoub', 'Busy')
]

for username, status in test_employees:
    success = db_manager.update_employee_status(username, status)
    print(f"✅ Set {username} to {status}" if success else f"❌ Failed to update {username}")

print("\nDone!")
