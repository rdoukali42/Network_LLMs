#!/usr/bin/env python3
"""
Live test of the fixed LLM evaluator with real API calls.
This script tests the evaluator with actual Google Gemini API calls.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Setup environment
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
load_dotenv(project_root / ".env")

def test_live_evaluation():
    """Test the LLM evaluator with real API calls."""
    
    # Check if API key is available
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("💡 Please set your Google API key in .env file")
        return False
    
    print("🧪 Live LLM Evaluator Test")
    print("=" * 50)
    print(f"🔑 API Key: {api_key[:10]}...")
    
    try:
        from config.config_loader import ConfigLoader
        from evaluation.llm_evaluator import LLMEvaluator
        
        # Load configuration
        config_loader = ConfigLoader(str(project_root / "configs"))
        config = config_loader.load_config("development")
        print("✅ Configuration loaded")
        
        # Initialize evaluator
        evaluator = LLMEvaluator(config)
        model_name = getattr(evaluator.judge_llm, 'model', 'unknown')
        print(f"✅ Evaluator initialized with model: {model_name}")
        
        # Test data
        test_query = "What are the main benefits of renewable energy?"
        test_response = """Renewable energy offers several key benefits:

1. **Environmental Impact**: Significantly reduces greenhouse gas emissions and air pollution
2. **Economic Benefits**: Creates jobs in manufacturing, installation, and maintenance
3. **Energy Independence**: Reduces reliance on fossil fuel imports
4. **Cost Savings**: Lower long-term operational costs once systems are installed
5. **Sustainability**: Inexhaustible energy sources like solar and wind
6. **Grid Stability**: Distributed generation improves energy security

These benefits make renewable energy crucial for addressing climate change while supporting economic growth."""
        
        print(f"\n🔍 Test Query: {test_query}")
        print(f"📝 Response Length: {len(test_response)} characters")
        
        # Run evaluation
        print("\n🤖 Running evaluation with Gemini Flash Pro...")
        evaluation_results = evaluator.evaluate_response(test_query, test_response)
        
        print(f"\n📊 EVALUATION RESULTS:")
        print("=" * 50)
        
        total_scores = []
        all_parsed_correctly = True
        
        for metric, result in evaluation_results.items():
            score = result.get('score')
            explanation = result.get('explanation', 'No explanation')
            parse_error = result.get('parse_error', False)
            
            print(f"\n📋 {metric.upper()}:")
            print(f"  Score: {score}/10" if score is not None else "  Score: Not evaluated")
            print(f"  Parse Error: {parse_error}")
            print(f"  Explanation: {explanation[:100]}{'...' if len(explanation) > 100 else ''}")
            
            if score is not None:
                total_scores.append(score)
            if parse_error:
                all_parsed_correctly = False
        
        # Summary
        print(f"\n🏆 SUMMARY:")
        print("=" * 50)
        
        if total_scores:
            avg_score = sum(total_scores) / len(total_scores)
            print(f"Overall Score: {avg_score:.1f}/10")
            
            quality_level = "Excellent" if avg_score >= 8 else "Good" if avg_score >= 6 else "Fair" if avg_score >= 4 else "Needs Improvement"
            print(f"Quality Level: {quality_level}")
        
        print(f"Metrics Evaluated: {len(total_scores)}/{len(evaluation_results)}")
        print(f"JSON Parsing Success: {'✅ All parsed correctly' if all_parsed_correctly else '⚠️ Some parsing issues'}")
        
        # Test success criteria
        success = (
            len(total_scores) >= len(evaluation_results) * 0.5 and  # At least 50% of metrics got scores
            all_parsed_correctly  # No parsing errors
        )
        
        if success:
            print(f"\n🎉 LIVE EVALUATION TEST PASSED!")
            print("✅ LLM evaluator is working correctly with real API calls")
            return True
        else:
            print(f"\n⚠️ LIVE EVALUATION TEST HAD ISSUES")
            print("🔧 Some metrics may need debugging")
            return False
            
    except Exception as e:
        print(f"\n❌ Live evaluation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Live LLM Evaluator Test")
    success = test_live_evaluation()
    
    if success:
        print("\n✅ All systems operational!")
        sys.exit(0)
    else:
        print("\n⚠️ Some issues detected - check output above")
        sys.exit(1)
