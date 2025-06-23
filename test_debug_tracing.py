#!/usr/bin/env python3
"""
Test script to verify comprehensive debug tracing throughout the redirect workflow.
This simulates a redirect scenario to test all debug output.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import required components
from src.main import AISystem

def test_debug_tracing():
    """Test the complete redirect workflow with debug tracing."""
    print("=" * 80)
    print("🧪 TESTING DEBUG TRACING - Redirect Workflow")
    print("=" * 80)
    
    # Initialize workflow
    workflow = AISystem()
    
    # Test 1: Initial ticket that should trigger redirect
    print("\n📋 TEST 1: Simulating a ticket that needs redirect...")
    print("-" * 60)
    
    query = """I need help setting up a new development environment with Docker containers 
    and microservices architecture. I also need configuration for CI/CD pipelines. 
    This seems complex and I think I need someone with more expertise in DevOps."""
    
    # Run the workflow
    try:
        result = workflow.process_query(query)
        
        print("\n📊 WORKFLOW RESULT:")
        print(f"Final response length: {len(result.get('final_response', ''))}")
        print(f"Synthesis available: {'Yes' if result.get('synthesis') else 'No'}")
        print(f"Call info: {'Yes' if result.get('call_info') else 'No'}")
        print(f"Vocal action: {result.get('vocal_action', 'None')}")
        
        # Check if redirect flow was triggered
        if result.get('redirect_info'):
            print(f"✅ Redirect info captured: {result['redirect_info']}")
        if result.get('redirect_candidates'):
            print(f"✅ Redirect candidates found: {len(result['redirect_candidates'])}")
        if result.get('selected_redirect_employee'):
            print(f"✅ Selected redirect employee: {result['selected_redirect_employee'].get('full_name', 'Unknown')}")
        if result.get('redirect_call_result'):
            print(f"✅ Redirect call result: {result['redirect_call_result'].get('status', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Error during workflow execution: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🧪 DEBUG TRACING TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    test_debug_tracing()
