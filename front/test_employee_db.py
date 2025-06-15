#!/usr/bin/env python3
"""
Test the employee database functionality.
"""

import sys
from pathlib import Path

# Add front directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import db_manager

def test_employee_database():
    """Test the employee database operations."""
    print("🧪 Testing Employee Database")
    print("=" * 50)
    
    try:
        # Test database connection
        stats = db_manager.get_employee_stats()
        print(f"✅ Database connected: {stats['database_path']}")
        print(f"📊 Current employees: {stats['total_active']}")
        
        # Test creating an employee
        print("\n📝 Testing employee creation...")
        success, message = db_manager.create_employee(
            username="john_doe",
            full_name="John Doe",
            role_in_company="Software Engineer",
            job_description="Develops and maintains web applications using Python and JavaScript.",
            expertise="Python, JavaScript, React, Django, API Development",
            responsibilities="Code development, code reviews, testing, deployment, technical documentation"
        )
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"⚠️ {message}")
        
        # Test getting employee
        print("\n🔍 Testing employee retrieval...")
        employee = db_manager.get_employee_by_username("john_doe")
        if employee:
            print(f"✅ Found employee: {employee['full_name']}")
            print(f"   Role: {employee['role_in_company']}")
            print(f"   Expertise: {employee['expertise'][:50]}...")
        else:
            print("❌ Employee not found")
        
        # Test creating another employee
        print("\n📝 Creating another test employee...")
        success, message = db_manager.create_employee(
            username="jane_smith",
            full_name="Jane Smith",
            role_in_company="Data Analyst",
            job_description="Analyzes business data to provide insights and recommendations.",
            expertise="SQL, Python, Power BI, Excel, Statistics, Machine Learning",
            responsibilities="Data analysis, reporting, dashboard creation, stakeholder communication"
        )
        
        if success:
            print(f"✅ {message}")
        
        # Test getting all employees
        print("\n👥 Testing employee listing...")
        employees = db_manager.get_all_employees()
        print(f"✅ Found {len(employees)} employees:")
        for emp in employees:
            print(f"   - {emp['full_name']} ({emp['username']}) - {emp['role_in_company']}")
        
        # Test search functionality
        print("\n🔍 Testing search functionality...")
        search_results = db_manager.search_employees("Python")
        print(f"✅ Found {len(search_results)} employees with 'Python' expertise:")
        for emp in search_results:
            print(f"   - {emp['full_name']} - {emp['role_in_company']}")
        
        # Test role-based search
        print("\n🔍 Testing role-based search...")
        engineers = db_manager.get_employees_by_role("Engineer")
        print(f"✅ Found {len(engineers)} engineers:")
        for emp in engineers:
            print(f"   - {emp['full_name']} - {emp['role_in_company']}")
        
        # Final stats
        print("\n📊 Final database statistics:")
        stats = db_manager.get_employee_stats()
        print(f"   Total active employees: {stats['total_active']}")
        print(f"   Role distribution: {stats['role_distribution']}")
        
        print("\n🎉 Database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_employee_database()
    sys.exit(0 if success else 1)
