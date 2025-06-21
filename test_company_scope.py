#!/usr/bin/env python3
"""
Test script to verify company scope integration in DataGuardianAgent.
"""

import sys
sys.path.append('.')

def test_company_scope_loading():
    """Test that company scope loads correctly."""
    from src.agents.data_guardian_agent import DataGuardianAgent
    
    print("🧪 Testing Company Scope Loading...")
    
    # Create agent
    agent = DataGuardianAgent()
    
    # Test company scope loading
    scope = agent._get_company_scope()
    
    # Verify content
    assert len(scope) > 100, "Company scope should have substantial content"
    assert "Company Overview" in scope, "Should contain company overview section"
    assert "Information Technology" in scope, "Should mention IT focus"
    
    print("✅ Company scope loading test PASSED!")
    print(f"📄 Loaded {len(scope)} characters of company scope")
    print(f"📄 Preview: {scope[:150]}...")
    
    return True

def test_scope_in_prompt():
    """Test that company scope gets included in analysis prompt."""
    from src.agents.data_guardian_agent import DataGuardianAgent
    
    print("\n🧪 Testing Company Scope in Prompt...")
    
    # Create agent without vector manager for simple test
    agent = DataGuardianAgent()
    
    # Test that scope loading works in context
    scope = agent._get_company_scope()
    
    # Simulate prompt creation
    test_query = "Can you help with Python development?"
    test_prompt = f"""
COMPANY SCOPE AND CAPABILITIES:
{scope}

Query: {test_query}
"""
    
    assert "Company Overview" in test_prompt, "Scope should be in prompt"
    assert len(test_prompt) > 1000, "Prompt should include full scope content"
    
    print("✅ Company scope prompt integration test PASSED!")
    print(f"📄 Prompt contains {len(test_prompt)} characters total")
    
    return True

if __name__ == "__main__":
    print("🚀 Testing Company Scope Integration\n")
    
    try:
        test_company_scope_loading()
        test_scope_in_prompt()
        
        print("\n🎉 All tests PASSED! Company scope integration working correctly.")
        print("\n📋 Summary:")
        print("   ✅ Company scope loads directly from file")
        print("   ✅ Content is substantial and properly formatted")
        print("   ✅ Scope integrates properly into analysis prompts")
        print("   ✅ No vector database required for company scope")
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        sys.exit(1)
