#!/usr/bin/env python3
"""
Test the complete END_CALL redirect workflow with real conversation analysis.
"""

import sys
import os
sys.path.append('/Users/level3/Desktop/Network')
sys.path.append('/Users/level3/Desktop/Network/src')

from src.main import AISystem
import json

def test_complete_end_call_redirect():
    """Test the complete END_CALL workflow with conversation analysis."""
    
    print("="*80)
    print("🧪 TESTING COMPLETE END_CALL REDIRECT WORKFLOW")
    print("="*80)
    
    # Create AI system and get workflow
    ai_system = AISystem()
    print("✅ AI System initialized")
    workflow = ai_system.workflow
    
    # Real conversation that contains a redirect request
    conversation_with_redirect = """You: Please provide the audio file.
Employee: Hi Patrick, my name is Anna. I'm reaching out about a support ticket we received from Tristan regarding the backend technology choices for a project. It's marked as medium priority, and it seems he has some questions he'd like answered. Is this something you can help with today?
You: Could you help Sarah, Pip?
Employee: Oh, I'm sorry, I seem to have gotten the names mixed up! My apologies, Patrick. I was focusing on the ticket details and got a little sidetracked. So, to clarify, Tristan has some questions about which backend technology to use for his project, and I was hoping you could lend your expertise. Is that something you're able to assist with today?
You: I meant redirect the call to sir
Employee: Oh, I understand! My apologies again for the confusion. So, you'd like me to redirect Tristan's question to someone else? Could you let me know who would be the best person to handle this backend technology question? I want to make sure Tristan gets the most accurate and helpful response.
You: Sarah
Employee: Oh, I understand! Thanks for clarifying. So, you'd like me to redirect Tristan's question to Sarah. Could you tell me a little more about why Sarah would be the best person to handle this? Knowing the reason will help me explain the redirection to Tristan more effectively.
You: just do it
Employee: Okay, I understand! So you'd like me to forward Tristan's questions about backend technology choices to Sarah. Perfect! I will do that right away. Thank you so much for your help in clarifying this for me, Patrick. I really appreciate it!"""
    
    print(f"\n📝 Testing with conversation that contains redirect request")
    print(f"🎯 Expected: Should detect redirect to 'Sarah'")
    print(f"🎯 Expected: Should trigger redirect workflow")
    
    print("\n" + "="*60)
    print("PHASE 1: Testing VocalAssistant END_CALL Processing")
    print("="*60)
    
    # Test VocalAssistant end_call processing directly first
    from src.agents.vocal_assistant import VocalAssistantAgent
    
    vocal_agent = VocalAssistantAgent()
    
    # Simulate END_CALL input to VocalAssistant
    end_call_input_data = {
        "action": "end_call",
        "ticket_data": {
            "id": "TICKET001",
            "subject": "Backend Technology Choice",
            "description": "Questions about backend technology selection"
        },
        "employee_data": {
            "username": "patrick",
            "full_name": "Patrick Neumann",
            "role_in_company": "Product Development Lead"
        },
        "conversation_summary": conversation_with_redirect,
        "conversation_data": {
            "conversation_summary": conversation_with_redirect,
            "call_duration": "5 minutes"
        },
        "call_duration": "5 minutes"
    }
    
    print(f"🔄 Testing VocalAssistant end_call processing...")
    
    try:
        vocal_result = vocal_agent.run(end_call_input_data)
        
        print(f"📊 VOCALASSISTANT RESULT:")
        print(f"   Action: {vocal_result.get('action', 'unknown')}")
        print(f"   Status: {vocal_result.get('status', 'unknown')}")
        print(f"   Conversation summary length: {len(vocal_result.get('conversation_summary', ''))}")
        
        # Check if redirect markers were added
        enhanced_conversation = vocal_result.get("conversation_summary", "")
        if "REDIRECT_REQUESTED: True" in enhanced_conversation:
            print(f"   ✅ SUCCESS: VocalAssistant enhanced conversation with redirect markers!")
            
            # Extract redirect info
            lines = enhanced_conversation.split('\n')
            for line in lines:
                if 'USERNAME_TO_REDIRECT:' in line or 'REDIRECT_REQUESTED:' in line:
                    print(f"   🎯 REDIRECT MARKER: {line.strip()}")
                    
        else:
            print(f"   ❌ ISSUE: VocalAssistant did not add redirect markers")
            print(f"   🔍 Enhanced conversation preview: {enhanced_conversation[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: VocalAssistant processing failed: {e}")
        import traceback
        print(f"   📋 Details: {traceback.format_exc()}")
        return False
    
    print("\n" + "="*60)
    print("PHASE 2: Testing Call Completion Handler")
    print("="*60)
    
    # Now test the call completion handler directly
    from src.graphs.workflow import MultiAgentWorkflow
    
    # Create workflow instance
    workflow_instance = MultiAgentWorkflow(ai_system.agents)
    
    # Create state with the enhanced vocal result
    completion_state = {
        "messages": [],
        "current_step": "call_completion_handler",
        "results": {
            "vocal_assistant": vocal_result  # Use the enhanced result from VocalAssistant
        },
        "metadata": {"request_type": "voice"},
        "query": "Process end call for ticket TICKET001"
    }
    
    print(f"🔄 Testing call completion handler...")
    
    try:
        # Test call completion handler directly
        handler_result = workflow_instance._call_completion_handler_step(completion_state)
        
        print(f"📊 CALL COMPLETION RESULT:")
        print(f"   Call completed: {handler_result.get('results', {}).get('call_completed', False)}")
        print(f"   Result keys: {list(handler_result.get('results', {}).keys())}")
        
        # Test routing decision
        routing_decision = workflow_instance._check_call_completion(handler_result)
        print(f"   Routing decision: {routing_decision}")
        
        if routing_decision == "redirect":
            print(f"   ✅ SUCCESS: Call completion handler correctly routes to redirect!")
            return True
        else:
            print(f"   ❌ ISSUE: Call completion handler did not route to redirect")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: Call completion handler failed: {e}")
        import traceback
        print(f"   📋 Details: {traceback.format_exc()}")
        return False

