"""
Utility functions for the AI project.
"""

import os
import json
from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


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
