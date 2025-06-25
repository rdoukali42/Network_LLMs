#!/usr/bin/env python3
"""
Test the fixed redirect detection with the actual failing conversation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Test conversation that should trigger redirect
test_conversation = """You: Please provide the audio file.
Employee: Hi Tristan, my name is Anna.  I'm working on a support ticket from Patrick – it's medium priority and he's asking about what a quantum computer is.  I figured you'd be the perfect person to help me understand it well enough to give him a good answer.  Could you give me a hand with that?
You: sorry but I have I don't have any information about the quantum computer could you please read the ticket to Tristan
Employee: Oh, I apologize!  I seem to have gotten a little ahead of myself there.  Let me try explaining it to Tristan again, focusing on what we need for Patrick's ticket.

Hi Tristan, my name is Anna. I'm working on a support ticket from Patrick – it's medium priority and he's asking about what a quantum computer is. I figured you'd be the perfect person to help me understand it well enough to give him a good answer, since I don't have any background information on quantum computing myself. Could you give me a hand with that?
You: I mean could you redirect the ticket to Sarah
Employee: Oh, I see!  You'd like to redirect the ticket to Sarah instead.  That's perfectly understandable.  While I was hoping to learn more about quantum computers from you, I respect your time and suggestion.  Is there a reason you think Sarah would be a better fit for this particular ticket?  (Just curious, no pressure at all!)
You: I believe she have knowledge about this she could be more useful than
Employee: That's a great point!  I appreciate you explaining your reasoning.  Since you think Sarah has more relevant expertise, redirecting the ticket to her sounds like the best course of action.  Wonderful! I think I have everything I need. Thank you so much for your help!"""

print("🧪 Testing Enhanced Redirect Detection with Real Failing Conversation")
print("=" * 70)

try:
    from src.agents.vocal_assistant import VocalAssistantAgent
    from src.config.config_loader import ConfigLoader
    
    # Initialize minimal config
    config = {}
    vocal_assistant = VocalAssistantAgent(config)
    
    print(f"📝 Input conversation length: {len(test_conversation)} chars")
    print(f"📝 Preview: {test_conversation[:100]}...")
    
    print(f"\n🔍 Testing redirect detection...")
    result = vocal_assistant._analyze_conversation_for_redirect(test_conversation)
    
    print(f"\n📊 RESULTS:")
    print(f"🔍 Redirect requested: {result.get('redirect_requested', False)}")
    print(f"🔍 Detection method: {result.get('detection_method', 'unknown')}")
    print(f"🔍 Employee info: {result.get('redirect_employee_info', {})}")
    
    # Check if it found the redirect to Sarah
    if result.get('redirect_requested'):
        employee_info = result.get('redirect_employee_info', {})
        if 'sarah' in str(employee_info).lower():
            print(f"✅ SUCCESS: Correctly detected redirect to Sarah!")
        else:
            print(f"⚠️ PARTIAL: Detected redirect but not to Sarah")
            print(f"   Found info: {employee_info}")
    else:
        print(f"❌ FAILED: Should have detected redirect to Sarah")
        
    print(f"\n🏁 Test complete!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    print(f"📊 Traceback: {traceback.format_exc()}")
