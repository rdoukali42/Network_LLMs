#!/usr/bin/env python3
"""
Debug script for HR Agent - shows detailed input/output for debugging
"""

import sys
import os
import json
from datetime import datetime

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def print_debug_separator(title):
    """Print a debug separator"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_json_pretty(data, title="Data"):
    """Pretty print JSON data"""
    print(f"\n📋 {title}:")
    print("-" * 40)
    print(json.dumps(data, indent=2, default=str))

def debug_hr_agent():
    """Debug HR Agent with detailed input/output"""
    
    print_debug_separator("HR AGENT DEBUG SESSION")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Import HR Agent and dependencies
        from agents.hr_agent import HRAgent
        from tools.availability_tool import AvailabilityTool
        
        print("\n✅ Imports successful")
        
        # Initialize availability tool and HR agent
        print_debug_separator("INITIALIZING HR AGENT")
        
        availability_tool = AvailabilityTool()
        hr_agent = HRAgent(config={}, tools=[], availability_tool=availability_tool)
        
        print("✅ HR Agent initialized successfully")
        print(f"   Agent Name: {hr_agent.name}")
        print(f"   Has Availability Tool: {hr_agent.availability_tool is not None}")
        
        # Test Case 1: Legacy Query Format
        print_debug_separator("TEST CASE 1: LEGACY QUERY FORMAT")
        
        legacy_input = {
            "query": "I need help with machine learning model deployment using Python and Docker"
        }
        
        print_json_pretty(legacy_input, "INPUT (Legacy Format)")
        
        print("\n🚀 Processing legacy query...")
        legacy_result = hr_agent.run(legacy_input)
        
        print_json_pretty(legacy_result, "OUTPUT (Legacy Query)")
        
        # Test Case 2: Structured Ticket Format
        print_debug_separator("TEST CASE 2: STRUCTURED TICKET FORMAT")
        
        structured_input = {
            "ticket_id": "TICKET-ML-001",
            "title": "ML Model Performance Optimization",
            "description": "Need help optimizing a recommendation system model. Current accuracy is 75% but we need to reach 85%. Using collaborative filtering with TensorFlow.",
            "priority": "high",
            "category": "Machine Learning",
            "department": "Engineering",
            "skills_required": ["machine learning", "tensorflow", "python", "optimization", "recommendation systems"],
            "urgency_level": 4
        }
        
        print_json_pretty(structured_input, "INPUT (Structured Format)")
        
        print("\n🚀 Processing structured ticket...")
        structured_result = hr_agent.run(structured_input)
        
        print_json_pretty(structured_result, "OUTPUT (Structured Ticket)")
        
        # Test Case 3: Invalid Input (Error Handling)
        print_debug_separator("TEST CASE 3: ERROR HANDLING")
        
        invalid_input = {
            "ticket_id": "",  # Invalid: empty
            "title": "",      # Invalid: empty
            "description": "This should fail validation",
            "priority": "super_urgent"  # Invalid priority
        }
        
        print_json_pretty(invalid_input, "INPUT (Invalid Data)")
        
        print("\n🚀 Processing invalid input...")
        error_result = hr_agent.run(invalid_input)
        
        print_json_pretty(error_result, "OUTPUT (Error Response)")
        
        # Test Case 4: Assignment Method
        print_debug_separator("TEST CASE 4: TICKET ASSIGNMENT")
        
        if structured_result.get('recommended_assignment'):
            recommended_emp = structured_result['recommended_assignment']
            
            print(f"📋 Testing assignment of TICKET-ML-001 to {recommended_emp}")
            
            assignment_result = hr_agent.assign_ticket(
                ticket_id="TICKET-ML-001",
                employee_id=recommended_emp,
                assignment_reason="Best match for ML expertise and availability"
            )
            
            print_json_pretty(assignment_result, "OUTPUT (Assignment)")
        else:
            print("⚠️ No recommendation available for assignment test")
        
        # Test Case 5: System Status
        print_debug_separator("TEST CASE 5: SYSTEM STATUS")
        
        print("🚀 Getting system status...")
        status_result = hr_agent.get_system_status()
        
        print_json_pretty(status_result, "OUTPUT (System Status)")
        
        # Summary
        print_debug_separator("DEBUG SUMMARY")
        
        print("📊 Test Results:")
        print(f"   ✅ Legacy Query: {legacy_result.get('status', 'unknown')}")
        print(f"   ✅ Structured Ticket: {structured_result.get('status', 'unknown')}")
        print(f"   ✅ Error Handling: {error_result.get('status', 'unknown')}")
        print(f"   ✅ System Status: {status_result.get('database_connection', False)}")
        
        if structured_result.get('matched_employees'):
            print(f"   📈 Found {len(structured_result['matched_employees'])} employee matches")
            best_match = structured_result['matched_employees'][0]
            print(f"   🏆 Best Match: {best_match['name']} (Score: {best_match['overall_score']:.2f})")
        
        print(f"   ⏱️ Processing Time: {structured_result.get('processing_time_ms', 0):.1f}ms")
        print(f"   🎯 Confidence: {structured_result.get('confidence_level', 0):.2f}")
        
        print("\n🎉 HR Agent Debug Session Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Debug session failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_hr_agent()
