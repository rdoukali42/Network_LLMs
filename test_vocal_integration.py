#!/usr/bin/env python3
"""
Simple test to verify vocal assistant integration works.
"""

import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "front"))

def test_vocal_assistant_import():
    """Test importing the VocalAssistant agent."""
    print("🧪 Testing Vocal Assistant Integration")
    print("=" * 50)
    
    try:
        from src.agents.vocal_assistant import VocalAssistantAgent
        print("✅ VocalAssistant import successful")
        
        # Test basic initialization
        vocal_agent = VocalAssistantAgent()
        print("✅ VocalAssistant initialization successful")
        
        return True
    except Exception as e:
        print(f"❌ VocalAssistant import failed: {e}")
        return False

def test_vocal_components_import():
    """Test importing vocal components."""
    try:
        from front.vocal_components import SmoothVocalChat, CloudTTS, GeminiChat
        print("✅ Vocal components import successful")
        
        # Test basic initialization
        vocal_chat = SmoothVocalChat()
        print("✅ SmoothVocalChat initialization successful")
        
        return True
    except Exception as e:
        print(f"❌ Vocal components import failed: {e}")
        return False

def test_workflow_integration():
    """Test workflow has vocal assistant step."""
    try:
        from src.main import AISystem
        system = AISystem()
        
        if "vocal_assistant" in system.agents:
            print("✅ VocalAssistant found in workflow system")
            return True
        else:
            print("❌ VocalAssistant not found in workflow system")
            return False
            
    except Exception as e:
        print(f"❌ Workflow integration test failed: {e}")
        return False

def test_session_state_setup():
    """Test session state variables are defined."""
    try:
        from front.tickets import show_ticket_interface
        print("✅ Ticket interface import successful")
        
        # Test that required functions exist
        from front.tickets import show_active_call_interface, generate_solution_from_call
        print("✅ Call interface functions found")
        
        return True
    except Exception as e:
        print(f"❌ Session state setup test failed: {e}")
        return False

def test_media_file_exists():
    """Test ringtone file exists."""
    ringtone_path = project_root / "media" / "old_phone.mp3"
    if ringtone_path.exists():
        print("✅ Ringtone file found")
        return True
    else:
        print("❌ Ringtone file not found")
        return False

if __name__ == "__main__":
    print("🔧 Vocal Assistant Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Vocal Assistant Import", test_vocal_assistant_import),
        ("Vocal Components Import", test_vocal_components_import),
        ("Workflow Integration", test_workflow_integration),
        ("Session State Setup", test_session_state_setup),
        ("Media File Exists", test_media_file_exists)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vocal Assistant integration is ready.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
