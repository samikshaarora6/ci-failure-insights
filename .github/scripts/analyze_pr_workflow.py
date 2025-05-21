import os
import sys
import json
import yaml
import openai
from github import Github
from typing import Dict, List

def analyze_workflow(workflow_content: str) -> Dict:
    """Analyze a workflow file using OpenAI."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    As a CI/CD expert, analyze this GitHub Actions workflow and provide specific, actionable insights:

    Workflow Content:
    {workflow_content}

    Please provide:
    1. Potential issues or improvements
    2. Best practices that could be implemented
    3. Security considerations
    4. Performance optimizations

    Format your response as a JSON object with the following structure:
    {{
        "issues": [
            {{
                "type": "issue/improvement/best_practice/security/performance",
                "description": "description of the issue or suggestion",
                "line": "relevant line number or section",
                "suggestion": "specific suggestion to fix or improve"
            }}
        ],
        "summary": "brief summary of the analysis"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert CI/CD engineer with deep knowledge of GitHub Actions and best practices."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in AI analysis: {str(e)}")
        return {
            "issues": [],
            "summary": "Error in analysis. Please check the workflow manually."
        }

def post_comment(analysis: Dict, pr_number: int):
    """Post the analysis as a PR comment."""
    github_token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # Format the comment
    comment = "## Workflow Analysis\n\n"
    
    if analysis["issues"]:
        comment += "### Issues and Suggestions\n\n"
        for issue in analysis["issues"]:
            comment += f"#### {issue['type'].title()}\n"
            comment += f"- **Description**: {issue['description']}\n"
            comment += f"- **Location**: {issue['line']}\n"
            comment += f"- **Suggestion**: {issue['suggestion']}\n\n"
    else:
        comment += "No issues found in the workflow.\n\n"
    
    comment += f"### Summary\n{analysis['summary']}\n\n"
    comment += "---\n*This analysis was generated automatically. Please review the suggestions carefully.*"
    
    # Post the comment
    pr.create_issue_comment(comment)

def main():
    # Get the PR number from the event file
    event_path = os.getenv("GITHUB_EVENT_PATH")
    with open(event_path, 'r') as f:
        event_data = json.load(f)
        pr_number = event_data['pull_request']['number']
    
    # Get the changed workflow files
    github_token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # Analyze each changed workflow file
    for file in pr.get_files():
        if file.filename.startswith('.github/workflows/') and file.filename.endswith(('.yml', '.yaml')):
            print(f"Analyzing {file.filename}...")
            
            # Get the file content
            content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode()
            
            # Analyze the workflow
            analysis = analyze_workflow(content)
            
            # Post the analysis as a comment
            post_comment(analysis, pr_number)

if __name__ == "__main__":
    main()
