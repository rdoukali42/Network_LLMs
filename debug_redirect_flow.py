#!/usr/bin/env python3
"""
Debug script to trace which redirect detection method is actually called
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def trace_redirect_flow():
    """Trace the redirect detection flow to see which method is called"""
    print("🔍 Tracing redirect detection flow...")
    
    # Check the call_handler.py flow
    with open('/Users/level3/Desktop/Network/src/graphs/call_handler.py', 'r') as f:
        content = f.read()
    
    print("\n📋 Call Handler Flow Analysis:")
    
    # Find the check_for_redirect method
    lines = content.split('\n')
    in_check_for_redirect = False
    redirect_detection_steps = []
    
    for i, line in enumerate(lines):
        if 'def check_for_redirect(' in line:
            in_check_for_redirect = True
            print(f"   Found check_for_redirect at line {i+1}")
            
        if in_check_for_redirect:
            # Look for redirect detection steps
            if 'REDIRECT_REQUESTED:' in line:
                redirect_detection_steps.append(f"Line {i+1}: {line.strip()}")
            elif '_extract_structured_redirect_info' in line:
                redirect_detection_steps.append(f"Line {i+1}: CALLS HANDLER METHOD - {line.strip()}")
            elif '_analyze_conversation_for_redirect' in line:
                redirect_detection_steps.append(f"Line {i+1}: CALLS VOCAL ASSISTANT METHOD - {line.strip()}")
            elif 'VocalResponse(' in line:
                redirect_detection_steps.append(f"Line {i+1}: CALLS LEGACY METHOD - {line.strip()}")
            
        if in_check_for_redirect and line.strip().startswith('def ') and 'check_for_redirect' not in line:
            break
    
    print("\n🔍 Redirect Detection Steps Found:")
    for step in redirect_detection_steps:
        print(f"   {step}")
    
    # Check which methods actually exist
    print("\n🔧 Method Availability Check:")
    
    # Check if vocal assistant method exists
    try:
        from src.agents.vocal_assistant import VocalAssistantAgent
        vocal_agent = VocalAssistantAgent()
        if hasattr(vocal_agent, '_analyze_conversation_for_redirect'):
            print("   ✅ Vocal Assistant AI method: _analyze_conversation_for_redirect EXISTS")
        else:
            print("   ❌ Vocal Assistant AI method: _analyze_conversation_for_redirect MISSING")
    except Exception as e:
        print(f"   ⚠️ Vocal Assistant import error: {e}")
    
    # Check if call handler method exists
    try:
        from src.graphs.call_handler import CallHandler
        handler = CallHandler({})
        if hasattr(handler, '_extract_structured_redirect_info'):
            print("   ✅ Call Handler method: _extract_structured_redirect_info EXISTS")
        else:
            print("   ❌ Call Handler method: _extract_structured_redirect_info MISSING")
    except Exception as e:
        print(f"   ⚠️ Call Handler import error: {e}")

if __name__ == "__main__":
    trace_redirect_flow()
