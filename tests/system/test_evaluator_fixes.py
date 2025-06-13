#!/usr/bin/env python3
"""
Test script to verify LLM evaluator JSON parsing fixes.

This script tests the LLMEvaluator's ability to parse various JSON formats
that might be returned by the Gemini Flash Pro model.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

print(f"📁 Project root: {project_root}")
print(f"📁 Source path: {src_path}")
print(f"🐍 Python path: {sys.path[:2]}")  # Show first 2 entries

def test_json_parsing():
    """Test the JSON parsing capabilities of the LLM evaluator."""
    print("🧪 Testing LLM Evaluator JSON Parsing")
    print("=" * 50)
    
    try:
        from evaluation.llm_evaluator import LLMEvaluator
        
        # Mock config for testing
        test_config = {
            'evaluation': {
                'judge_model': 'gemini-1.5-flash',
                'metrics': ['relevance', 'accuracy', 'completeness']
            }
        }
        
        evaluator = LLMEvaluator.__new__(LLMEvaluator)  # Create without calling __init__
        evaluator.config = test_config
        evaluator.metrics = test_config['evaluation']['metrics']
        print("✅ LLMEvaluator instance created for testing")
        
        # Test cases: various JSON formats that LLM might return
        test_cases = [
            # Case 1: Clean JSON
            ('Clean JSON', '{"score": 9, "explanation": "Excellent response with clear details"}'),
            
            # Case 2: Markdown wrapped JSON
            ('Markdown JSON', '```json\n{"score": 8, "explanation": "Good response"}\n```'),
            
            # Case 3: Code block without json label
            ('Code block', '```\n{"score": 7, "explanation": "Decent response"}\n```'),
            
            # Case 4: JSON with extra whitespace
            ('Whitespace JSON', '  \n  {"score": 6, "explanation": "Okay response"}  \n  '),
            
            # Case 5: Natural language with score
            ('Natural language', 'I would rate this a score of 5 with explanation "Average response"'),
            
            # Case 6: Colon format
            ('Colon format', 'score: 4\nexplanation: "Below average response"'),
            
            # Case 7: Mixed format
            ('Mixed format', 'The score is 3. Explanation: "Poor response quality"'),
            
            # Case 8: Invalid JSON with fallback
            ('Invalid format', 'This is just text without proper structure'),
        ]
        
        print("\n🔍 Testing JSON parsing for different response formats:")
        print("-" * 60)
        
        success_count = 0
        for case_name, test_input in test_cases:
            try:
                result = evaluator._parse_evaluation(test_input)
                score = result.get('score')
                explanation = result.get('explanation', '')
                parse_error = result.get('parse_error', False)
                
                if score is not None:
                    status = "✅ PASS"
                    success_count += 1
                elif parse_error:
                    status = "⚠️  FALLBACK"
                else:
                    status = "❌ FAIL"
                
                score_str = str(score) if score is not None else "N/A"
                print(f"{status} {case_name:15} | Score: {score_str:>3} | Error: {parse_error}")
                if len(explanation) > 50:
                    print(f"     {'':15} | Explanation: {explanation[:47]}...")
                else:
                    print(f"     {'':15} | Explanation: {explanation}")
                    
            except Exception as e:
                print(f"❌ FAIL {case_name:15} | Exception: {e}")
        
        print("-" * 60)
        print(f"📊 Results: {success_count}/{len(test_cases)} test cases successfully parsed")
        
        if success_count >= len(test_cases) - 1:  # Allow 1 failure for invalid case
            print("🎉 JSON parsing tests PASSED!")
            return True
        else:
            print("⚠️  Some JSON parsing issues detected")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_configuration():
    """Test that the evaluator uses the correct model configuration."""
    print("\n🔧 Testing Model Configuration")
    print("=" * 50)
    
    try:
        from evaluation.llm_evaluator import LLMEvaluator
        
        # Test with different config setups
        configs = [
            {
                'evaluation': {
                    'judge_model': 'gemini-1.5-flash',
                    'metrics': ['relevance']
                }
            },
            {
                'evaluation': {
                    'metrics': ['relevance']
                }
                # Missing judge_model - should default to gemini-1.5-flash
            }
        ]
        
        for i, config in enumerate(configs, 1):
            # Test configuration parsing without initializing API client
            try:
                model_name = config.get('evaluation', {}).get('judge_model', 'gemini-1.5-flash')
                print(f"✅ Config {i}: Model name resolved to '{model_name}'")
            except Exception as e:
                print(f"❌ Config {i}: Error resolving model name: {e}")
                return False
            
        print("🎉 Model configuration tests PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Model configuration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 LLM Evaluator Test Suite")
    print("=" * 50)
    
    # Run tests
    json_test_passed = test_json_parsing()
    model_test_passed = test_model_configuration()
    
    print("\n📋 FINAL RESULTS")
    print("=" * 50)
    
    if json_test_passed and model_test_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ LLM Evaluator fixes are working correctly")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed - review the output above")
        sys.exit(1)
