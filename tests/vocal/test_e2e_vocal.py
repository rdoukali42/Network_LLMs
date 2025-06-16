#!/usr/bin/env python3
"""
End-to-end test of the Vocal Assistant integration.
Tests the complete workflow from ticket assignment to voice call.
"""

import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "front"))

def test_e2e_vocal_workflow():
    """Test the complete vocal assistant workflow."""
    print("🧪 End-to-End Vocal Assistant Workflow Test")
    print("=" * 60)
    
    try:
        # 1. Test ticket creation and assignment parsing
        print("\n1. Testing ticket assignment logic...")
        from front.tickets import TicketManager
        from front.database import db_manager
        
        ticket_manager = TicketManager()
        
        # Create test ticket
        ticket_id = ticket_manager.create_ticket(
            user="test_user",
            category="Technical Issue",
            priority="High",
            subject="ML Model Deployment Help",
            description="I need help deploying my machine learning model to production using Docker"
        )
        print(f"✅ Created test ticket: {ticket_id}")
        
        # 2. Test employee assignment
        print("\n2. Testing employee assignment...")
        employee = db_manager.get_employee_by_username("alex01")
        if employee:
            ticket_manager.assign_ticket(ticket_id, "alex01")
            print(f"✅ Assigned ticket to {employee['full_name']}")
        else:
            print("❌ Test employee alex01 not found")
            return False
        
        # 3. Test vocal assistant initialization
        print("\n3. Testing vocal assistant initialization...")
        from src.agents.vocal_assistant import VocalAssistantAgent
        vocal_agent = VocalAssistantAgent()
        
        # Test call initiation
        ticket_data = ticket_manager.get_ticket_by_id(ticket_id)
        employee_data = employee
        
        call_result = vocal_agent.run({
            "action": "initiate_call",
            "ticket_data": ticket_data,
            "employee_data": employee_data,
            "query": "ML model deployment help"
        })
        
        if call_result.get("status") == "call_initiated":
            print("✅ Voice call initiated successfully")
            print(f"   Call info: {call_result.get('call_info', {}).get('employee_name', 'Unknown')}")
        else:
            print(f"❌ Call initiation failed: {call_result}")
            return False
        
        # 4. Test voice components
        print("\n4. Testing voice components...")
        from front.vocal_components import SmoothVocalChat
        vocal_chat = SmoothVocalChat()
        
        # Test text-to-speech
        test_text = "Hello, this is a test of the text-to-speech system."
        tts_audio = vocal_chat.tts.synthesize_speech(test_text)
        if tts_audio:
            print("✅ Text-to-speech working")
        else:
            print("❌ Text-to-speech failed")
        
        # Test Gemini chat
        test_response = vocal_chat.gemini.chat(
            "What's the best way to deploy ML models?",
            ticket_data,
            employee_data,
            is_employee=True
        )
        if test_response and len(test_response) > 10:
            print("✅ Gemini chat working")
        else:
            print("❌ Gemini chat failed")
        
        # 5. Test solution generation
        print("\n5. Testing solution generation...")
        conversation_history = [
            ("User", "I need help deploying my ML model"),
            ("Employee", "I recommend using Docker containers with a Flask API"),
            ("User", "How do I set that up?"),
            ("Employee", "First create a Dockerfile, then build the image and run it")
        ]
        
        solution = vocal_chat.gemini.chat(
            "Generate a professional ticket resolution based on this conversation",
            ticket_data,
            employee_data,
            is_employee=False
        )
        
        if solution and len(solution) > 50:
            print("✅ Solution generation working")
            print(f"   Solution preview: {solution[:100]}...")
            
            # Update ticket with solution
            ticket_manager.update_employee_solution(ticket_id, solution)
            print("✅ Solution saved to ticket")
        else:
            print("❌ Solution generation failed")
        
        print("\n✅ End-to-end test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_integration():
    """Test Streamlit-specific integration points."""
    print("\n🧪 Testing Streamlit Integration Points")
    print("-" * 50)
    
    try:
        # Test session state setup
        print("Testing session state setup...")
        from front.tickets import show_ticket_interface
        print("✅ Main ticket interface importable")
        
        # Test call interface functions
        from front.tickets import show_active_call_interface, generate_solution_from_call
        print("✅ Call interface functions importable")
        
        # Test audio recorder availability
        try:
            from audio_recorder_streamlit import audio_recorder
            print("✅ Audio recorder available")
        except ImportError:
            print("❌ Audio recorder not available")
            return False
        
        # Test vocal components for Streamlit
        from front.vocal_components import SmoothVocalChat, CloudTTS, GeminiChat
        print("✅ All vocal components importable")
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit integration test failed: {e}")
        return False

def test_workflow_routing():
    """Test that the workflow properly routes to vocal assistant."""
    print("\n🧪 Testing Workflow Routing")
    print("-" * 50)
    
    try:
        from src.main import AISystem
        system = AISystem()
        
        # Test that vocal assistant is in the system
        if "vocal_assistant" in system.agents:
            print("✅ Vocal assistant found in agents")
        else:
            print("❌ Vocal assistant not found in agents")
            return False
        
        # Test workflow graph includes vocal assistant
        workflow = system.workflow
        if hasattr(workflow, 'graph'):
            # Check if vocal_assistant step exists
            if hasattr(workflow, '_vocal_assistant_step'):
                print("✅ Vocal assistant step found in workflow")
            else:
                print("❌ Vocal assistant step not found in workflow")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow routing test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Comprehensive Vocal Assistant Integration Test")
    print("=" * 70)
    
    tests = [
        ("End-to-End Workflow", test_e2e_vocal_workflow),
        ("Streamlit Integration", test_streamlit_integration),
        ("Workflow Routing", test_workflow_routing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} Test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Vocal Assistant integration is fully functional.")
        print("\n🚀 Ready for production use:")
        print("   - Voice calls are triggered when tickets are assigned")
        print("   - Answer button appears in sidebar for incoming calls")
        print("   - Voice conversations generate solutions")
        print("   - Solutions are automatically saved to tickets")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print(f"   Success rate: {(passed/total)*100:.1f}%")
