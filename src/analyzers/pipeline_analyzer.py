# src/analyzers/pipeline_analyzer.py

import yaml
from typing import Dict, Tuple
import re
import openai
import os
from datetime import datetime

class PipelineAnalyzer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"

    def analyze_pipeline(self, pipeline_content: str, failure_data: Dict) -> Dict:
        """Analyze a pipeline file and identify the error location."""
        try:
            # Parse the YAML content
            workflow_yaml = yaml.safe_load(pipeline_content)
            
            # Find the error location
            error_line, error_context = self._find_error_location(pipeline_content, failure_data['failure_reason'])
            
            # Get the failed job
            failed_job = self._find_failed_job(workflow_yaml, failure_data['failure_reason'])
            
            # Get AI suggestions
            suggestions = self._get_ai_suggestions(
                error_line=error_line,
                error_context=error_context,
                failure_reason=failure_data['failure_reason'],
                failed_job=failed_job,
                workflow_name=failure_data['workflow_name']
            )
            
            return {
                'error_line': error_line,
                'error_context': error_context,
                'failed_job': failed_job,
                'suggestions': suggestions
            }
        except Exception as e:
            return {
                'error': f"Error analyzing pipeline: {str(e)}",
                'error_line': None,
                'error_context': None,
                'failed_job': "Unknown job",
                'suggestions': ['Check pipeline file syntax', 'Verify file permissions']
            }

    def _find_error_location(self, pipeline_content: str, failure_reason: str) -> Tuple[str, str]:
        """Find the exact line where the error occurred."""
        lines = pipeline_content.split('\n')
        
        # Try to match the failure reason with the pipeline content
        for i, line in enumerate(lines):
            if failure_reason.lower() in line.lower():
                return line.strip(), f"Line {i + 1}"
            
            # Check for common GitHub Actions error patterns
            if 'error:' in line.lower() or 'failed:' in line.lower():
                return line.strip(), f"Line {i + 1}"
        
        # If no exact match found, return the most relevant line
        for i, line in enumerate(lines):
            if 'run:' in line.lower() or 'uses:' in line.lower():
                return line.strip(), f"Line {i + 1}"
        
        return "Error location not found", "Unknown line"

    def _find_failed_job(self, workflow_yaml: Dict, failure_reason: str) -> str:
        """Find the job that failed in the workflow."""
        if not isinstance(workflow_yaml, dict):
            return "Unknown job"
        
        jobs = workflow_yaml.get('jobs', {})
        for job_name, job_config in jobs.items():
            # Check if the job name is mentioned in the failure reason
            if job_name.lower() in failure_reason.lower():
                return job_name
            
            # Check if any step in the job matches the failure reason
            steps = job_config.get('steps', [])
            for step in steps:
                if isinstance(step, dict):
                    step_name = step.get('name', '').lower()
                    if step_name in failure_reason.lower():
                        return f"{job_name} - {step['name']}"
        
        return "Unknown job"

    def _get_ai_suggestions(self, error_line: str, error_context: str, failure_reason: str, 
                          failed_job: str, workflow_name: str) -> list:
        """Get AI-powered suggestions for fixing the error."""
        try:
            prompt = f"""
            As a CI/CD expert, analyze this GitHub Actions workflow failure and provide specific, actionable suggestions:

            Workflow: {workflow_name}
            Failed Job: {failed_job}
            Error Line: {error_line}
            Error Context: {error_context}
            Failure Reason: {failure_reason}

            Please provide 3 specific, actionable suggestions to fix this error. Focus on practical steps that can be taken immediately.
            Format each suggestion as a clear, concise bullet point.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert CI/CD engineer with deep knowledge of GitHub Actions and pipeline failures."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            # Extract suggestions from the response
            suggestions = response.choices[0].message.content.strip().split('\n')
            # Clean up the suggestions (remove bullet points, etc.)
            suggestions = [s.strip('- ').strip() for s in suggestions if s.strip()]
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            print(f"Error getting AI suggestions: {str(e)}")
            return [
                "Review the error message carefully",
                "Check the workflow configuration",
                "Verify all dependencies are correctly specified"
            ]