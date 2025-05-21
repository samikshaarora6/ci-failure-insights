# src/scripts/analyze_github_workflows.py

import os
import sys
from pathlib import Path
from typing import List, Dict
import json
import yaml
from datetime import datetime, timedelta
import requests

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.analyzers.pipeline_analyzer import PipelineAnalyzer
from src.database.db_manager import DatabaseManager
from src.collectors.github_collector import GitHubCollector

class GitHubWorkflowAnalyzer:
    def __init__(self):
        # Get GitHub credentials from environment variables
        token = os.getenv('GITHUB_TOKEN')
        owner = os.getenv('GITHUB_OWNER')
        repo = os.getenv('GITHUB_REPO')
        
        if not all([token, owner, repo]):
            raise ValueError("Missing GitHub credentials. Please set GITHUB_TOKEN, GITHUB_OWNER, and GITHUB_REPO in .env file")
        
        self.github_collector = GitHubCollector(token=token, owner=owner, repo=repo)
        self.pipeline_analyzer = PipelineAnalyzer()
        self.db = DatabaseManager()

    def analyze_failed_workflows(self, days_back: int = 7):
        """Analyze all failed workflows from the last N days."""
        # Get all workflow files first
        workflow_files = self._get_workflow_files()
        
        # Get failed workflow runs
        failed_runs = self._get_failed_workflows(days_back)
        
        print(f"\nFound {len(workflow_files)} workflow files")
        print(f"Analyzing {len(failed_runs)} failed workflows")
        print("=" * 50)
        
        for run in failed_runs:
            self._analyze_single_workflow(run, workflow_files)

    def _get_workflow_files(self) -> Dict[str, str]:
        """Get all workflow YAML files from GitHub."""
        try:
            # Get the contents of the .github/workflows directory
            url = f"https://api.github.com/repos/{self.github_collector.owner}/{self.github_collector.repo}/contents/.github/workflows"
            response = requests.get(url, headers=self.github_collector.headers)
            response.raise_for_status()
            
            workflow_files = {}
            for file in response.json():
                if file['name'].endswith(('.yml', '.yaml')):
                    # Get the file content
                    content = self.github_collector.get_file_content(file['path'])
                    if content:
                        workflow_files[file['name']] = content
            
            return workflow_files
            
        except Exception as e:
            print(f"Error getting workflow files: {str(e)}")
            return {}

    def _get_failed_workflows(self, days_back: int) -> List[Dict]:
        """Get all failed workflow runs from GitHub."""
        # Calculate the date range
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        # Get workflow runs
        runs = self.github_collector.get_workflow_runs(created_after=start_date)
        
        # Filter for failed runs
        return [run for run in runs if run['conclusion'] == 'failure']

    def _analyze_single_workflow(self, run: Dict, workflow_files: Dict[str, str]):
        """Analyze a single failed workflow run."""
        print(f"\nAnalyzing workflow: {run['workflow_name']}")
        print(f"Run ID: {run['run_id']}")
        print(f"Failure Reason: {run['failure_reason']}")
        
        try:
            # Find the matching workflow file
            workflow_content = None
            for filename, content in workflow_files.items():
                # Try to match the workflow name with the file content
                try:
                    workflow_yaml = yaml.safe_load(content)
                    if workflow_yaml.get('name') == run['workflow_name']:
                        workflow_content = content
                        break
                except yaml.YAMLError:
                    continue
            
            if not workflow_content:
                print(f"Could not find workflow file for: {run['workflow_name']}")
                return
            
            # Analyze the workflow
            analysis = self.pipeline_analyzer.analyze_pipeline(
                workflow_content,
                {
                    'failure_reason': run['failure_reason'],
                    'workflow_name': run['workflow_name'],
                    'run_id': run['run_id'],
                    'started_at': run['started_at'],
                    'duration': run['duration']
                }
            )
            
            # Print the analysis
            self._print_analysis(analysis)
            
            # Store the analysis
            self._store_analysis(run, analysis)
            
        except Exception as e:
            print(f"Error analyzing workflow: {str(e)}")

    def _print_analysis(self, analysis: Dict):
        """Print the analysis results."""
        if analysis.get('error'):
            print(f"Error: {analysis['error']}")
            return
        
        print("\nAnalysis Results:")
        print("-" * 30)
        
        if analysis['error_line']:
            print(f"Failed Job: {analysis['failed_job']}")
            print(f"Error: {analysis['error_line']}")
            print(f"Location: {analysis['error_context']}")
            print("\nAI Suggestions:")
            for suggestion in analysis['suggestions']:
                print(f"- {suggestion}")

    def _store_analysis(self, run: Dict, analysis: Dict):
        """Store the analysis results in the database."""
        analysis_data = {
            'run_id': run['run_id'],
            'workflow_name': run['workflow_name'],
            'failure_reason': run['failure_reason'],
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
        
        self.db.store_analysis_result('github_workflow_analysis', analysis_data)

def main():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        # Initialize the analyzer
        analyzer = GitHubWorkflowAnalyzer()
        
        # Analyze failed workflows from the last 7 days
        analyzer.analyze_failed_workflows(days_back=7)
    except ValueError as e:
        print(f"Error: {str(e)}")
        print("\nPlease make sure your .env file contains the following variables:")
        print("GITHUB_TOKEN=your_github_token")
        print("GITHUB_OWNER=your_username")
        print("GITHUB_REPO=your_repo")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()