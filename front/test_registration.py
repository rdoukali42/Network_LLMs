#!/usr/bin/env python3
"""
Test the employee registration form functionality.
"""

import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "front"))

from database import db_manager

def test_registration_functionality():
    """Test the registration and database integration."""
    print("🧪 Testing Employee Registration System")
    print("=" * 50)
    
    # Test data for a new employee
    test_employee = {
        "username": "alice_johnson",
        "full_name": "Alice Johnson",
        "role_in_company": "UI/UX Designer",
        "job_description": "Design user interfaces and experiences for web and mobile applications. Conduct user research and create wireframes, prototypes, and visual designs.",
        "expertise": "Figma, Adobe Creative Suite, User Research, Prototyping, Interaction Design, HTML/CSS",
        "responsibilities": "Create design mockups, conduct user testing, collaborate with development team, maintain design system"
    }
    
    print("📝 Testing employee registration...")
    success, message = db_manager.create_employee(**test_employee)
    
    if success:
        print(f"✅ Registration successful: {message}")
        
        # Verify the employee was created
        employee = db_manager.get_employee_by_username(test_employee["username"])
        if employee:
            print(f"✅ Employee verified in database:")
            print(f"   Name: {employee['full_name']}")
            print(f"   Role: {employee['role_in_company']}")
            print(f"   Expertise: {employee['expertise'][:50]}...")
        else:
            print("❌ Employee not found after creation")
    else:
        print(f"⚠️ Registration result: {message}")
    
    # Test validation scenarios
    print("\n🔍 Testing validation scenarios...")
    
    # Test duplicate username
    duplicate_success, duplicate_message = db_manager.create_employee(
        username=test_employee["username"],
        full_name="Another Person",
        role_in_company="Developer",
        job_description="Test",
        expertise="Test",
        responsibilities="Test"
    )
    
    if not duplicate_success:
        print(f"✅ Duplicate username correctly rejected: {duplicate_message}")
    else:
        print(f"❌ Duplicate username was incorrectly accepted")
    
    # Show final statistics
    stats = db_manager.get_employee_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   Total active employees: {stats['total_active']}")
    print(f"   Database location: {stats['database_path']}")
    
    if stats['role_distribution']:
        print(f"   Role distribution:")
        for role, count in stats['role_distribution'].items():
            print(f"     - {role}: {count}")
    
    print("\n✅ Registration system test completed!")
    print("\n📋 To use the registration form:")
    print("1. Run: streamlit run app.py")
    print("2. Click 'Register as Employee' on login page")
    print("3. Fill out the registration form")
    print("4. Use registered username to login")

if __name__ == "__main__":
    test_registration_functionality()
