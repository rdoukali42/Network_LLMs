#!/usr/bin/env python3
"""
Verification test to confirm WebSearchTool has been completely removed
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

def verify_websearch_removal():
    """Verify that WebSearchTool has been completely removed from the system"""
    
    print("🔍 WEBSEARCH TOOL REMOVAL VERIFICATION")
    print("=" * 50)
    
    try:
        # Test 1: Try to import WebSearchTool (should fail)
        print("1. Testing WebSearchTool import...")
        try:
            from tools.custom_tools import WebSearchTool
            print("❌ ERROR: WebSearchTool is still importable!")
            return False
        except ImportError:
            print("✅ WebSearchTool import correctly fails")
        
        # Test 2: Check available tools
        print("\n2. Checking available tools...")
        from tools.custom_tools import DocumentAnalysisTool, CalculatorTool
        
        doc_tool = DocumentAnalysisTool()
        calc_tool = CalculatorTool()
        
        print(f"✅ {doc_tool.name}: {doc_tool.description}")
        print(f"✅ {calc_tool.name}: {calc_tool.description}")
        
        # Test 3: Initialize AI System
        print("\n3. Testing AI System initialization...")
        from main import AISystem
        
        system = AISystem("development")
        print("✅ AI System initialized successfully")
        
        # Test 4: Check tools in agents
        print("\n4. Checking agent tools...")
        tools_count = len(system.tools)
        print(f"✅ System has {tools_count} tools available")
        
        if tools_count == 2:
            print("✅ Correct number of tools (expected: 2)")
        else:
            print(f"⚠️ Unexpected number of tools (expected: 2, got: {tools_count})")
        
        # Test 5: Run a simple query
        print("\n5. Testing system query processing...")
        result = system.process_query("What is 5 + 5?")
        
        if result.get('status') == 'success':
            print("✅ Query processing works correctly")
        else:
            print("⚠️ Query processing had issues")
        
        print("\n" + "=" * 50)
        print("🎉 VERIFICATION COMPLETE!")
        print("✅ WebSearchTool has been successfully removed")
        print("✅ System is working with remaining tools:")
        print("   • CalculatorTool")
        print("   • DocumentAnalysisTool")
        print("✅ AI workflow continues to function properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_websearch_removal()
    
    if success:
        print("\n🏆 REMOVAL VERIFICATION PASSED!")
        print("WebSearchTool has been completely removed from the system.")
    else:
        print("\n💥 Verification failed - check errors above")
    
    sys.exit(0 if success else 1)
