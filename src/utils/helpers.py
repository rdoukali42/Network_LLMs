"""
Utility functions for the AI project.
"""

import os
import json
from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_sample_data() -> List[str]:
    """Load sample documents for testing."""
    sample_docs = [
        """
        Artificial Intelligence (AI) is a branch of computer science that aims to create 
        intelligent machines that work and react like humans. Some of the activities 
        computers with artificial intelligence are designed for include speech recognition, 
        learning, planning, and problem solving.
        """,
        """
        Machine Learning is a subset of artificial intelligence (AI) that provides systems 
        the ability to automatically learn and improve from experience without being 
        explicitly programmed. Machine learning focuses on the development of computer 
        programs that can access data and use it to learn for themselves.
        """,
        """
        Natural Language Processing (NLP) is a subfield of linguistics, computer science, 
        and artificial intelligence concerned with the interactions between computers and 
        human language, in particular how to program computers to process and analyze 
        large amounts of natural language data.
        """
    ]
    return sample_docs


def ensure_directory_exists(path: str) -> None:
    """Ensure a directory exists, create if it doesn't."""
    Path(path).mkdir(parents=True, exist_ok=True)


def save_experiment_results(results: Dict[str, Any], experiment_name: str) -> str:
    """Save experiment results to a JSON file."""
    results_dir = "data/experiments"
    ensure_directory_exists(results_dir)
    
    filename = f"{results_dir}/{experiment_name}_results.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Experiment results saved to {filename}")
    return filename


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
