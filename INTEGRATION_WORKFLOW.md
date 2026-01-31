"""
Integration Guide: How the PR Agent fits into your overall system

This file shows the complete integration flow and how data moves through the system.
"""

# ============================================================================
# ARCHITECTURE DIAGRAM
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SYSTEMS                               │
│  GitHub/GitLab Webhooks, CI/CD, Monitoring, Ticket Systems            │
└────────────┬────────────────────────────────────────────────────────────┘
             │
             │ PR/Incident Events
             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MASTER AGENT (agent_graph.py)                       │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ ROUTER NODE: Task Type Detection                                 │ │
│  │ - Checks task_type field                                        │ │
│  │ - Routes to appropriate specialized agent                       │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│           │                              │                            │
│      Incident Path                   PR Path                           │
│           │                              │                            │
│     ┌─────▼──────┐                ┌─────▼──────┐                      │
│     │Investigator│                │  PR Agent  │                      │
│     │   (Logs)   │                │ (Analysis) │                      │
│     └─────┬──────┘                └─────┬──────┘                      │
│           │                             │                             │
│     ┌─────▼──────┐                ┌─────▼──────┐                      │
│     │ Researcher │                │  Code Analyzer                    │
│     │   (Docs)   │                │  Conflict Checker                 │
│     └─────┬──────┘                │  Quality Assessor                 │
│           │                       └─────┬──────┘                      │
│     ┌─────▼──────┐                      │                             │
│     │   Analyst  │                      │                             │
│     │ (Diagnose) │                      │                             │
│     └─────┬──────┘                      │                             │
│           │                             │                             │
│     ┌─────▼──────┐                ┌─────▼──────┐                      │
│     │ Responder  │                │   Report   │                      │
│     │  (Action)  │                │ Generator  │                      │
│     └─────┬──────┘                └─────┬──────┘                      │
│           │                             │                             │
│           └────────────┬────────────────┘                             │
│                        │                                              │
│                  ┌─────▼──────┐                                       │
│                  │  Aggregate │                                       │
│                  │  Results   │                                       │
│                  └─────┬──────┘                                       │
│                        │                                              │
└────────────────────────┼──────────────────────────────────────────────┘
                         │
                    Structured
                    Response
                         ▼
             ┌──────────────────────┐
             │  Response Handler    │
             │  - Log results       │
             │  - Notify teams      │
             │  - Update tracking   │
             │  - Post comments     │
             └──────────────────────┘
"""

# ============================================================================
# DATA FLOW EXAMPLES
# ============================================================================

# EXAMPLE 1: PR Request Flow
print("="*80)
print("EXAMPLE 1: PR REQUEST FLOW")
print("="*80)

pr_request_flow = """
1. INCOMING DATA (from GitHub/API):
   {
     "event": "pull_request.opened",
     "pr": {
       "id": 1234,
       "title": "Add user authentication",
       "description": "Implements OAuth2...",
       "author": "alice_dev",
       "base": "main",
       "head": "develop",
       "files_changed": [...]
     }
   }

2. TRANSFORM TO MASTER AGENT STATE:
   {
     "task_id": "PR_1234",
     "task_type": "pr",
     "pr_request": {
       "task_type": "analyze",
       "pr_title": "Add user authentication",
       "pr_description": "Implements OAuth2...",
       "pr_author": "alice_dev",
       "base_branch": "main",
       "target_branch": "develop",
       "pr_files_changed": [...]
     }
   }

3. MASTER AGENT ROUTES:
   Router detects task_type == "pr"
   → Route to pr_agent node

4. PR AGENT PROCESSES:
   a) analyze_pr_code()
      - Evaluates code structure
      - Checks patterns and practices
      - Returns code quality findings

   b) check_pr_conflicts()
      - Analyzes potential merge conflicts
      - Checks for breaking changes
      - Returns conflict assessment

   c) assess_pr_quality()
      - Overall quality scoring
      - Risk level assignment
      - Generates recommendations

   d) generate_pr_report()
      - Synthesizes all findings
      - Creates structured response

