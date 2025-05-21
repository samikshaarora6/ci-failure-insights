# src/scripts/analyze_pipeline.py

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.analyzers.pipeline_analyzer import PipelineAnalyzer
from src.database.db_manager import DatabaseManager

def analyze_pipeline(pipeline_path: str, failure_data: dict):
    """Analyze a pipeline file and store the results."""
    analyzer = PipelineAnalyzer()
    db = DatabaseManager()
    
    # Analyze the pipeline
    analysis = analyzer.analyze_pipeline(pipeline_path, failure_data)
    
    # Print the analysis
    print("\nPipeline Analysis Results:")
    print("=" * 50)
    
    if analysis.get('error'):
        print(f"Error: {analysis['error']}")
        return
    
    print(f"\nError Location: Line {analysis['error_location'][0]}")
    print(f"Error Line: {analysis['error_location'][1]}")
    
    print("\nContext:")
    print("Before:")
    for line in analysis['error_context']['before']:
        print(f"  {line}")
    print(f"Error: {analysis['error_context']['error_line']}")
    print("After:")
    for line in analysis['error_context']['after']:
        print(f"  {line}")
    
    print(f"\nError Type: {analysis['error_type']}")
    print("\nSuggestions:")
    for suggestion in analysis['suggestions']:
        print(f"- {suggestion}")
    
    # Store the analysis
    db.store_analysis_result('pipeline_analysis', analysis)

if __name__ == "__main__":
    # Example usage
    pipeline_path = ".github/workflows/ci.yaml"  # Update this path
    failure_data = {
        'failure_reason': 'Test failure in step: Run tests',
        'workflow_name': 'Build Failure Simulation'
    }
    
    analyze_pipeline(pipeline_path, failure_data)