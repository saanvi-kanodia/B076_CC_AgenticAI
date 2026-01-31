"""
Example: How to use the PR Agent with the Master Agent

This file demonstrates different ways to interact with the PR Agent
through the master agent system.
"""

from agent_graph import run_agent_on_pr
import json

# Example 1: Simple PR Analysis
print("="*80)
print("EXAMPLE 1: Simple PR Analysis")
print("="*80)

simple_pr = {
    "task_id": "PR_EXAMPLE_001",
    "task_type": "analyze",
    "pr_title": "Add user profile endpoint",
    "pr_description": "Adds a new GET /users/{id}/profile endpoint with caching",
    "pr_files_changed": [
        {
            "filename": "src/api/users.py",
            "changes": "Added profile endpoint",
            "additions": 45,
            "deletions": 5
        },
        {
            "filename": "tests/api/test_users.py",
            "changes": "Added profile endpoint tests",
            "additions": 60,
            "deletions": 0
        }
    ],
    "pr_author": "alice_dev",
    "base_branch": "main",
    "target_branch": "develop"
}

result = run_agent_on_pr(simple_pr)
print("\nResult:")
print(json.dumps(result, indent=2, default=str))

# Example 2: Complex PR with Breaking Changes
print("\n\n" + "="*80)
print("EXAMPLE 2: Complex PR with Breaking Changes")
print("="*80)

complex_pr = {
    "task_id": "PR_EXAMPLE_002",
    "task_type": "analyze",
    "pr_title": "BREAKING: Migrate from REST to GraphQL API",
    "pr_description": """
    This is a major refactor migrating from REST to GraphQL.
    - All REST endpoints deprecated
    - New GraphQL endpoint at /graphql
    - Migration guide included in docs
    - Old endpoints maintained for 6 months with deprecation warnings
    """,
    "pr_files_changed": [
        {"filename": "src/api/graphql/schema.py", "changes": "GraphQL schema", "additions": 200, "deletions": 0},
        {"filename": "src/api/graphql/resolvers.py", "changes": "GraphQL resolvers", "additions": 150, "deletions": 0},
        {"filename": "src/api/rest_deprecated.py", "changes": "Deprecated REST API", "additions": 20, "deletions": 100},
        {"filename": "docs/migration_guide.md", "changes": "Migration guide", "additions": 80, "deletions": 0},
        {"filename": "tests/api/test_graphql.py", "changes": "GraphQL tests", "additions": 120, "deletions": 0},
    ],
    "pr_author": "bob_architect",
    "base_branch": "main",
    "target_branch": "develop",
    "additional_context": "Implements design proposal #789. Requires security review."
}

result = run_agent_on_pr(complex_pr)
print("\nResult:")
print(json.dumps(result, indent=2, default=str))

# Example 3: Security-focused PR
print("\n\n" + "="*80)
print("EXAMPLE 3: Security Enhancement PR")
print("="*80)

security_pr = {
    "task_id": "PR_EXAMPLE_003",
    "task_type": "analyze",
    "pr_title": "Security: Add rate limiting and input validation",
    "pr_description": """
    Addresses security vulnerabilities by implementing:
    - Rate limiting on all API endpoints
    - Input validation and sanitization
    - CORS configuration hardening
    - Security headers (HSTS, CSP, X-Frame-Options)
    """,
    "pr_files_changed": [
        {"filename": "src/middleware/rate_limiter.py", "changes": "Rate limiter", "additions": 60, "deletions": 0},
        {"filename": "src/middleware/validators.py", "changes": "Input validation", "additions": 80, "deletions": 10},
        {"filename": "src/config/security.py", "changes": "Security config", "additions": 30, "deletions": 5},
        {"filename": "tests/security/test_rate_limiting.py", "changes": "Security tests", "additions": 100, "deletions": 0},
    ],
    "pr_author": "security_team",
    "base_branch": "main",
    "target_branch": "develop",
    "additional_context": "Fixes security issues #234, #235, #236. Requires security review before merge."
}

result = run_agent_on_pr(security_pr)
print("\nResult:")
print(json.dumps(result, indent=2, default=str))

# Example 4: Batch Processing Multiple PRs
print("\n\n" + "="*80)
print("EXAMPLE 4: Batch Processing Multiple PRs")
print("="*80)

prs = [
    {
        "task_id": "PR_BATCH_001",
        "task_type": "analyze",
        "pr_title": "Fix: Database connection timeout",
        "pr_description": "Increases connection pool timeout and adds retry logic",
        "pr_files_changed": [
            {"filename": "src/db/pool.py", "changes": "Connection pool", "additions": 25, "deletions": 10}
        ],
        "pr_author": "devops_team",
        "base_branch": "main",
        "target_branch": "develop"
    },
    {
        "task_id": "PR_BATCH_002",
        "task_type": "analyze",
        "pr_title": "Refactor: Extract utility functions",
        "pr_description": "Extracts common utility functions to reduce code duplication",
        "pr_files_changed": [
            {"filename": "src/utils/common.py", "changes": "New utils", "additions": 100, "deletions": 0},
            {"filename": "src/core/logic.py", "changes": "Uses new utils", "additions": 10, "deletions": 50}
        ],
        "pr_author": "code_quality_team",
        "base_branch": "main",
        "target_branch": "develop"
    }
]

print(f"\nProcessing {len(prs)} PRs...\n")
for pr in prs:
    print(f"Processing {pr['task_id']}: {pr['pr_title']}")
    result = run_agent_on_pr(pr)
    status = result.get('status')
    analysis = result.get('analysis', {})
    severity = analysis.get('severity', 'unknown')
    action = analysis.get('suggested_action', 'unknown')
    print(f"  → Status: {status} | Severity: {severity} | Action: {action}\n")

# Example 5: Direct PR Agent Usage (without master agent)
print("\n" + "="*80)
print("EXAMPLE 5: Direct PR Agent Usage (Optional)")
print("="*80)

print("""
You can also use the PR Agent directly without going through the master agent:

from pr_agent import process_pr_task, PRAnalysisRequest

pr_request = PRAnalysisRequest(
    task_type="analyze",
    pr_title="Add caching layer",
    pr_description="Adds Redis caching",
    pr_files_changed=[...],
    pr_author="cache_team",
    base_branch="main",
    target_branch="develop"
)

result = process_pr_task("PR_DIRECT_001", pr_request)
print(result)
""")

print("\n" + "="*80)
print("Examples completed!")
print("="*80)
