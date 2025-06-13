#!/usr/bin/env python3
"""
LangFuse Integration Test - Generate data for visualization
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_langfuse_integration():
    """Test system with LangFuse tracking enabled."""
    print("🚀 Testing LangFuse Integration")
    print("=" * 50)
    
    # Verify environment variables
    langfuse_public = os.getenv('LANGFUSE_PUBLIC_KEY')
    langfuse_secret = os.getenv('LANGFUSE_SECRET_KEY')
    google_api = os.getenv('GOOGLE_API_KEY')
    
    if not all([langfuse_public, langfuse_secret, google_api]):
        print("❌ Missing required API keys")
        return False
    
    print(f"✅ LangFuse Public Key: {langfuse_public[:20]}...")
    print(f"✅ LangFuse Secret Key: {langfuse_secret[:20]}...")
    print(f"✅ Google API Key: {google_api[:20]}...")
    
    try:
        from src.main import AISystem
        
        # Initialize system
        print("\n🔧 Initializing AI System...")
        system = AISystem("development")
        print("✅ System initialized successfully")
        
        # Test queries to generate LangFuse data
        test_queries = [
            "What is artificial intelligence?",
            "Explain the benefits of renewable energy",
            "How does machine learning work?",
            "What are the latest developments in quantum computing?",
            "Compare different programming languages for data science"
        ]
        
        print(f"\n🧪 Running {len(test_queries)} test queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}/{len(test_queries)}: {query}")
            try:
                result = system.process_query(query)
                print(f"✅ Status: {result.get('status', 'unknown')}")
                print(f"📊 Agents used: {result.get('agents_used', [])}")
                print(f"🛠️  Tools available: {result.get('tools_available', 0)}")
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        print("\n🎉 Test completed! Check your LangFuse dashboard:")
        print("🌐 https://cloud.langfuse.com")
        print("\nYou should see:")
        print("• 📊 Query traces with agent interactions")
        print("• ⏱️  Performance metrics")
        print("• 🔍 Tool usage patterns")
        print("• 📈 System behavior over time")
        
        return True
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False

def run_experiment_comparison():
    """Run A/B test experiment to generate comparison data."""
    print("\n🧪 Running Experiment Comparison")
    print("=" * 40)
    
    try:
        from src.main import AISystem
        
        # Test with different configurations
        configs = ["development", "production"]
        test_query = "Explain the impact of AI on healthcare"
        
        results = {}
        
        for config in configs:
            print(f"\n🔬 Testing with {config} configuration...")
            system = AISystem(config)
            result = system.process_query(test_query)
            results[config] = result
            print(f"✅ {config} test completed")
        
        print("\n📊 Experiment completed!")
        print("Check LangFuse dashboard for configuration comparison data")
        
        return True
        
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 LangFuse Integration & Visualization Test")
    print("=" * 60)
    
    success = test_langfuse_integration()
    
    if success:
        run_experiment_comparison()
        
        print("\n" + "=" * 60)
        print("🎯 Next Steps:")
        print("1. 🌐 Open https://cloud.langfuse.com")
        print("2. 📊 Navigate to your project dashboard")
        print("3. 🔍 Explore the traces and analytics")
        print("4. 📈 View performance metrics and comparisons")
        print("\n✨ Your AI system is now fully observable with LangFuse!")
    else:
        print("\n❌ Test failed. Please check your configuration.")
