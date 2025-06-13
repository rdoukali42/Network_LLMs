#!/usr/bin/env python3
"""Debug the markdown JSON parsing issue."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from evaluation.llm_evaluator import LLMEvaluator

# Create evaluator instance for testing
evaluator = LLMEvaluator.__new__(LLMEvaluator)

# Test the specific case that's failing
test_input = '```json\n{"score": 8, "explanation": "Good"}\n```'
print(f"Input: {repr(test_input)}")

result = evaluator._parse_evaluation(test_input)
print(f"Result: {result}")

# Debug the regex matching
import re

# Test the regex pattern
json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', test_input, re.DOTALL)
if json_match:
    print(f"Regex match found: {repr(json_match.group(1))}")
else:
    print("No regex match found")
