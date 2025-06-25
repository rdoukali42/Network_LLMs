#!/usr/bin/env python3
"""
Quick test to trace the AI analysis call flow
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.graphs.workflow_core import MultiAgentWorkflow
from src.data.database_manager import DatabaseManager

def test_ai_analysis_call_flow():
    """Test if the AI analysis method gets called during call completion"""
    print("🔍 Testing AI analysis call flow...")
    
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
        print("Voice functionality will not be available")
    
    # Create workflow
    workflow = MultiAgentWorkflow(agents)
    
    # Create initial state
    state = {
        "ticket_id": "TEST-AI-001",
        "user_id": "test_user", 
        "user_input": "Test AI call tracing",
        "conversation_id": "conv_123",
        "messages": [
            {"role": "user", "content": "Hi, I need help with my login issue"},
            {"role": "assistant", "content": "I understand you're having login issues. Let me redirect you to our security specialist Patrick who can help you better."},
            {"role": "user", "content": "That sounds good, please redirect the ticket to Patrick"}
        ],
        "results": {
            "vocal_assistant": {
                "response": "REDIRECT_REQUESTED: True\nUSERNAME_TO_REDIRECT: Patrick\nROLE_OF_THE_REDIRECT_TO: Security Specialist\nRESPONSIBILITIES: Login and security issues",
                "confidence": 0.9,
                "conversation_summary": "User requested redirect to Patrick for login security issues"
            }
        }
    }
    
    print(f"📋 State setup complete:")
    print(f"   - Ticket ID: {state['ticket_id']}")
    print(f"   - Messages: {len(state['messages'])} messages")
    print(f"   - Vocal result: {bool(state['results'].get('vocal_assistant'))}")
    
    try:
        print(f"\n🔄 Processing end call workflow...")
        result_state = workflow.process_end_call(state)
        
        print(f"✅ Workflow completed successfully!")
        print(f"   - Final results keys: {list(result_state['results'].keys())}")
        
        # Check if redirect was detected
        if "redirect_info" in result_state['results']:
            redirect_info = result_state['results']["redirect_info"]
            print(f"   ✅ Redirect detected: {redirect_info}")
            return True
        else:
            print(f"   ❌ No redirect info in results")
            return False
            
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_ai_analysis_call_flow()
    if success:
        print(f"\n✅ SUCCESS: AI analysis method is being called and working correctly!")
    else:
        print(f"\n❌ FAILURE: AI analysis method may not be working correctly")
