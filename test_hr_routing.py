#!/usr/bin/env python3
"""
Test script to verify HR_Agent routing is working correctly.
"""

import sys
import os
sys.path.append('src')
sys.path.append('front')

from main import AISystem


def test_hr_routing():
    """Test HR_Agent routing with queries that should trigger it."""
    print("🧪 Testing HR_Agent Routing System")
    print("=" * 50)
    
    try:
        # Initialize system
        print("Initializing AI System...")
        system = AISystem()
        print("✅ System initialized successfully\n")
        
        # Test queries that should definitely not be in company documents
        test_queries = [
            "How do I build a quantum computer from scratch?",
            "What is the recipe for making chocolate cake?", 
            "How do I perform brain surgery?",
            "What are the steps to launch a rocket to Mars?",
            "How do I write machine learning algorithms in Python?"  # This should match Alex Johnson
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"🔍 Test {i}: {query}")
            print("-" * 40)
            
            try:
                result = system.process_query(query)
                result_text = result.get('result', '')
                
                # Check for HR routing indicators
                hr_indicators = [
                    'alex johnson', 'ml engineer', 'available', 'contact',
                    'employee', 'expert', 'specialist', 'status:', 'reach out'
                ]
                
                doc_indicators = [
                    'cannot provide instructions', 'documents do not contain',
                    'based on the information available', 'consult other resources'
                ]
                
                hr_matches = [ind for ind in hr_indicators if ind in result_text.lower()]
                doc_matches = [ind for ind in doc_indicators if ind in result_text.lower()]
                
                print(f"Result preview: {result_text[:150]}...")
                print(f"HR indicators: {hr_matches}")
                print(f"Doc indicators: {doc_matches}")
                
                if hr_matches and not doc_matches:
                    print("✅ SUCCESS: HR routing worked")
                elif doc_matches and not hr_matches:
                    print("❌ ISSUE: Document response instead of HR routing")
                else:
                    print("❓ MIXED: Check response manually")
                    
            except Exception as e:
                print(f"❌ Error processing query: {e}")
            
            print("\n")
            
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_hr_routing()
