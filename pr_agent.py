"""
PR Agent for OpenCode.ai
This agent specializes in handling Pull Request related tasks.
It receives tasks from the master agent, processes them, and returns results.
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from typing import TypedDict, List, Optional
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize LLM - prefer OPENCODE_API_KEY as alias, otherwise use GROQ_API_KEY
GROQ_KEY = os.getenv("GROQ_API_KEY")

# If OPENCODE key present, use it as the GROQ key (alias)
if not GROQ_KEY:
	raise RuntimeError("GROQ_API_KEY (or OPENCODE_API_KEY) not set. Set it in .env to use Groq.")

print("ℹ️ Using Groq for LLM calls.")
llm = ChatGroq(
	model="moonshotai/kimi-k2-instruct-0905",
	temperature=0,
	api_key=GROQ_KEY
)

# --- DATA MODELS ---

class PRAnalysisRequest(BaseModel):
	"""Request model for PR analysis tasks"""
	task_type: str  # 'analyze', 'review', 'suggest_fix', 'check_conflicts'
	pr_title: str
	pr_description: str
	pr_files_changed: List[dict]  # [{'filename': str, 'changes': str, 'additions': int, 'deletions': int}]
	pr_author: str
	base_branch: str
	target_branch: str
	additional_context: Optional[str] = None

class PRAnalysisResponse(BaseModel):
	"""Response model for PR analysis"""
	status: str  # 'success', 'error'
	analysis_type: str
	findings: str
	severity: str  # 'low', 'medium', 'high', 'critical'
	recommendations: List[str]
	action_required: bool
	suggested_action: str

# --- PR AGENT STATE ---

class PRAgentState(TypedDict):
	# Input from master agent
	task_id: str
	pr_request: PRAnalysisRequest
    
	# Processing steps
	code_analysis: str
	quality_assessment: str
	conflict_check: str
    
	# Output
	analysis_result: PRAnalysisResponse
	status: str
	error_message: Optional[str]

# --- AGENT TOOLS ---

def analyze_pr_code(pr_request: PRAnalysisRequest) -> str:
	"""
	Analyzes the code changes in the PR for quality, patterns, and potential issues.
	"""
	print("🔍 PR_AGENT: Analyzing code changes...")
    
	files_summary = "\n".join([
		f"- {f['filename']}: +{f['additions']} -{f['deletions']} lines"
		for f in pr_request.pr_files_changed[:10]
	])
    
	prompt = f"""
	Analyze this Pull Request for code quality and potential issues:
    
	TITLE: {pr_request.pr_title}
	DESCRIPTION: {pr_request.pr_description}
	AUTHOR: {pr_request.pr_author}
	BASE BRANCH: {pr_request.base_branch} -> {pr_request.target_branch}
    
	FILES CHANGED:
	{files_summary}
    
	Assess:
	1. Code complexity and readability
	2. Potential bugs or security issues
	3. Adherence to best practices
	4. Performance implications
    
	Keep response concise and actionable.
	"""
    
	response = llm.invoke(prompt)
	return response.content

def check_pr_conflicts(pr_request: PRAnalysisRequest) -> str:
	"""
	Checks for potential merge conflicts and compatibility issues.
	"""
	print("⚠️ PR_AGENT: Checking for conflicts...")
    
	prompt = f"""
	Check for potential merge conflicts and compatibility issues:
    
	Base Branch: {pr_request.base_branch}
	Target Branch: {pr_request.target_branch}
    
	Files Modified:
	{', '.join([f['filename'] for f in pr_request.pr_files_changed[:5]])}
    
	Identify:
	1. Likely merge conflicts
	2. Breaking changes
	3. Version compatibility issues
    
	Keep response concise.
	"""
    
	response = llm.invoke(prompt)
	return response.content

def assess_pr_quality(pr_request: PRAnalysisRequest, code_analysis: str) -> str:
	"""
	Provides an overall quality assessment and recommendations.
	"""
	print("📊 PR_AGENT: Assessing overall quality...")
    
	prompt = f"""
	Based on the code analysis, provide a quality assessment:
    
	CODE ANALYSIS:
	{code_analysis}
    
	ADDITIONAL CONTEXT:
	{pr_request.additional_context or 'None provided'}
    
	Provide:
	1. Overall quality score (1-10)
	2. Key strengths
	3. Areas for improvement
	4. Recommendation (approve/request changes/reject)
    
	Be constructive and specific.
	"""
    
	response = llm.invoke(prompt)
	return response.content

def generate_pr_report(pr_request: PRAnalysisRequest, analyses: dict) -> PRAnalysisResponse:
	"""
	Synthesizes all analyses into a structured PR response.
	"""
	print("📋 PR_AGENT: Generating report...")
    
	prompt = f"""
	Create a concise PR review report:
    
	CODE ANALYSIS: {analyses['code_analysis'][:300]}
	CONFLICT CHECK: {analyses['conflict_check'][:300]}
	QUALITY ASSESSMENT: {analyses['quality_assessment'][:300]}
    
	Format as JSON with keys:
	- severity: 'low'|'medium'|'high'|'critical'
	- key_findings: list of 2-3 main points
	- recommendations: list of 2-3 actionable items
	- action_required: boolean
	- suggested_action: 'approve'|'request_changes'|'reject'
	"""
    
	response = llm.invoke(prompt)
    
	try:
		# Try to parse JSON response
		import re
		json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
		if json_match:
			report_dict = json.loads(json_match.group())
		else:
			report_dict = {
				"severity": "medium",
				"key_findings": [response.content[:100]],
				"recommendations": ["Review manually"],
				"action_required": True,
				"suggested_action": "request_changes"
			}
	except:
		report_dict = {
			"severity": "medium",
			"key_findings": ["See analysis above"],
			"recommendations": ["Review manually"],
			"action_required": True,
			"suggested_action": "request_changes"
		}
    
	return PRAnalysisResponse(
		status="success",
		analysis_type=report_dict.get("analysis_type", "comprehensive"),
		findings="\n".join(report_dict.get("key_findings", [])),
		severity=report_dict.get("severity", "medium"),
		recommendations=report_dict.get("recommendations", []),
		action_required=report_dict.get("action_required", True),
		suggested_action=report_dict.get("suggested_action", "request_changes")
	)

# --- PR AGENT NODES ---

def node_analyze_code(state: PRAgentState) -> dict:
	"""Node: Analyzes PR code changes"""
	try:
		analysis = analyze_pr_code(state['pr_request'])
		return {"code_analysis": analysis, "status": "analyzing"}
	except Exception as e:
		return {"code_analysis": "", "error_message": str(e)}

def node_check_conflicts(state: PRAgentState) -> dict:
	"""Node: Checks for conflicts and compatibility"""
	try:
		conflict_check = check_pr_conflicts(state['pr_request'])
		return {"conflict_check": conflict_check}
	except Exception as e:
		return {"conflict_check": "", "error_message": str(e)}

def node_assess_quality(state: PRAgentState) -> dict:
	"""Node: Assesses overall PR quality"""
	try:
		quality = assess_pr_quality(state['pr_request'], state.get('code_analysis', ''))
		return {"quality_assessment": quality}
	except Exception as e:
		return {"quality_assessment": "", "error_message": str(e)}

def node_generate_report(state: PRAgentState) -> dict:
	"""Node: Generates final PR analysis report"""
	try:
		analyses = {
			'code_analysis': state.get('code_analysis', ''),
			'conflict_check': state.get('conflict_check', ''),
			'quality_assessment': state.get('quality_assessment', '')
		}
		report = generate_pr_report(state['pr_request'], analyses)
		return {
			"analysis_result": report,
			"status": "completed"
		}
	except Exception as e:
		return {"error_message": str(e), "status": "error"}

# --- PUBLIC INTERFACE FOR MASTER AGENT ---

def process_pr_task(task_id: str, pr_request: PRAnalysisRequest) -> dict:
	"""
	Main entry point for master agent to submit PR tasks.
    
	Returns:
		dict with analysis results and status
	"""
	print(f"\n🤖 PR_AGENT: Received task {task_id}")
	print(f"   PR Title: {pr_request.pr_title}")
	print(f"   Files Changed: {len(pr_request.pr_files_changed)}")
    
	# Initialize state
	state: PRAgentState = {
		"task_id": task_id,
		"pr_request": pr_request,
		"code_analysis": "",
		"quality_assessment": "",
		"conflict_check": "",
		"analysis_result": None,
		"status": "pending",
		"error_message": None
	}
    
	# Process through nodes
	state.update(node_analyze_code(state))
	state.update(node_check_conflicts(state))
	state.update(node_assess_quality(state))
	state.update(node_generate_report(state))
    
	# Prepare response for master agent
	result = {
		"task_id": task_id,
		"status": state.get("status"),
		"analysis": state.get("analysis_result").dict() if state.get("analysis_result") else None,
		"error": state.get("error_message")
	}
    
	print(f"   ✅ PR Analysis Complete: {result['status']}")
	return result

# --- TEST / DEMO ---

if __name__ == "__main__":
	# Example PR for testing
	sample_pr = PRAnalysisRequest(
		task_type="analyze",
		pr_title="Fix: Handle null pointer exception in user service",
		pr_description="This PR fixes the issue where user profiles with missing email fields would crash the API. Added proper null checks and validation.",
		pr_files_changed=[
			{"filename": "src/services/user_service.py", "changes": "Added null checks", "additions": 15, "deletions": 5},
			{"filename": "tests/test_user_service.py", "changes": "Added test cases", "additions": 25, "deletions": 0},
			{"filename": "docs/api.md", "changes": "Updated docs", "additions": 10, "deletions": 3}
		],
		pr_author="dev_john",
		base_branch="main",
		target_branch="develop",
		additional_context="Fixes critical issue #1234"
	)
    
	# Process the PR
	result = process_pr_task("PR_TASK_001", sample_pr)
    
	print("\n" + "="*60)
	print("PR ANALYSIS RESULT:")
	print("="*60)
	print(json.dumps(result, indent=2))

