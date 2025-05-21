# src/analyzers/gpt_analyzer.py

import openai
from typing import Dict, List
import os
from datetime import datetime

class GPTAnalyzer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo-16k"

    def _generate_fallback_analysis(self, failure_data: Dict) -> str:
        """Generate a basic analysis when GPT API is unavailable."""
        return f"""
        Basic Analysis (GPT API Unavailable):
        
        Workflow: {failure_data['workflow_name']}
        Failure Reason: {failure_data['failure_reason']}
        
        Suggested Steps:
        1. Review the failure reason carefully
        2. Check the workflow configuration
        3. Verify all dependencies are correctly specified
        4. Ensure all required files exist
        5. Check for any permission issues
        
        Note: This is a basic analysis. For more detailed insights, please ensure the GPT API is properly configured and has sufficient quota.
        """

    def analyze_failure(self, failure_data: Dict) -> Dict:
        """Analyze a single failure using GPT."""
        
        prompt = f"""
        As a CI/CD expert, analyze this pipeline failure and provide specific, actionable insights:

        Pipeline Details:
        - Workflow: {failure_data['workflow_name']}
        - Failure Reason: {failure_data['failure_reason']}
        - Duration: {failure_data['duration']} seconds
        - Branch: {failure_data['branch']}

        Please provide a structured analysis with:
        1. Root Cause: What likely caused this failure?
        2. Immediate Fix: What specific steps should be taken to fix this?
        3. Prevention: How can similar failures be prevented in the future?
        4. Best Practices: What CI/CD best practices should be implemented?

        Format your response in a clear, structured way with bullet points.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert CI/CD engineer with deep knowledge of pipeline failures, testing, and best practices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
        except Exception as e:
            print(f"Error in GPT analysis: {str(e)}")
            analysis = self._generate_fallback_analysis(failure_data)
        
        return {
            'failure_id': failure_data['run_id'],
            'analysis': analysis,
            'timestamp': datetime.now().isoformat(),
            'workflow_name': failure_data['workflow_name'],
            'failure_reason': failure_data['failure_reason']
        }

    def analyze_failure_patterns(self, failures: List[Dict]) -> Dict:
        """Analyze patterns across multiple failures using GPT."""
        
        # Group failures by type
        failure_types = self._group_failures_by_type(failures)
        
        pattern_analysis = {}
        for failure_type, type_failures in failure_types.items():
            prompt = f"""
            As a CI/CD expert, analyze these {failure_type} failures and identify patterns:

            Number of failures: {len(type_failures)}
            Recent failures:
            {self._format_failures(type_failures[:5])}

            Please provide:
            1. Common Patterns: What patterns do you see in these failures?
            2. Systemic Issues: Are there any underlying system problems?
            3. Solution Strategy: What systematic solutions would you recommend?
            4. Prevention Plan: How can these failures be prevented?

            Format your response in a clear, structured way with bullet points.
            """
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert CI/CD engineer analyzing patterns in pipeline failures."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                pattern_analysis[failure_type] = response.choices[0].message.content
                
            except Exception as e:
                print(f"Error in pattern analysis: {str(e)}")
                pattern_analysis[failure_type] = "Error in pattern analysis"
        
        return pattern_analysis

    def _group_failures_by_type(self, failures: List[Dict]) -> Dict[str, List[Dict]]:
        """Group failures by their type."""
        failure_types = {}
        
        for failure in failures:
            failure_type = self._categorize_failure(failure)
            if failure_type not in failure_types:
                failure_types[failure_type] = []
            failure_types[failure_type].append(failure)
        
        return failure_types

    def _categorize_failure(self, failure: Dict) -> str:
        """Categorize a failure into a specific type."""
        reason = failure['failure_reason'].lower()
        
        if 'test' in reason:
            return 'Test Failures'
        elif 'build' in reason:
            return 'Build Failures'
        elif 'timeout' in reason:
            return 'Timeout Issues'
        elif 'dependency' in reason:
            return 'Dependency Problems'
        elif 'permission' in reason:
            return 'Permission Issues'
        elif 'network' in reason or 'connection' in reason:
            return 'Network Problems'
        else:
            return 'Other Issues'

    def _format_failures(self, failures: List[Dict]) -> str:
        """Format failures for the prompt."""
        formatted = ""
        for failure in failures:
            formatted += f"""
            - Workflow: {failure['workflow_name']}
              Reason: {failure['failure_reason']}
              Time: {failure['started_at']}
            """
        return formatted