#!/usr/bin/env python3
"""
Demo script to test the AI app with Gemini Flash 1.5.
This script shows how to use the app without requiring API keys.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def demo_without_api_keys():
    """Demonstrate the app functionality without API keys."""
    print("🤖 AI App Demo with Gemini Flash 1.5")
    print("=" * 50)
    
    try:
        from src.config.config_loader import config_loader
        from src.tools.custom_tools import DocumentAnalysisTool, CalculatorTool
        from src.agents.base_agent import MaestroAgent, DataGuardianAgent
        
        # Load configuration
        config = config_loader.load_config("development")
        print(f"✅ Configuration loaded: {config['llm']['provider']} - {config['llm']['model']}")
        
        # Initialize tools (these work without API keys)
        doc_tool = DocumentAnalysisTool()
        calc_tool = CalculatorTool()
        
        print("✅ Tools initialized:")
        print(f"   📄 {doc_tool.name}: {doc_tool.description}")
        print(f"   🧮 {calc_tool.name}: {calc_tool.description}")
        
        # Test tool functionality (mock mode)
        print("\n🧪 Testing tools:")
        
        # Test calculator (works without API)
        calc_result = calc_tool._run("2 + 2 * 3")
        print(f"   Calculator: 2 + 2 * 3 = {calc_result}")
        
        # Test web search (mock response)
        web_result = web_tool._run("artificial intelligence")
        print(f"   Web Search: {web_result[:100]}...")
        
        # Test document analysis (mock response)
        doc_result = doc_tool._run("This is a sample document about AI.")
        print(f"   Document Analysis: {doc_result[:100]}...")
        
        print("\n✅ All components working in demo mode!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False
    
    return True

def demo_with_api_keys():
    """Demonstrate full functionality with API keys."""
    print("\n🔑 Testing with API Keys")
    print("=" * 30)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if API key is available
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("⚠️  GOOGLE_API_KEY not found in environment")
        print("   To test with real API calls:")
        print("   1. Create a .env file with GOOGLE_API_KEY=your_key_here")
        print("   2. Get your API key from: https://aistudio.google.com/app/apikey")
        return False
    
    print(f"✅ GOOGLE_API_KEY found: {google_api_key[:20]}...")
    
    try:
        from src.main import AISystem
        
        # Initialize full system
        system = AISystem("development")
        print("✅ Full AI system initialized with Gemini Flash 1.5")
        
        # Test a simple query
        test_query = "What is machine learning?"
        print(f"\n🤔 Testing query: '{test_query}'")
        
        # This would make actual API calls
        result = system.process_query(test_query)
        print(f"✅ Response received: {str(result)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting AI App Demo")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"🔧 Python path: {sys.path[0]}")
    
    # Always run demo without API keys
    demo_success = demo_without_api_keys()
    
    # Try demo with API keys if available
    if demo_success:
        demo_with_api_keys()
    
    print("\n" + "=" * 50)
    print("📚 How to test your app:")
    print("=" * 50)
    print("1. 🔧 Basic Setup Test:")
    print("   python demo_gemini_app.py")
    print()
    print("2. 🔑 With API Keys:")
    print("   echo 'GOOGLE_API_KEY=your_key_here' > .env")
    print("   python demo_gemini_app.py")
    print()
    print("3. 🧪 Run Full Test Suite:")
    print("   python -m pytest tests/ -v")
    print()
    print("4. 🏃‍♂️ Run Experiments:")
    print("   python scripts/run_experiments.py")
    print()
    print("5. 📊 Start Jupyter Notebook:")
    print("   jupyter notebook notebooks/experimentation.ipynb")
    print("\n🎯 Your AI app is now using Gemini Flash 1.5 instead of OpenAI!")
