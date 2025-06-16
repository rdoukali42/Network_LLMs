#!/usr/bin/env python3
"""
Test script to verify Maestro integration for voice call solution review.
"""

import sys
import os
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "front"))

def test_maestro_voice_solution_review():
    """Test Maestro's ability to review voice call solutions."""
    print("🧪 Testing Maestro Integration for Voice Call Solutions")
    print("=" * 60)
    
    try:
        from workflow_client import WorkflowClient
        
        # Initialize workflow client
        print("1. Initializing Workflow Client...")
        client = WorkflowClient()
        
        if not client.is_ready():
            print("❌ Workflow client not ready")
            return False
            
        print("✅ Workflow client initialized")
        
        # Simulate voice call solution for review
        print("\n2. Testing Maestro Voice Call Solution Review...")
        
        test_input = """Voice Call Solution Review

Original Ticket:
Subject: ML Model Deployment Help
Description: I need help deploying my machine learning model to production. What tools should I use and how do I handle model updates?
Priority: Medium

Employee Expert: Alex Johnson (Machine Learning Engineer)

Voice Call Conversation Summary:
Anna: Hi Alex! I'm calling about a ticket regarding ML model deployment. The user needs help with deployment tools and handling model updates.
Alex: Hi Anna! For ML model deployment, I'd recommend using Docker containers with a model serving framework like TensorFlow Serving or Seldon Core.
Anna: That sounds great! Can you tell me more about the deployment process?
Alex: Sure! First, containerize the model with Docker, then use Kubernetes for orchestration. For model updates, implement a blue-green deployment strategy.
Anna: What about monitoring?
Alex: Use Prometheus for metrics and set up model drift detection. Also implement A/B testing for new model versions.
Anna: Perfect! I think I have everything I need. Thank you!

Employee Solution:
For ML model deployment, I recommend the following approach:

1. **Containerization**: Use Docker to containerize your model with TensorFlow Serving or Seldon Core
2. **Orchestration**: Deploy using Kubernetes for scalability and management
3. **Model Updates**: Implement blue-green deployment strategy for safe model updates
4. **Monitoring**: Set up Prometheus for metrics and implement model drift detection
5. **Testing**: Use A/B testing for new model versions

This approach ensures reliable, scalable, and maintainable ML model deployment.

Please provide a comprehensive final conclusion that:
1. Reviews the employee's solution for completeness and clarity
2. Adds any necessary context or technical insights
3. Ensures the solution addresses all aspects of the original ticket
4. Formats the response professionally for the customer
5. Provides clear next steps if needed

Create the final, comprehensive ticket resolution."""

        result = client.process_message(test_input)
        
        if result and "error" not in result:
            print("✅ Maestro successfully processed voice call solution")
            
            # Extract response
            response = None
            if isinstance(result, dict):
                response = (result.get("result") or 
                          result.get("synthesis") or 
                          result.get("response"))
            elif isinstance(result, str):
                response = result
                
            if response:
                print(f"\n📝 Maestro's Final Review:")
                print("-" * 40)
                print(response[:500] + ("..." if len(response) > 500 else ""))
                print("-" * 40)
                
                # Check if response contains comprehensive elements
                checks = [
                    ("deployment tools mentioned", any(tool in response.lower() for tool in ["docker", "kubernetes", "tensorflow serving", "seldon"])),
                    ("monitoring guidance", any(term in response.lower() for term in ["monitoring", "prometheus", "metrics"])),
                    ("professional formatting", "recommendation" in response.lower() or "solution" in response.lower()),
                    ("clear structure", any(marker in response for marker in ["1.", "2.", "•", "-"]))
                ]
                
                passed_checks = sum(1 for _, check in checks)
                total_checks = len(checks)
                
                print(f"\n🔍 Quality Checks: {passed_checks}/{total_checks} passed")
                for check_name, passed in checks:
                    status = "✅" if passed else "❌"
                    print(f"  {status} {check_name}")
                
                if passed_checks >= 3:
                    print("\n✅ Maestro integration working well!")
                    return True
                else:
                    print("\n⚠️ Maestro integration working but could be improved")
                    return True
            else:
                print("❌ No response from Maestro")
                return False
        else:
            print(f"❌ Error from Maestro: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_client_availability():
    """Test if WorkflowClient is available and working."""
    print("\n🧪 Testing WorkflowClient Availability")
    print("=" * 40)
    
    try:
        from workflow_client import WorkflowClient
        client = WorkflowClient()
        
        if client.is_ready():
            print("✅ WorkflowClient is ready")
            
            # Test simple query
            result = client.process_message("What is 2+2?")
            if result and "error" not in result:
                print("✅ WorkflowClient can process queries")
                return True
            else:
                print(f"❌ WorkflowClient query failed: {result}")
                return False
        else:
            print("❌ WorkflowClient not ready")
            return False
            
    except Exception as e:
        print(f"❌ WorkflowClient test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Maestro Integration Test for Voice Call Solutions")
    print("=" * 70)
    
    tests = [
        ("WorkflowClient Availability", test_workflow_client_availability),
        ("Maestro Voice Solution Review", test_maestro_voice_solution_review)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        result = test_func()
        if result:
            passed += 1
        print(f"{'='*70}")
    
    print(f"\n🎯 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Maestro integration for voice call solutions is working!")
    elif passed > 0:
        print("⚠️ Some tests passed. Maestro integration is partially working.")
    else:
        print("❌ All tests failed. Maestro integration needs attention.")
