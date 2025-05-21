# src/scripts/analyze_with_gpt.py

import os
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from src.database.db_manager import DatabaseManager
from src.analyzers.gpt_analyzer import GPTAnalyzer

def analyze_with_gpt():
    # Load environment variables
    load_dotenv()
    
    # Initialize database and analyzer
    db = DatabaseManager()
    analyzer = GPTAnalyzer()
    
    # Get recent failures
    with db.get_connection() as conn:
        conn.row_factory = db.dict_factory
        c = conn.cursor()
        c.execute('''
            SELECT * FROM pipeline_runs
            WHERE conclusion = 'failure'
            ORDER BY started_at DESC
            LIMIT 10
        ''')
        failures = c.fetchall()
    
    print(f"\nAnalyzing {len(failures)} recent failures with GPT")
    print("=" * 50)
    
    # Analyze each failure
    for failure in failures:
        print(f"\nAnalyzing failure in {failure['workflow_name']}")
        print(f"Failure Reason: {failure['failure_reason']}")
        
        analysis = analyzer.analyze_failure(failure)
        print("\nGPT Analysis:")
        print(analysis['analysis'])
        print("-" * 50)
        
        # Store the analysis
        db.store_analysis_result('gpt_analysis', analysis)
    
    # Analyze patterns across all failures
    print("\nAnalyzing failure patterns with GPT...")
    pattern_analysis = analyzer.analyze_failure_patterns(failures)
    
    print("\nPattern Analysis:")
    for failure_type, analysis in pattern_analysis.items():
        print(f"\n{failure_type}:")
        print(analysis)
        print("-" * 50)
        
        # Store the pattern analysis
        db.store_analysis_result('gpt_pattern_analysis', {
            'failure_type': failure_type,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })

if __name__ == "__main__":
    analyze_with_gpt()