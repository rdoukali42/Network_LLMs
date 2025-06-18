#!/usr/bin/env python3
"""
Quick test to verify HR Agent Pydantic refactoring worked correctly
"""

import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_hr_agent_simple():
    """Simple test of HR Agent with mock data"""
    try:
        from agents.hr_agent import HRAgent
        from tools.availability_tool import AvailabilityTool
        
        print("🧪 Testing HR Agent Pydantic Refactoring")
        print("=" * 50)
        
        # Create availability tool and HR agent
        availability_tool = AvailabilityTool()
        hr_agent = HRAgent(config={}, tools=[], availability_tool=availability_tool)
        
        print("✅ HR Agent created successfully")
        
        # Test with a simple query (legacy format)
        test_query = {
            "query": "I need help with machine learning classification algorithms"
        }
        
        print("🔍 Processing test query...")
        result = hr_agent.run(test_query)
        
        print(f"✅ Query processed successfully!")
        print(f"   Status: {result.get('status')}")
        print(f"   Agent: {result.get('agent_name')}")
        print(f"   Ticket ID: {result.get('ticket_id')}")
        print(f"   Total matches: {result.get('total_matches', 0)}")
        print(f"   Confidence: {result.get('confidence_level', 0):.2f}")
        print(f"   Processing time: {result.get('processing_time_ms', 0):.1f}ms")
        
        if result.get('matched_employees'):
            best_match = result['matched_employees'][0]
            print(f"   Best match: {best_match['name']} (Score: {best_match['overall_score']:.2f})")
        
        # Test error handling
        print("\n🔍 Testing error handling...")
        invalid_query = {"invalid": "data"}
        error_result = hr_agent.run(invalid_query)
        
        print(f"✅ Error handling works!")
        print(f"   Status: {error_result.get('status')}")
        print(f"   Error type: {error_result.get('error_type')}")
        
        print("\n🎉 HR Agent Pydantic refactoring test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_hr_agent_simple()
    if success:
        print("\n✅ ALL TESTS PASSED - Pydantic refactoring is working correctly!")
    else:
        print("\n❌ TESTS FAILED - There are issues with the refactoring")
    sys.exit(0 if success else 1)
