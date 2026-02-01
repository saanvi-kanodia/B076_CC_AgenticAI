"""
Documentation PR Automation
Automatically creates PRs to improve api_docs.md based on incident patterns
"""

import os
import json
from datetime import datetime
from typing import List, Dict
from github import Github
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

class DocumentationPRAgent:
    """
    Analyzes incident patterns and automatically creates PRs to improve documentation
    """
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        if not self.github_token:
            print("⚠️ GITHUB_TOKEN not set - PRs will be simulated")
            self.github_client = None
        else:
            self.github_client = Github(self.github_token)
        
        if not self.groq_key:
            raise RuntimeError("GROQ_API_KEY required for documentation analysis")
        
        self.llm = ChatGroq(
            model="moonshotai/kimi-k2-instruct-0905",
            temperature=0.3,
            api_key=self.groq_key
        )
    
    def analyze_documentation_gaps(self) -> Dict:
        """
        Analyzes active incidents to find documentation gaps
        """
        print("📚 Analyzing documentation gaps from incident patterns...")
        
        # Load active incidents
        try:
            with open('dataset/active_incidents.json', 'r') as f:
                incidents = json.load(f)
        except FileNotFoundError:
            print("❌ No active incidents found. Run detection first.")
            return None
        
        # Load current documentation
        try:
            with open('dataset/api_docs.md', 'r') as f:
                current_docs = f.read()
        except FileNotFoundError:
            print("❌ api_docs.md not found")
            return None
        
        # Analyze what's missing
        gap_analysis = self._identify_gaps(incidents, current_docs)
        
        return gap_analysis
    
    def _identify_gaps(self, incidents: List[Dict], current_docs: str) -> Dict:
        """
        Use LLM to identify what's missing in the documentation
        """
        # Summarize incident patterns
        incident_summary = self._summarize_incidents(incidents)
        
        prompt = f"""
You are a technical documentation analyst. Analyze incident patterns to identify documentation gaps.

CURRENT DOCUMENTATION LENGTH: {len(current_docs)} characters

INCIDENT PATTERNS:
{incident_summary}

CURRENT DOCUMENTATION EXCERPT:
{current_docs[:2000]}...

Identify:
1. What topics are causing most support tickets?
2. What's unclear or missing in current docs?
3. What specific sections need improvement?
4. What new sections should be added?

Return JSON format:
{{
    "gaps_found": true/false,
    "gap_count": number,
    "critical_gaps": ["gap1", "gap2"],
    "suggested_additions": ["addition1", "addition2"],
    "priority": "high/medium/low",
    "reasoning": "explanation"
}}
"""
        
        response = self.llm.invoke(prompt)
        
        # Parse JSON response
        try:
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                gap_data = json.loads(json_match.group())
                return gap_data
        except:
            return {
                "gaps_found": False,
                "reasoning": "Could not parse LLM response"
            }
    
    def _summarize_incidents(self, incidents: List[Dict]) -> str:
        """
        Create a summary of incident patterns
        """
        summaries = []
        for inc in incidents[:10]:  # Top 10 incidents
            summaries.append(
                f"- {inc.get('summary', 'Unknown')[:100]} "
                f"({inc.get('ticket_count', 0)} tickets, "
                f"{inc.get('ml_category', 'unknown')} category)"
            )
        return "\n".join(summaries)
    
    def generate_documentation_improvements(self, gap_analysis: Dict) -> str:
        """
        Generate specific documentation improvements
        """
        if not gap_analysis.get('gaps_found'):
            print("✅ No significant documentation gaps found")
            return None
        
        print(f"📝 Generating improvements for {gap_analysis.get('gap_count', 0)} gaps...")
        
        # Load current docs
        with open('dataset/api_docs.md', 'r') as f:
            current_docs = f.read()
        
        prompt = f"""
You are a technical writer. Based on this gap analysis, write specific improvements to add to the API documentation.

GAP ANALYSIS:
{json.dumps(gap_analysis, indent=2)}

CURRENT DOCUMENTATION:
{current_docs[:3000]}...

Write a NEW SECTION to add to the documentation that addresses the critical gaps.
The section should:
1. Be clear and actionable
2. Include code examples if relevant
3. Address the most common confusion points
4. Follow the existing documentation style

Format as Markdown. Start with ## [Section Name]
"""
        
        response = self.llm.invoke(prompt)
        return response.content
    
    def create_pr_for_docs_update(
        self,
        improvements: str,
        gap_analysis: Dict,
        repo_name: str = "saanvi-kanodia/B076_CC_AgenticAI"
    ) -> Dict:
        """
        Creates a Pull Request with documentation improvements
        """
        if not self.github_client:
            print("📋 SIMULATION MODE - Would create PR with:")
            print(f"Repository: {repo_name}")
            print(f"Title: Update API documentation - {datetime.now().strftime('%Y-%m-%d')}")
            print(f"Improvements:\n{improvements[:500]}...")
            return {
                'status': 'simulated',
                'message': 'No GitHub token configured'
            }
        
        try:
            repo = self.github_client.get_repo(repo_name)
            
            # Create a new branch
            main_branch = repo.get_branch("main")
            branch_name = f"docs-update-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=main_branch.commit.sha
            )
            print(f"✅ Created branch: {branch_name}")
            
            # Get current file content
            file = repo.get_contents("dataset/api_docs.md", ref=branch_name)
            current_content = file.decoded_content.decode('utf-8')
            
            # Append improvements to the end
            updated_content = current_content + "\n\n---\n\n" + improvements
            
            # Update the file
            repo.update_file(
                path="dataset/api_docs.md",
                message="📚 Update API documentation based on incident patterns",
                content=updated_content,
                sha=file.sha,
                branch=branch_name
            )
            print("✅ Updated api_docs.md")
            
            # Create PR
            pr_title = f"📚 Update API Documentation - {datetime.now().strftime('%Y-%m-%d')}"
            pr_body = f"""## Documentation Update

**Auto-generated by Documentation PR Agent**

### Gaps Addressed:
{', '.join(gap_analysis.get('critical_gaps', []))}

### Priority: {gap_analysis.get('priority', 'medium').upper()}

### Reasoning:
{gap_analysis.get('reasoning', 'Based on recent incident patterns')}

### Changes:
- Added new section addressing common support issues
- Clarified existing documentation based on user confusion patterns
- Added examples for frequently misunderstood topics

**Generated from incident analysis on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**
"""
            
            pr = repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base="main"
            )
            
            print(f"✅ Created PR: {pr.html_url}")
            
            return {
                'status': 'success',
                'pr_number': pr.number,
                'pr_url': pr.html_url,
                'branch': branch_name
            }
            
        except Exception as e:
            print(f"❌ Error creating PR: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run_full_workflow(self, repo_name: str = "saanvi-kanodia/B076_CC_AgenticAI"):
        """
        Complete workflow: Analyze → Generate → Create PR
        """
        print("🚀 Starting Documentation PR Workflow...\n")
        
        # Step 1: Analyze gaps
        gap_analysis = self.analyze_documentation_gaps()
        if not gap_analysis or not gap_analysis.get('gaps_found'):
            print("\n✅ Documentation is up to date!")
            return None
        
        print(f"\n📊 Found {gap_analysis.get('gap_count', 0)} documentation gaps")
        print(f"Priority: {gap_analysis.get('priority', 'unknown').upper()}")
        
        # Step 2: Generate improvements
        improvements = self.generate_documentation_improvements(gap_analysis)
        if not improvements:
            print("\n⚠️ Could not generate improvements")
            return None
        
        print(f"\n📝 Generated {len(improvements)} characters of improvements")
        
        # Step 3: Create PR
        result = self.create_pr_for_docs_update(improvements, gap_analysis, repo_name)
        
        print("\n" + "="*80)
        if result['status'] == 'success':
            print(f"✅ SUCCESS! PR created: {result['pr_url']}")
        elif result['status'] == 'simulated':
            print("📋 SIMULATED - Add GITHUB_TOKEN to .env to create real PRs")
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
        print("="*80)
        
        return result


# Example usage
if __name__ == "__main__":
    agent = DocumentationPRAgent()
    
    # Run the full workflow
    result = agent.run_full_workflow()
    
    if result:
        print(f"\nFinal result: {json.dumps(result, indent=2)}")
