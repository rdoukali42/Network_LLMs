"""
Utility functions for the AI project.
"""

import os
import json
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: Datetime object to format
        format_str: Format string
        
    Returns:
        Formatted datetime string or empty string if dt is None
    """
    if dt is None:
        return ""
    return dt.strftime(format_str)


def sanitize_input(input_text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input by removing potentially harmful content.
    
    Args:
        input_text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized input text
    """
    if not input_text:
        return ""
    
    # Remove potential script tags and other dangerous content
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', input_text, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<[^>]+>', '', sanitized)  # Remove HTML tags
    sanitized = re.sub(r'[^\w\s\-.,!?@#$%^&*()+=\[\]{}|;:\'",.<>/]', '', sanitized)  # Remove special chars
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a unique identifier.
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part
        
    Returns:
        Generated unique ID
    """
    random_part = str(uuid.uuid4()).replace('-', '')[:length]
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def ensure_directory_exists(path: str) -> None:
    """Ensure a directory exists, create if it doesn't."""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_experiment_results(experiment_name: str) -> Dict[str, Any]:
    """Load experiment results from a JSON file."""
    filename = f"data/experiments/{experiment_name}_results.json"
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Experiment results file {filename} not found")
    
    with open(filename, 'r') as f:
        return json.load(f)


def format_evaluation_report(evaluation_results: List[Dict[str, Any]]) -> str:
    """Format evaluation results into a readable report."""
    report = "=== Evaluation Report ===\n\n"
    
    for i, result in enumerate(evaluation_results, 1):
        report += f"Query {i}: {result.get('query', 'N/A')}\n"
        report += f"Response: {result.get('response', 'N/A')[:100]}...\n"
        
        if 'evaluation' in result:
            eval_data = result['evaluation']
            report += "Scores:\n"
            for metric, score_data in eval_data.items():
                if isinstance(score_data, dict):
                    score = score_data.get('score', 'N/A')
                    report += f"  {metric.capitalize()}: {score}/10\n"
        
        report += "\n" + "="*50 + "\n\n"
    
    return report
