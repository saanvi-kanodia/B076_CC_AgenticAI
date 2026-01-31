# PR Agent Integration Guide

## Overview

The **PR Agent** is a specialized worker in the master agent system designed to handle Pull Request analysis and review tasks. It leverages OpenCode.ai integration to analyze code quality, detect conflicts, and provide actionable recommendations.

## Architecture

```
┌─────────────────────────────────────────────────┐
│          MASTER AGENT (agent_graph.py)          │
│  - Routes tasks by type                         │
│  - Coordinates specialized agents               │
└─────────────┬───────────────────────────────────┘
              │
       ┌──────┴──────┬────────────────────┐
       │             │                    │
  Incident Path    PR Path          (More agents...)
       │             │
    ┌──┴──┐      ┌───▼────┐
    │     │      │ PR_AGENT│
    └─────┘      └────┬────┘
                      │
              ┌───────┴───────┐
              │               │
         ┌────▼──────┐  ┌────▼─────┐
         │   Analyze │  │  Conflict │
         │   Code    │  │   Check   │
         └───────────┘  └───────────┘
```

## Components

### 1. PR Agent (`pr_agent.py`)

The standalone PR agent module with the following key functions:

#### Main Entry Point
```python
process_pr_task(task_id: str, pr_request: PRAnalysisRequest) -> dict
```
- Called by the master agent to process PR requests
- Returns analysis results with recommendations

#### Analysis Nodes

1. **analyze_pr_code()** - Code quality and pattern analysis
2. **check_pr_conflicts()** - Merge conflict and compatibility detection
3. **assess_pr_quality()** - Overall quality scoring and recommendations
4. **generate_pr_report()** - Synthesizes findings into structured response

#### Data Models

**PRAnalysisRequest:**
```python
{
    "task_type": "analyze",
    "pr_title": str,
    "pr_description": str,
    "pr_files_changed": [
        {
            "filename": str,
            "changes": str,
            "additions": int,
            "deletions": int
        }
    ],
    "pr_author": str,
    "base_branch": str,
    "target_branch": str,
    "additional_context": Optional[str]
}
```

**PRAnalysisResponse:**
```python
{
    "status": "success|error",
    "analysis_type": str,
    "findings": str,
    "severity": "low|medium|high|critical",
    "recommendations": [str],
    "action_required": bool,
    "suggested_action": "approve|request_changes|reject"
}
```

### 2. Master Agent Integration (`agent_graph.py`)

The master agent has been enhanced with:

- **Router Node** - Directs tasks to appropriate agent
- **PR Agent Node** - Orchestrates PR analysis
- **State Expansion** - Added PR-related fields to AgentState

#### Key Functions for Master Agent

```python
run_agent_on_pr(pr_data: dict) -> dict
```
Submit a PR for analysis through the master agent.

```python
run_agent_on_incident(incident_data: dict) -> dict
```
Existing incident processing (unchanged).

## Usage

### From Master Agent

```python
from agent_graph import run_agent_on_pr

# Prepare PR data
pr_request = {
    "task_id": "PR_001",
    "task_type": "analyze",
    "pr_title": "Add user authentication",
    "pr_description": "Implements OAuth2 authentication",
    "pr_files_changed": [
        {
            "filename": "src/auth/oauth.py",
            "changes": "New OAuth implementation",
            "additions": 150,
            "deletions": 0
        },
        {
            "filename": "tests/test_auth.py",
            "changes": "Added OAuth tests",
            "additions": 80,
            "deletions": 0
        }
    ],
    "pr_author": "john_dev",
    "base_branch": "main",
    "target_branch": "develop",
    "additional_context": "Implements feature #456"
}

# Process through master agent
result = run_agent_on_pr(pr_request)

# Access results
print(result['status'])
print(result['analysis']['severity'])
print(result['analysis']['recommendations'])
```

### Direct PR Agent Usage

```python
from pr_agent import process_pr_task, PRAnalysisRequest

# Create request object
pr_request = PRAnalysisRequest(
    task_type="analyze",
    pr_title="Fix database connection pool leak",
    pr_description="Closes connections properly on error",
    pr_files_changed=[...],
    pr_author="alice_dev",
    base_branch="main",
    target_branch="develop"
)

# Process directly
result = process_pr_task("PR_002", pr_request)
```

## Features

### Code Analysis
- Complexity assessment
- Code quality evaluation
- Best practices adherence
- Performance implications

### Conflict Detection
- Merge conflict prediction
- Breaking changes identification
- Version compatibility issues
- Dependency conflicts

### Quality Metrics
- Code quality scoring (1-10)
- Risk assessment
- Security considerations
- Test coverage evaluation

### Recommendations
- Specific, actionable suggestions
- Automated best practices
- Security improvements
- Performance optimization tips

## Integration with Master Agent

The PR Agent integrates seamlessly:

1. **Task Routing**: Master agent routes "pr" task_type to PR Agent
2. **State Management**: PR-specific data flows through AgentState
3. **Result Aggregation**: PR analysis results stored in pr_analysis_result field
4. **Response Format**: Consistent with master agent response patterns

## Example Workflow

```
1. Master Agent receives PR task
   ↓
2. Router identifies task_type == "pr"
   ↓
3. PR Agent Node invoked
   ↓
4. PR Agent processes:
   - Code Analysis
   - Conflict Check
   - Quality Assessment
   - Report Generation
   ↓
5. Results returned to Master Agent
   ↓
6. Master Agent can:
   - Log findings
   - Notify developers
   - Block/allow merge
   - Generate feedback
```

## Response Format

```json
{
  "task_id": "PR_001",
  "status": "completed",
  "analysis": {
    "status": "success",
    "analysis_type": "comprehensive",
    "findings": "Code is well-structured with proper error handling",
    "severity": "low",
    "recommendations": [
      "Add unit tests for edge cases",
      "Document the OAuth flow",
      "Consider adding rate limiting"
    ],
    "action_required": false,
    "suggested_action": "approve"
  },
  "error": null
}
```

## Testing

Run the demo to test both incident and PR processing:

```bash
python agent_graph.py
```

This will:
1. Process sample incidents (if data available)
2. Analyze a sample PR with the PR Agent
3. Display findings and recommendations

## Extension Points

To customize PR analysis:

1. **Modify LLM Prompts**: Edit prompt templates in pr_agent.py
2. **Add Custom Tools**: Create new analysis functions
3. **Extend Checks**: Add more analysis nodes in the workflow
4. **Custom Metrics**: Define domain-specific quality metrics

## Performance Considerations

- **LLM Calls**: 4-5 invocations per PR (code, conflicts, quality, report)
- **Processing Time**: ~10-30 seconds depending on file changes
- **Token Usage**: ~2000-5000 tokens per PR analysis
- **Scalability**: Can handle 100+ PRs/hour with proper batching

## Error Handling

The PR Agent handles:
- Missing PR data gracefully
- LLM response parsing failures
- Invalid state transitions
- Missing required fields

All errors are captured in the response:
```json
{
  "status": "error",
  "error": "Error message here"
}
```

## Future Enhancements

- Integration with GitHub/GitLab APIs
- Automated code review posting
- Team-specific analysis rules
- Historical trend analysis
- ML-based approval prediction
