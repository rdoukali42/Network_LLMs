#!/usr/bin/env python3
"""
Test the complete HR Agent with Pydantic models integration.
"""

import sys
import os
sys.path.append('src')

from agents.hr_agent import HRAgent
from tools.availability_tool import AvailabilityTool


def test_hr_agent_integration():
    """Test HR Agent with real data using new Pydantic models."""
    print("🧪 Testing HR Agent with Pydantic Models")
    print("=" * 50)
    
    try:
        # Initialize availability tool and HR agent
        availability_tool = AvailabilityTool()
        hr_agent = HRAgent(tools=[], availability_tool=availability_tool)
        
        print("✅ HR Agent initialized successfully")
        
        # Test with legacy query format (backward compatibility)
        print("\n1. Testing legacy query format...")
        legacy_query = {
            "query": "I need help implementing a machine learning classification model"
        }
        
        result = hr_agent.run(legacy_query)
        print(f"Status: {result.get('status')}")
        print(f"Ticket ID: {result.get('ticket_id')}")
        print(f"Total matches: {result.get('total_matches', 0)}")
        
        if result.get('matched_employees'):
            best_match = result['matched_employees'][0]
            print(f"Best match: {best_match['name']} (Score: {best_match['overall_score']:.2f})")
            print(f"Skills: {best_match['skills'][:3]}")
            print(f"Reasoning: {best_match['match_reasoning'][:100]}...")
        
        # Test with new structured format
        print("\n2. Testing structured ticket format...")
        structured_ticket = {
            "ticket_id": "TICKET-001",
            "title": "ML Model Development Help",
            "description": "Need assistance building a recommendation system using collaborative filtering",
            "priority": "high",
            "skills_required": ["machine learning", "python", "recommendation systems"],
            "department": "Engineering",
            "urgency_level": 4
        }
        
        result2 = hr_agent.run(structured_ticket)
        print(f"Status: {result2.get('status')}")
        print(f"Confidence: {result2.get('confidence_level', 0):.2f}")
        print(f"Processing time: {result2.get('processing_time_ms', 0):.1f}ms")
        print(f"Matching strategy: {result2.get('matching_strategy')}")
        
        # Test assignment method
        print("\n3. Testing ticket assignment...")
        if result2.get('recommended_assignment'):
            assignment_result = hr_agent.assign_ticket(
                ticket_id="TICKET-001",
                employee_id=result2['recommended_assignment'],
                assignment_reason="Best skill match for ML project"
            )
            print(f"Assignment status: {assignment_result.get('status')}")
            print(f"Assigned to: {assignment_result.get('assigned_employee_name')}")
            print(f"Confidence: {assignment_result.get('assignment_confidence', 0):.2f}")
        
        # Test system status
        print("\n4. Testing system status...")
        status = hr_agent.get_system_status()
        print(f"Total employees: {status.get('total_employees', 0)}")
        print(f"Available: {status.get('available_employees', 0)}")
        print(f"Busy: {status.get('busy_employees', 0)}")
        print(f"Database connected: {status.get('database_connection', False)}")
        
        # Test error handling
        print("\n5. Testing error handling...")
        invalid_ticket = {
            "ticket_id": "",  # Invalid
            "title": "",      # Invalid
            "description": "Valid description"
        }
        
        error_result = hr_agent.run(invalid_ticket)
        print(f"Error status: {error_result.get('status')}")
        print(f"Error type: {error_result.get('error_type')}")
        print(f"Error message: {error_result.get('error_message', '')[:100]}...")
        
        print("\n🎉 HR Agent integration tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_hr_agent_integration()
    sys.exit(0 if success else 1)
