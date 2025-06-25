#!/usr/bin/env python3
"""
Test to verify AI can detect redirect requests
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.graphs.workflow_core import MultiAgentWorkflow
from src.data.database_manager import DatabaseManager

def test_ai_redirect_detection():
    """Test if the AI can detect an actual redirect request"""
    print("🔍 Testing AI redirect detection with explicit redirect...")
    
    # Create minimal agent dictionary for testing
    db_manager = DatabaseManager()
    agents = {
        "database_manager": db_manager,
    }
    
    # Add VocalAssistant if available
    try:
        from src.agents.vocal_assistant import VocalAssistantAgent
        from src.config.config_loader import config_loader
        config = config_loader.load_config("development")
        agents["vocal_assistant"] = VocalAssistantAgent(config=config, tools=[])
        print("✅ VocalAssistant agent loaded successfully")
    except ImportError as e:
        print(f"⚠️ Warning: Could not load VocalAssistant agent: {e}")
        return False
    
    # Create workflow
    workflow = MultiAgentWorkflow(agents)
    
    # Create state with explicit redirect request
    state = {
        "ticket_id": "TEST-REDIRECT-001",
        "user_id": "test_user", 
        "user_input": "Please redirect this to Patrick for security help",
        "conversation_id": "conv_redirect_123",
        "messages": [
            {"role": "user", "content": "Hi, I'm having trouble with my account security"},
            {"role": "assistant", "content": "I understand you're having security issues. Let me help you with that."},
            {"role": "user", "content": "Actually, can you please redirect this ticket to Patrick? He's the security specialist who helped me before."},
            {"role": "assistant", "content": "Of course! I'll redirect this ticket to Patrick who specializes in security issues. He'll be able to help you better with your account security concerns."}
        ],
        "results": {
            "vocal_assistant": {
                "action": "end_call",
                "status": "call_completed", 
                "conversation_summary": "User requested redirect to Patrick for security help",
                "conversation_data": {
                    "conversation_summary": "User requested redirect to Patrick for security help",
                    "response": "User requested redirect to Patrick for security help"
                }
            }
        }
    }
    
    print(f"📋 State setup with explicit redirect request:")
    print(f"   - Ticket ID: {state['ticket_id']}")
    print(f"   - Messages: {len(state['messages'])} messages")
    print(f"   - Last message mentions: 'redirect this ticket to Patrick'")
    
    try:
        print(f"\n🔄 Processing end call workflow...")
        result_state = workflow.process_end_call(state)
        
        print(f"✅ Workflow completed successfully!")
        
        # Check if redirect was detected
        if isinstance(result_state, dict) and "results" in result_state:
            if "redirect_info" in result_state["results"]:
                redirect_info = result_state["results"]["redirect_info"]
                print(f"   ✅ Redirect detected: {redirect_info}")
                return True
            else:
                print(f"   ❌ No redirect info in results")
                print(f"   🔧 Available result keys: {list(result_state['results'].keys())}")
                return False
        else:
            print(f"   ❌ Invalid result state format")
            return False
            
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_ai_redirect_detection()
    if success:
        print(f"\n✅ SUCCESS: AI can detect redirect requests correctly!")
    else:
        print(f"\n⚠️ AI analysis ran but may not have detected the redirect correctly")
