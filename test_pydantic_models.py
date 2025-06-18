#!/usr/bin/env python3
"""
Test script to validate the new Pydantic models for HR Agent.
"""

import sys
import os
sys.path.append('src')

from models.hr_models import HRTicketRequest, HREmployeeMatch, HRTicketResponse
from models.common_models import StatusEnum
from pydantic import ValidationError


def test_pydantic_models():
    """Test the new Pydantic models."""
    print("🧪 Testing HR Agent Pydantic Models")
    print("=" * 50)
    
    try:
        # Test HRTicketRequest
        print("Testing HRTicketRequest...")
        ticket_request = HRTicketRequest(
            ticket_id="test-001",
            title="Need help with machine learning model",
            description="I need assistance implementing a classification model using Python",
            priority="high",
            skills_required=["machine learning", "python", "classification"]
        )
        print(f"✅ HRTicketRequest created: {ticket_request.ticket_id}")
        print(f"   Priority: {ticket_request.priority}")
        print(f"   Skills: {ticket_request.skills_required}")
        
        # Test HREmployeeMatch
        print("\nTesting HREmployeeMatch...")
        employee_match = HREmployeeMatch(
            employee_id="alex_johnson",
            name="Alex Johnson",
            email="alex.johnson@company.com",
            department="Engineering",
            skills=["machine learning", "python", "tensorflow"],
            availability_status="Available",
            workload_level=45,
            overall_score=0.85,
            skill_match_score=0.9,
            availability_score=1.0,
            workload_score=0.55,
            department_match_score=0.8,
            matching_skills=["machine learning", "python"],
            missing_skills=[],
            match_reasoning="Strong ML expertise and currently available"
        )
        print(f"✅ HREmployeeMatch created: {employee_match.name}")
        print(f"   Overall Score: {employee_match.overall_score}")
        print(f"   Matching Skills: {employee_match.matching_skills}")
        
        # Test HRTicketResponse
        print("\nTesting HRTicketResponse...")
        ticket_response = HRTicketResponse(
            agent_name="HRAgent",
            ticket_id="test-001",
            matched_employees=[employee_match],
            total_matches=1,
            recommended_assignment="alex_johnson",
            assignment_reasoning="Best match for ML expertise"
        )
        print(f"✅ HRTicketResponse created for ticket: {ticket_response.ticket_id}")
        print(f"   Total matches: {ticket_response.total_matches}")
        print(f"   Recommended: {ticket_response.recommended_assignment}")
        
        # Test serialization
        print("\nTesting serialization...")
        response_dict = ticket_response.dict()
        print(f"✅ Serialization successful, keys: {list(response_dict.keys())}")
        
        # Test validation error
        print("\nTesting validation errors...")
        try:
            invalid_request = HRTicketRequest(
                ticket_id="",  # Invalid: empty string
                title="",      # Invalid: empty string
                description="Valid description",
                priority="invalid_priority"  # Invalid priority
            )
        except ValidationError as e:
            print(f"✅ Validation error caught as expected: {len(e.errors())} errors")
            for error in e.errors():
                print(f"   - {error['loc'][0]}: {error['msg']}")
        
        print("\n🎉 All Pydantic model tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pydantic_models()
    sys.exit(0 if success else 1)