5. RESPONSE GENERATED:
   {
     "status": "completed",
     "analysis": {
       "severity": "low",
       "findings": "Well-structured OAuth implementation",
       "recommendations": [
         "Add unit tests for token refresh",
         "Document OAuth flow",
         "Add security headers"
       ],
       "suggested_action": "approve"
     }
   }

6. OUTPUT HANDLING:
   Response can be:
   - Posted as PR comment on GitHub
   - Stored in tracking system
   - Sent to notification system
   - Logged for metrics/history
"""

print(pr_request_flow)

# ============================================================================
# INTEGRATION POINTS
# ============================================================================

print("\n" + "="*80)
print("INTEGRATION POINTS")
print("="*80)

integration_points = """
1. INPUT SOURCES:
   - GitHub/GitLab webhooks
   - REST API endpoints
   - CI/CD pipelines
   - Ticket systems
   - Direct agent calls

2. PROCESSING:
   - Master agent routes to appropriate specialist
   - Specialist agent processes task
   - Results aggregated in master agent state
   - Response formatted for downstream systems

3. OUTPUT DESTINATIONS:
   - Post comments on PRs
   - Update issue trackers
   - Send Slack/email notifications
   - Store in analytics database
   - Block/approve merges (if CI/CD integrated)
   - Feed to dashboards

4. FEEDBACK LOOPS:
   - Quality metrics collection
   - Agent performance tracking
   - Team feedback integration
   - Continuous improvement
"""

print(integration_points)

# ============================================================================
# COMPLETE WORKFLOW EXAMPLE
# ============================================================================

print("\n" + "="*80)
print("COMPLETE WORKFLOW: GitHub PR → Analysis → Comment → Merge Decision")
print("="*80)

workflow_example = """
STEP 1: GitHub PR Created
   User creates PR with:
   - Title: "Fix: Handle null in user service"
   - Description: "Addresses crash when email is missing"
   - Files: main.py (+25 lines), test.py (+40 lines)

STEP 2: Webhook Triggered
   GitHub sends POST to your endpoint with PR details

STEP 3: Transform & Submit to Master Agent
   transform_pr_to_agent_request(github_pr)
   → Master agent.invoke(request)

STEP 4: Agent Processing
   a) Router: Identifies task_type == "pr"
   b) Routes to: pr_agent node
   c) PR Agent pipeline:
      - Analyzes code for null handling
      - Checks for merge conflicts with main
      - Scores overall quality (8/10)
      - Generates recommendations
   d) Returns: Analysis with severity = "low"

STEP 5: Process Response
   if analysis['severity'] in ['high', 'critical']:
       block_merge()
   else:
       post_comment_on_pr(analysis)
       update_metrics()

STEP 6: Post GitHub Comment
   Comment posted with:
   - Findings summary
   - Recommendations
   - Link to detailed analysis
   - Suggested action

STEP 7: Developer Feedback
   Developer reviews comment
   - May request changes
   - May approve merge
   - May request manual review

STEP 8: Final Decision
   Team lead reviews + analysis
   → Merge or request changes
"""

print(workflow_example)

# ============================================================================
# CODE IMPLEMENTATION EXAMPLE
# ============================================================================

print("\n" + "="*80)
print("CODE: End-to-End Integration")
print("="*80)

implementation_code = """
# app.py - Your Flask/FastAPI application

from flask import Flask, request
from agent_graph import run_agent_on_pr, app as master_agent
import github

app = Flask(__name__)
gh = github.Github(os.getenv("GITHUB_TOKEN"))

