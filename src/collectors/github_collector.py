# src/collectors/github_collector.py

import requests
from datetime import datetime
from typing import Dict, List
import base64
import re

class GitHubCollector:
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_workflow_runs(self, created_after: str = None) -> List[Dict]:
        """Get workflow runs from GitHub.
        
        Args:
            created_after: ISO format date string to filter runs after this date
        """
        try:
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/actions/runs"
            params = {}
            if created_after:
                params['created'] = f">={created_after}"
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            runs = response.json()['workflow_runs']
            return [self._process_run(run) for run in runs]
            
        except Exception as e:
            print(f"Error getting workflow runs: {str(e)}")
            return []

    def get_run_jobs(self, run_id: str) -> List[Dict]:
        """Get jobs for a specific run."""
        url = f"{self.base_url}/actions/runs/{run_id}/jobs"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()['jobs']

    def get_job_logs(self, job_id: str) -> str:
        """Get logs for a specific job."""
        try:
            url = f"{self.base_url}/actions/jobs/{job_id}/logs"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Try different encodings if utf-8 fails
            try:
                return response.content.decode('utf-8')
            except UnicodeDecodeError:
                return response.content.decode('latin-1')
        except Exception as e:
            print(f"Error getting logs for job {job_id}: {str(e)}")
            return ""

    def _process_run(self, run: Dict) -> Dict:
        """Process a workflow run into a standard format."""
        return {
            'run_id': run['id'],
            'workflow_name': run['name'],
            'status': run['status'],
            'conclusion': run['conclusion'],
            'started_at': run['created_at'],
            'duration': self._calculate_duration(run['created_at'], run['updated_at']),
            'branch': run['head_branch'],
            'failure_reason': self._get_failure_reason(run['id']) if run['conclusion'] == 'failure' else None
        }

    def _calculate_duration(self, started: str, completed: str) -> int:
        """Calculate duration in seconds."""
        started_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
        completed_dt = datetime.fromisoformat(completed.replace('Z', '+00:00'))
        return int((completed_dt - started_dt).total_seconds())

    def _get_failure_reason(self, run_id: str) -> str:
        """Get the reason for failure if the run failed."""
        if run_id:
            jobs = self.get_run_jobs(run_id)
            for job in jobs:
                if job['conclusion'] == 'failure':
                    # First check the job steps
                    steps = job.get('steps', [])
                    for step in steps:
                        if step.get('conclusion') == 'failure':
                            step_name = step.get('name', '')
                            if 'test' in step_name.lower():
                                return f"Test failure in step: {step_name}"
                            elif 'build' in step_name.lower():
                                return f"Build failure in step: {step_name}"
                            return f"Failure in step: {step_name}"

                    # If no step failure found, try to get logs
                    logs = self.get_job_logs(job['id'])
                    if logs:
                        # Look for common failure patterns
                        if "AssertionError" in logs:
                            return "Test assertion failed"
                        elif "ModuleNotFoundError" in logs:
                            return "Missing dependency"
                        elif "Timeout" in logs:
                            return "Job timed out"
                        elif "Permission denied" in logs:
                            return "Permission error"
                        elif "Connection refused" in logs:
                            return "Network connection failed"
                        
                        # Try to find the last error message
                        error_lines = [line for line in logs.split('\n') 
                                     if any(keyword in line.lower() 
                                           for keyword in ['error', 'failed', 'exception', 'traceback'])]
                        if error_lines:
                            return error_lines[-1].strip()

                    # Fallback to job name
                    return f"Failure in job: {job.get('name', 'Unknown job')}"
        return 'Unknown failure'

    def get_file_content(self, file_path: str) -> str:
        """Get the content of a file from GitHub."""
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{file_path}",
                headers=self.headers
            )
            response.raise_for_status()
            
            # The content is base64 encoded
            content = base64.b64decode(response.json()['content']).decode('utf-8')
            return content
            
        except Exception as e:
            print(f"Error getting file content: {str(e)}")
            return ""