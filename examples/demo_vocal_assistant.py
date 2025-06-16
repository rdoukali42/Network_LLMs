#!/usr/bin/env python3
"""
Demo script showing the Vocal Assistant workflow.
"""

import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "front"))

def demo_vocal_assistant():
    """Demonstrate the vocal assistant workflow."""
    print("🎤 Vocal Assistant Demo")
    print("=" * 50)
    
    print("This demo shows how the Vocal Assistant integration works:")
    
    print("\n1. 📋 TICKET CREATION")
    print("   User creates ticket: 'I need help deploying ML models'")
    
    print("\n2. 🤖 AI PROCESSING")
    print("   → Maestro analyzes ticket")
    print("   → DataGuardian searches documents")
    print("   → No sufficient answer found")
    print("   → HR_Agent finds expert: Alex Johnson (ML Engineer)")
    
    print("\n3. 📞 VOICE CALL INITIATION")
    print("   → VocalAssistant triggers call")
    print("   → Sidebar shows: '📞 Incoming Call from Alex Johnson'")
    print("   → Ticket: ML Model Deployment Help")
    
    print("\n4. 🎧 VOICE CONVERSATION")
    print("   User clicks '📞 Answer Call'")
    print("   → Active call interface appears")
    print("   → Voice conversation begins:")
    print("   ")
    print("   🎧 User: 'I need help deploying my ML model'")
    print("   🤖 Anna: 'Hi! I'm Anna, your AI assistant. Alex, this user needs help with ML model deployment. What's your experience with Docker containers?'")
    print("   👨‍💼 Alex: 'I've worked with Docker extensively. For ML models, I'd recommend using containers with Flask API.'")
    print("   🤖 Anna: 'That sounds great! Can you walk them through the specific steps you'd recommend?'")
    print("   👨‍💼 Alex: 'Sure! Create a Dockerfile, build the image, then deploy to cloud infrastructure.'")
    print("   🤖 Anna: 'Perfect! What would be the exact Docker commands they should use?'")
    print("   👨‍💼 Alex: 'Use docker build -t ml-model . then docker run -p 5000:5000 ml-model'")
    
    print("\n5. 📝 SOLUTION GENERATION")
    print("   → User clicks 'End Call & Generate Solution'")
    print("   → AI processes conversation")
    print("   → Professional solution generated from Alex's expertise:")
    print("   ")
    print("   📄 'Solution provided by Alex Johnson (ML Engineer):")
    print("      Based on our conversation, here are the recommended steps:")
    print("      1. Create a Dockerfile with Python and ML dependencies")
    print("      2. Build Docker image: docker build -t ml-model .")
    print("      3. Run container: docker run -p 5000:5000 ml-model")
    print("      4. Deploy to your preferred cloud infrastructure")
    print("      Contact Alex directly if you need further assistance.'")
    
    print("\n6. ✅ TICKET COMPLETION")
    print("   → Solution automatically saved to ticket")
    print("   → Ticket status: 'Solved'")
    print("   → User sees Alex's solution in 'My Tickets'")
    
    print("\n" + "=" * 50)
    print("🎉 ANNA AI ASSISTANT WORKFLOW COMPLETE!")
    print("Anna helped facilitate the conversation between user and expert!")
    
    # Demo the actual components
    print("\n🔧 Testing Actual Components:")
    
    try:
        from front.tickets import TicketManager
        from src.agents.vocal_assistant import VocalAssistantAgent
        from front.vocal_components import SmoothVocalChat
        
        print("✅ All components loaded successfully")
        
        # Test vocal assistant
        vocal_agent = VocalAssistantAgent()
        test_result = vocal_agent.run({
            "action": "initiate_call",
            "ticket_data": {"id": "demo", "subject": "Demo Call"},
            "employee_data": {"full_name": "Demo Employee", "username": "demo"}
        })
        
        if test_result.get("status") == "call_initiated":
            print("✅ Vocal Assistant call initiation working")
        
        # Test voice components
        vocal_chat = SmoothVocalChat()
        test_tts = vocal_chat.tts.synthesize_speech("Testing voice synthesis")
        if test_tts:
            print("✅ Text-to-speech working")
        
        test_response = vocal_chat.gemini.chat(
            "Hello", 
            {"subject": "Test"}, 
            {"full_name": "Test Employee"}, 
            is_employee=True
        )
        if test_response:
            print("✅ AI conversation working")
        
        print("\n🚀 System ready for voice-enabled ticket resolution!")
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")

if __name__ == "__main__":
    demo_vocal_assistant()
