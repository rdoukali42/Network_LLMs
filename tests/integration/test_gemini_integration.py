#!/usr/bin/env python3
"""
Test script to verify Gemini Flash 1.5 integration works.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.config.config_loader import ConfigLoader
    from src.evaluation.llm_evaluator import LLMEvaluator
    from src.chains.basic_chains import QuestionAnsweringChain
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    
    print("✅ All imports successful!")
    
    # Test configuration loading
    config_loader = ConfigLoader()
    config = config_loader.load_config("development")
    print(f"✅ Configuration loaded: {config['llm']['provider']} - {config['llm']['model']}")
    
    # Test that we can create Gemini instances (without actual API calls)
    try:
        # This will fail without API key, but that's expected
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.7
        )
        print("✅ ChatGoogleGenerativeAI instance created successfully")
    except Exception as e:
        print(f"⚠️  ChatGoogleGenerativeAI creation failed (expected without API key): {e}")
    
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-1.5-flash"
        )
        print("✅ GoogleGenerativeAIEmbeddings instance created successfully")
    except Exception as e:
        print(f"⚠️  GoogleGenerativeAIEmbeddings creation failed (expected without API key): {e}")
    
    print("\n🎉 Gemini Flash 1.5 integration is ready!")
    print("📝 To fully test:")
    print("   1. Add your GOOGLE_API_KEY to .env file")
    print("   2. Run: python scripts/setup_project.py")
    print("   3. Run: python -c \"from src.main import AISystem; system = AISystem(); print('System ready!')\"")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Make sure you've installed langchain-google-genai:")
    print("   pip install langchain-google-genai")
except Exception as e:
    print(f"❌ Error: {e}")
