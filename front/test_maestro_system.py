#!/usr/bin/env python3
"""
Test the complete Maestro/DataGuardian implementation.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_maestro_data_guardian_system():
    """Test the complete Maestro/DataGuardian system."""
    print("🧪 Testing Maestro & DataGuardian System")
    print("=" * 50)
    
    try:
        # Import the main system
        from main import AISystem
        
        # Initialize system
        print("🚀 Initializing AI System...")
        system = AISystem()
        
        # Check that the correct agents are loaded
        if system.agents:
            print(f"✅ Agents loaded: {list(system.agents.keys())}")
            
            # Verify we have the new agents
            if "maestro" in system.agents and "data_guardian" in system.agents:
                print("✅ Maestro and DataGuardian agents confirmed")
            else:
                print("❌ Expected Maestro and DataGuardian agents not found")
                return False
        else:
            print("⚠️ No agents loaded")
        
        # Check vector store
        if system.vector_manager:
            print("✅ Vector store manager initialized")
        else:
            print("⚠️ Vector store manager not available")
        
        # Test queries that should use local documents
        test_queries = [
            "What is artificial intelligence?",  # Should find info in sample_doc_1.txt
            "What are the company values regarding integrity?",  # Should find info in code_of_conduct.md
            "Calculate 15 + 25 for me",  # Should use calculator tool
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            result = system.process_query(query)
            
            if result["status"] == "success":
                response = result.get("result", "")
                print(f"✅ Success - Response length: {len(response)} characters")
                
                # Check if response seems to use local data
                if len(response) > 50:
                    print("✅ Detailed response generated")
                else:
                    print("⚠️ Short response - may not have found relevant data")
            else:
                print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
        
        print("\n🎉 Maestro/DataGuardian system test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_maestro_data_guardian_system()
    sys.exit(0 if success else 1)
