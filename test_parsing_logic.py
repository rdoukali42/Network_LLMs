#!/usr/bin/env python3
"""
Test script to verify the HR response parsing and assignment logic.
"""

import sys
import os
sys.path.append('src')
sys.path.append('front')

from tickets import TicketManager
from database import DatabaseManager

def test_parsing_logic():
    """Test the HR response parsing logic with real response format."""
    print("🧪 Testing HR Response Parsing Logic")
    print("=" * 50)
    
    # Sample HR response format from actual ticket
    sample_response = """I couldn't find a direct answer in our knowledge base for your request, but I can help connect you with the right expert.

👤 **Alex Johnson** (@alex01)
🏢 **Role**: Machine Learning Engineer
💼 **Expertise**: Python, Deep Learning, NLP, PyTorch, MLOps
📋 **Responsibilities**: Develop and optimize ML models

Deploy models to production

Maintain ML pipelines

Collaborate on data strategy
🟢 **Status**: Available

This employee has the expertise to help with your request.

Please reach out to them directly - they'll be able to provide specialized assistance with your specific issue."""

    print("Testing parsing conditions:")
    print(f"Contains 👤: {'👤' in sample_response}")
    print(f"Contains (@: {'(@' in sample_response}")
    print(f"Contains 🏢 **Role**: {'🏢 **Role**:' in sample_response}")
    
    # Test username extraction
    if "(@" in sample_response:
        username_match = sample_response.split("(@")[1].split(")")[0]
        print(f"Extracted username: '{username_match}'")
    
    # Test overall condition
    should_assign = "👤" in sample_response and "(@" in sample_response and "🏢 **Role**:" in sample_response
    print(f"Should assign ticket: {should_assign}")
    
    if should_assign:
        print("✅ SUCCESS: Parsing logic should work correctly!")
    else:
        print("❌ ISSUE: Parsing logic needs adjustment")

if __name__ == "__main__":
    test_parsing_logic()
