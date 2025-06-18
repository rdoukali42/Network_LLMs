#!/usr/bin/env python3
"""
Simple test to validate HR Agent Pydantic refactoring.
"""

import sys
import os
import sys
import traceback

# Add the src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

try:
    # Test imports
    from models.hr_models import HRTicketRequest, HREmployeeMatch, HRTicketResponse
    from models.common_models import StatusEnum
    
    print("✅ Pydantic models imported successfully")
    
    # Test basic model creation
    ticket = HRTicketRequest(
        ticket_id="test-123",
        title="Test ticket",
        description="This is a test description for ML help",
        priority="medium"
    )
    
    print(f"✅ Created ticket: {ticket.ticket_id}")
    print(f"   Priority: {ticket.priority}")
    print(f"   Skills required: {ticket.skills_required}")
    
    # Test employee match
    employee = HREmployeeMatch(
        employee_id="test_emp",
        name="Test Employee",
        email="test@company.com",
        department="Engineering",
        skills=["python", "machine learning"],
        availability_status="Available",
        overall_score=0.75,
        skill_match_score=0.8,
        availability_score=1.0,
        workload_score=0.6,
        department_match_score=0.7,
        matching_skills=["python"],
        missing_skills=["tensorflow"],
        match_reasoning="Good match for Python work"
    )
    
    print(f"✅ Created employee match: {employee.name}")
    print(f"   Overall score: {employee.overall_score}")
    
    # Test response
    response = HRTicketResponse(
        agent_name="HRAgent",
        ticket_id=ticket.ticket_id,
        matched_employees=[employee],
        total_matches=1,
        recommended_assignment=employee.employee_id
    )
    
    print(f"✅ Created response for ticket: {response.ticket_id}")
    print(f"   Status: {response.status}")
    print(f"   Total matches: {response.total_matches}")
    
    # Test serialization
    response_data = response.model_dump()
    print(f"✅ Serialization successful, has {len(response_data)} fields")
    
    print("\n🎉 All basic Pydantic tests passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    traceback.print_exc()
    sys.exit(1)
