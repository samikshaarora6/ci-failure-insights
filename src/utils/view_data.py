# src/utils/view_data.py

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import DatabaseManager
import json

def view_data():
    db = DatabaseManager()
    
    # Get all pipeline runs
    with db.get_connection() as conn:
        conn.row_factory = db.dict_factory
        c = conn.cursor()
        
        print("\n=== Pipeline Runs ===")
        c.execute('SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 5')
        runs = c.fetchall()
        for run in runs:
            print(f"\nRun ID: {run['run_id']}")
            print(f"Workflow: {run['workflow_name']}")
            print(f"Status: {run['conclusion']}")
            print(f"Duration: {run['duration']} seconds")
            if run['failure_reason']:
                print(f"Failure Reason: {run['failure_reason']}")
        
        print("\n=== Test Results ===")
        c.execute('''
            SELECT tr.*, pr.workflow_name 
            FROM test_results tr
            JOIN pipeline_runs pr ON tr.run_id = pr.run_id
            WHERE tr.status = 'failed'
            ORDER BY tr.created_at DESC LIMIT 5
        ''')
        tests = c.fetchall()
        for test in tests:
            print(f"\nTest: {test['test_name']}")
            print(f"Workflow: {test['workflow_name']}")
            print(f"Error: {test['error_type']}")
            print(f"Message: {test['failure_message']}")
        
        print("\n=== Error Patterns ===")
        c.execute('SELECT * FROM error_patterns ORDER BY frequency DESC')
        patterns = c.fetchall()
        for pattern in patterns:
            print(f"\nPattern: {pattern['pattern']}")
            print(f"Type: {pattern['error_type']}")
            print(f"Frequency: {pattern['frequency']}")
            print(f"Suggested Fix: {pattern['suggested_fix']}")

if __name__ == "__main__":
    view_data()