@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    '''Handle GitHub PR webhook events'''
    
    payload = request.json
    
    # Only process PR events
    if payload['action'] not in ['opened', 'synchronize']:
        return {"status": "ignored"}
    
    pr = payload['pull_request']
    
    # Transform GitHub PR to agent request
    agent_pr = {
        "task_id": f"PR_{pr['id']}",
        "task_type": "analyze",
        "pr_title": pr['title'],
        "pr_description": pr['body'],
        "pr_author": pr['user']['login'],
        "base_branch": pr['base']['ref'],
        "target_branch": pr['head']['ref'],
        "pr_files_changed": fetch_pr_files(pr),
        "additional_context": f"Repo: {pr['repo']['full_name']}"
    }
    
    # Submit to master agent
    result = run_agent_on_pr(agent_pr)
    
    # Process result
    analysis = result.get('analysis', {})
    severity = analysis.get('severity', 'medium')
    
    # Post comment on GitHub
    github_pr = gh.get_user(pr['user']['login']).get_repo(
        pr['repo']['name']
    ).get_pull(pr['number'])
    
    comment = format_analysis_comment(analysis)
    github_pr.create_issue_comment(comment)
    
    # Log for metrics
    log_pr_analysis(pr['id'], analysis)
    
    # Block if critical
    if severity == 'critical':
        github_pr.create_review_comment(
            "PR blocked by automated analysis: Critical issues found"
        )
    
    return {"status": "processed", "severity": severity}

def fetch_pr_files(pr):
    '''Fetch file changes from GitHub PR'''
    files = []
    for file in pr.get('files', []):
        files.append({
            "filename": file['filename'],
            "changes": f"+{file['additions']} -{file['deletions']}",
            "additions": file['additions'],
            "deletions": file['deletions']
        })
    return files

def format_analysis_comment(analysis):
    '''Format analysis result as GitHub comment'''
    comment = f\"\"\"
    # 🤖 Automated PR Analysis
    
    **Severity:** {analysis['severity'].upper()}
    **Findings:** {analysis['findings']}
    
    ## Recommendations
    {chr(10).join(f"- {rec}" for rec in analysis['recommendations'])}
    
    **Suggested Action:** {analysis['suggested_action'].upper()}
    \"\"\"
    return comment

if __name__ == '__main__':
    app.run(debug=True)
"""

print(implementation_code)

# ============================================================================
# DEPLOYMENT CHECKLIST
# ============================================================================

print("\n" + "="*80)
print("DEPLOYMENT CHECKLIST")
print("="*80)

checklist = """
✓ Files Setup
  □ pr_agent.py created and tested
  □ agent_graph.py updated with PR agent integration
  □ agent_tools.py extended with PR tools
  □ Documentation (PR_AGENT_GUIDE.md) reviewed

✓ Configuration
  □ GROQ_API_KEY set in .env
  □ LLM model configured
  □ Input validation added

✓ Testing
  □ Run: python agent_graph.py (test routing)
  □ Run: python pr_agent_examples.py (test all scenarios)
  □ Test error handling for invalid inputs
  □ Test with real PRs from your repository

✓ Integration
  □ Choose webhook platform (GitHub/GitLab)
  □ Set up webhook endpoint
  □ Implement response handler
  □ Add PR comment formatting
  □ Test end-to-end flow

✓ Monitoring
  □ Add logging for all PR analyses
  □ Track performance metrics
  □ Monitor LLM token usage
  □ Alert on critical findings

✓ Production
  □ Set up error handling
  □ Implement rate limiting
  □ Add authentication to webhook
  □ Deploy to production environment
  □ Configure backups/rollback plan
"""

print(checklist)

# ============================================================================
# NEXT STEPS
# ============================================================================

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)

next_steps = """
1. TEST LOCALLY:
   python agent_graph.py              # Test routing
   python pr_agent_examples.py        # Test scenarios

2. SET UP WEBHOOK:
   - Create GitHub/GitLab webhook
   - Configure to POST to your endpoint
   - Test with sample PR event

3. IMPLEMENT HANDLER:
   - Create Flask/FastAPI route
   - Transform webhook payload
   - Call run_agent_on_pr()
   - Post result as comment

4. DEPLOY:
   - Push code to repository
   - Configure production environment
   - Set up monitoring
   - Enable webhook

5. ITERATE:
   - Collect feedback
   - Tune LLM prompts
   - Add custom rules
   - Improve analysis quality
"""

print(next_steps)

print("\n" + "="*80)
print("Your PR Agent is ready to integrate!")
print("="*80)
