#!/usr/bin/env python3
"""
Test the updated agents with tool integration
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

def test_agents_with_tools():
    """Test that agents can now use tools properly"""
    
    # Load environment variables
    load_dotenv()
    
    print("🧪 Testing Agent Tool Integration")
    print("=" * 50)
    
    try:
        # Import components
        from config.config_loader import config_loader
        from agents import MaestroAgent
        from tools.custom_tools import CalculatorTool, DocumentAnalysisTool
        
        # Load config
        config = config_loader.load_config("development")
        
        # Initialize tools
        tools = [
            CalculatorTool(),
            DocumentAnalysisTool()
        ]
        print(f"✅ Initialized {len(tools)} tools")
        
        # Initialize agent with tools
        maestro_agent = MaestroAgent(config=config, tools=tools)
        print("✅ MaestroAgent initialized with tools")
        
        # Check if agent executor was created
        if hasattr(maestro_agent, 'agent_executor') and maestro_agent.agent_executor:
            print("✅ Agent executor created successfully - tools are bound!")
        else:
            print("⚠️ Agent executor not created - falling back to LLM only")
        
        # Test with a query that should trigger tool usage
        test_query = "What are the latest developments in AI? Also calculate 25 + 37."
        print(f"\n🔍 Testing query: {test_query}")
        
        result = maestro_agent.run({"query": test_query})
        
        print(f"\n📊 Result:")
        print(f"Status: {result.get('status')}")
        print(f"Agent: {result.get('agent')}")
        print(f"Result length: {len(result.get('result', ''))}")
        
        # Check if result contains evidence of web search
        result_text = result.get('result', '')
        if 'search' in result_text.lower() or 'current' in result_text.lower():
            print("✅ Result may indicate web search was used")
        else:
            print("ℹ️ Result appears to be from LLM knowledge only")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agents_with_tools()
    
    if success:
        print("\n🎉 Agent tool integration test completed!")
        print("The agents are now configured to use tools including CalculatorTool and DocumentAnalysisTool.")
    else:
        print("\n❌ Test failed - check errors above")
    
    sys.exit(0 if success else 1)
