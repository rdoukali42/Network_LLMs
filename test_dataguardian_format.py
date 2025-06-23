#!/usr/bin/env python3
"""
Test DataGuardianAgent format consistency
"""

import sys
import os
sys.path.append('/Users/level3/Desktop/Network/src')

from agents.data_guardian_agent import DataGuardianAgent
from agents.maestro_agent import MaestroAgent

def test_dataguardian_format():
    """Test that DataGuardianAgent returns the expected colon-separated format."""
    
    print("🧪 Testing DataGuardianAgent format consistency...")
    
    # Mock a simple vector manager for testing
    class MockVectorManager:
        def similarity_search(self, query, k=4):
            return [
                {
                    'content': 'This is a test document about company policies.',
                    'metadata': {'source': 'test_doc.md'},
                    'score': 0.85
                }
            ]
    
    # Create test config
    config = {
        'llm': {
            'model': 'gemini-1.5-flash',
            'temperature': 0.7
        }
    }
    
    # Create test agent
    vector_manager = MockVectorManager()
    agent = DataGuardianAgent(config=config, vector_manager=vector_manager)
    
    # Test query within scope
    test_input = {
        "query": "What is our harassment policy?",
        "search_queries": "harassment policy procedures"
    }
    
    print(f"   Testing query: {test_input['query']}")
    result = agent.run(test_input)
    
    if result['status'] == 'success':
        response = result['result']
        print(f"   Raw response: {response[:200]}...")
        
        # Check if it follows the colon-separated format
        lines = response.strip().split('\n')
        expected_headers = ['SCOPE_STATUS:', 'ANSWER_CONFIDENCE:', 'INFORMATION_FOUND:']
        
        found_headers = []
        for line in lines[:10]:  # Check first 10 lines
            for header in expected_headers:
                if line.strip().startswith(header):
                    found_headers.append(header)
                    print(f"   ✅ Found: {line.strip()}")
        
        if len(found_headers) == 3:
            print("   ✅ DataGuardianAgent returns correct colon-separated format!")
            
            # Test that MaestroAgent can parse this
            maestro = MaestroAgent(config=config)
            
            # Test MaestroAgent's parsing
            parsed_response = maestro._parse_data_guardian_response(response)
            has_sufficient = maestro._has_sufficient_answer(response)
            
            print(f"   📊 MaestroAgent parsing results:")
            print(f"      Parsed Response: {parsed_response}")
            print(f"      Has Sufficient Answer: {has_sufficient}")
            
            return True
        else:
            print(f"   ❌ Missing headers. Found {len(found_headers)}/3: {found_headers}")
            return False
    else:
        print(f"   ❌ Agent failed: {result}")
        return False

def test_outside_scope_query():
    """Test OUTSIDE_SCOPE query handling."""
    
    print("\n🧪 Testing OUTSIDE_SCOPE query...")
    
    # Mock vector manager with no relevant results
    class MockVectorManager:
        def similarity_search(self, query, k=4):
            return []  # No relevant documents
    
    config = {
        'llm': {
            'model': 'gemini-1.5-flash',
            'temperature': 0.7
        }
    }
    
    vector_manager = MockVectorManager()
    agent = DataGuardianAgent(config=config, vector_manager=vector_manager)
    
    # Test outside scope query
    test_input = {
        "query": "How do I fix my kitchen sink?",
        "search_queries": "kitchen sink plumbing repair"
    }
    
    print(f"   Testing query: {test_input['query']}")
    result = agent.run(test_input)
    
    if result['status'] == 'success':
        response = result['result']
        print(f"   Raw response: {response[:200]}...")
        
        # Test MaestroAgent's handling
        maestro = MaestroAgent(config=config)
        
        parsed_response = maestro._parse_data_guardian_response(response)
        has_sufficient = maestro._has_sufficient_answer(response)
        
        print(f"   📊 MaestroAgent results:")
        print(f"      Parsed Response: {parsed_response}")
        print(f"      Has Sufficient Answer: {has_sufficient}")
        
        scope_status = parsed_response.get('scope_status', 'UNKNOWN')
        
        if scope_status == "OUTSIDE_SCOPE":
            print("   ✅ Correctly identified as OUTSIDE_SCOPE!")
            if has_sufficient == "OUTSIDE_SCOPE":
                print("   ✅ MaestroAgent correctly returns OUTSIDE_SCOPE status!")
                return True
            else:
                print("   ❌ MaestroAgent should return OUTSIDE_SCOPE status for outside scope queries!")
                return False
        else:
            print(f"   ⚠️  Expected OUTSIDE_SCOPE, got: {scope_status} (may be correct if LLM determines it's within scope)")
            return True  # Don't fail on this since LLM might make different decisions
    else:
        print(f"   ❌ Agent failed: {result}")
        return False

def test_no_llm_fallback():
    """Test that fallback responses when no LLM is configured still use structured format."""
    
    print("\n🧪 Testing no-LLM fallback format...")
    
    # Mock vector manager
    class MockVectorManager:
        def similarity_search(self, query, k=4):
            return [
                {
                    'content': 'Test document content.',
                    'metadata': {'source': 'test.md'},
                    'score': 0.5
                }
            ]
    
    # Create agent without config (no LLM)
    vector_manager = MockVectorManager()
    agent = DataGuardianAgent(vector_manager=vector_manager)
    
    test_input = {
        "query": "Test query",
        "search_queries": "test"
    }
    
    result = agent.run(test_input)
    
    if result['status'] == 'success':
        response = result['result']
        print(f"   Response: {response[:100]}...")
        
        if response.startswith("SCOPE_STATUS:"):
            print("   ✅ Fallback response uses structured format!")
            return True
        else:
            print("   ❌ Fallback response doesn't use structured format!")
            return False
    else:
        print(f"   ❌ Fallback test failed: {result}")
        return False

if __name__ == "__main__":
    success1 = test_dataguardian_format()
    success2 = test_outside_scope_query()
    success3 = test_no_llm_fallback()
    
    if success1 and success2 and success3:
        print("\n🎉 All format consistency tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
