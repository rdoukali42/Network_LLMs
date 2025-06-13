#!/usr/bin/env python3
"""
Experiment runner script.
Runs experiments and compares configurations.
"""

import sys
import json
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from main import AISystem
from utils.helpers import save_experiment_results, format_evaluation_report


def run_experiments():
    """Run all experiments and generate comparison report."""
    print("🧪 Running Experiments...")
    
    # Test queries for evaluation
    test_queries = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "What are the applications of natural language processing?",
        "Explain the difference between AI and machine learning",
        "What are the ethical considerations in AI development?"
    ]
    
    experiments = ["experiment_1", "experiment_2"]
    all_results = {}
    
    for experiment in experiments:
        print(f"\n📊 Running {experiment}...")
        
        try:
            # Initialize system for this experiment
            system = AISystem()
            
            # Run experiment
            results = system.run_experiment(experiment, test_queries)
            all_results[experiment] = results
            
            # Save results
            filename = save_experiment_results(results, experiment)
            print(f"✅ Results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error running {experiment}: {e}")
            continue
    
    # Generate comparison report
    if len(all_results) >= 2:
        print("\n📈 Generating comparison report...")
        generate_comparison_report(all_results)
    
    print("\n🎉 Experiment run complete!")


def generate_comparison_report(results):
    """Generate a comparison report between experiments."""
    report = "# Experiment Comparison Report\n\n"
    
    for experiment, data in results.items():
        report += f"## {experiment.title()}\n"
        report += f"Configuration: {data.get('config', {}).get('experiment_name', 'N/A')}\n\n"
        
        # Add results summary
        experiment_results = data.get('results', [])
        report += f"Total queries processed: {len(experiment_results)}\n\n"
        
        for i, result in enumerate(experiment_results, 1):
            query = result.get('query', 'N/A')
            report += f"### Query {i}: {query}\n"
            report += f"Status: {result.get('result', {}).get('status', 'Unknown')}\n\n"
        
        report += "---\n\n"
    
    # Save comparison report
    with open("data/experiments/comparison_report.md", 'w') as f:
        f.write(report)
    
    print("✅ Comparison report saved to data/experiments/comparison_report.md")


if __name__ == "__main__":
    run_experiments()
