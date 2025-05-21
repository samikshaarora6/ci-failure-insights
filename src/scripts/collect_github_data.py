# src/scripts/collect_github_data.py

import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from src.collectors.github_collector import GitHubCollector
from src.database.db_manager import DatabaseManager

def collect_github_data():
    # Load environment variables
    load_dotenv()
    
    # Initialize collector and database
    collector = GitHubCollector(
        token=os.getenv("GITHUB_TOKEN"),
        owner=os.getenv("GITHUB_OWNER"),
        repo=os.getenv("GITHUB_REPO")
    )
    db = DatabaseManager()
    
    # Get all workflow runs
    runs = collector.get_workflow_runs()
    
    print(f"Found {len(runs)} workflow runs")
    
    # Store runs in database
    for run in runs:
        print(f"\nProcessing run {run['run_id']} - {run['workflow_name']}")
        print(f"Status: {run['status']}")
        print(f"Conclusion: {run['conclusion']}")
        print(f"Duration: {run['duration']} seconds")
        
        db.store_pipeline_run(run)
        
        # If the run failed, get more details
        if run['conclusion'] == 'failure':
            print(f"Failure Reason: {run['failure_reason']}")
            jobs = collector.get_run_jobs(run['run_id'])
            for job in jobs:
                if job['conclusion'] == 'failure':
                    print(f"Failed Job: {job['name']}")
                    print(f"Job Failure Reason: {job.get('failure_reason', 'Unknown reason')}")

if __name__ == "__main__":
    collect_github_data()