def test_conversation_analysis_only():
    """Test just the conversation analysis part to debug AI parsing."""
    
    print("\n" + "="*80)
    print("🧪 TESTING CONVERSATION ANALYSIS ONLY")
    print("="*80)
    
    from src.agents.vocal_assistant import VocalAssistantAgent
    
    # Initialize VocalAssistant
    vocal_agent = VocalAssistantAgent()
    
    # Test conversation
    test_conversation = """You: I meant redirect the call to sir
Employee: Oh, I understand! So, you'd like me to redirect Tristan's question to someone else?
You: Sarah
Employee: So you'd like me to forward Tristan's questions to Sarah. Perfect! I will do that right away."""
    
    print(f"📝 Testing conversation analysis with:")
    print(f"   Length: {len(test_conversation)} characters")
    print(f"   Content: {test_conversation[:100]}...")
    
    # Test the analysis method directly
    try:
        result = vocal_agent._analyze_conversation_for_redirect(test_conversation)
        
        print(f"\n📊 ANALYSIS RESULT:")
        print(f"   Redirect requested: {result.get('redirect_requested', False)}")
        print(f"   Employee info: {result.get('redirect_employee_info', {})}")
        
        if result.get('redirect_requested'):
            print(f"   ✅ SUCCESS: Redirect detected in conversation!")
            return True
        else:
            print(f"   ❌ FAILURE: Redirect not detected")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: Analysis failed: {e}")
        import traceback
        print(f"   📋 Details: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Testing END_CALL redirect workflow...")
    
    # Test 1: Conversation analysis only
    print("\n🔹 Step 1: Testing conversation analysis...")
    analysis_success = test_conversation_analysis_only()
    
    # Test 2: Complete workflow
    print("\n🔹 Step 2: Testing complete workflow...")
    workflow_success = test_complete_end_call_redirect()
    
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    print(f"   Conversation Analysis: {'✅ PASSED' if analysis_success else '❌ FAILED'}")
    print(f"   Complete Workflow: {'✅ PASSED' if workflow_success else '❌ FAILED'}")
    
    if analysis_success and workflow_success:
        print(f"\n🎉 ALL TESTS PASSED! END_CALL redirect workflow is working!")
    else:
        print(f"\n❌ TESTS FAILED! Need to fix redirect workflow")
        sys.exit(1)
