#!/usr/bin/env python3
"""
Debug the vocal assistant conversation analysis to see what it's actually producing.
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def debug_conversation_analysis():
    """Debug what the vocal assistant is actually producing."""
    
    print("🔍 DEBUGGING VOCAL ASSISTANT ANALYSIS")
    print("=" * 60)
    
    try:
        from agents.vocal_assistant import VocalAssistant
        from config.config_manager import config_manager
        
        # Initialize vocal assistant
        vocal_assistant = VocalAssistant(config_manager)
        
        # Test conversation with clear redirect request
        test_conversation = """You: Hello, I need help with setting up a new database connection for our project.
Employee: Hi! I'm Sarah, and I'd be happy to help you with database setup. What type of database are you looking to connect to?
You: We're using PostgreSQL, but I'm having trouble with the connection string configuration.
Employee: I see. PostgreSQL connection strings can be tricky. What specific error are you encountering?
You: The connection times out after a few seconds. I think it might be a configuration issue.
Employee: That sounds like it could be related to network settings or authentication. Let me check... Actually, this seems like something that would be better handled by our database specialist, Mike. He has more experience with PostgreSQL performance issues.
You: Can you redirect this to Mike then?
Employee: Absolutely! I'll redirect this conversation to Mike right away. He'll be able to help you with the PostgreSQL connection timeout issue."""
        
        print(f"📝 Test Conversation:")
        print(f"   Length: {len(test_conversation)} characters")
        print(f"   Contains 'redirect': {'redirect' in test_conversation.lower()}")
        print(f"   Contains 'Mike': {'Mike' in test_conversation}")
        
        # Analyze the conversation using vocal assistant
        print(f"\n🔍 ANALYZING CONVERSATION...")
        
        analysis_result = vocal_assistant._analyze_conversation_for_redirects(test_conversation)
        
        print(f"\n📊 ANALYSIS RESULT:")
        print(f"   Type: {type(analysis_result)}")
        print(f"   Keys: {list(analysis_result.keys()) if isinstance(analysis_result, dict) else 'Not a dict'}")
        print(f"   Content: {analysis_result}")
        
        # Check what the VocalResponse parser gets
        print(f"\n🔍 TESTING VOCALRESPONSE PARSER...")
        from agents.vocal_assistant import VocalResponse
        
        # Test with the raw conversation
        vocal_response = VocalResponse({"response": test_conversation})
        print(f"   Redirect requested: {vocal_response.redirect_requested}")
        print(f"   Redirect info: {vocal_response.redirect_employee_info}")
        
        # Test with the analysis result if it's structured
        if isinstance(analysis_result, dict) and 'response' in analysis_result:
            vocal_response2 = VocalResponse(analysis_result)
            print(f"   Redirect requested (from analysis): {vocal_response2.redirect_requested}")
            print(f"   Redirect info (from analysis): {vocal_response2.redirect_employee_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ DEBUG FAILED: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    debug_conversation_analysis()
