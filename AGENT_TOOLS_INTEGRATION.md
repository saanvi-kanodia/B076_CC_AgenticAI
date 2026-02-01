# Agent Tools Integration Summary

## Overview

This document outlines all tools available to the multi-agent system and how they're integrated into the agent workflow.

---

## Available Agent Tools

### 1. **fetch_merchant_logs**

- **Location**: `agent_tools.py`
- **Purpose**: Retrieves log data for specified merchants from logs.json
- **Used By**: Investigator Agent (node_investigator)
- **Parameters**:
  - `merchant_ids`: List of merchant IDs to fetch logs for
- **Integration**: Called directly in investigator node to gather initial data
- **Example**:
  ```python
  tool_result = fetch_merchant_logs.invoke({"merchant_ids": merchant_sample})
  ```

### 2. **search_documentation**

- **Location**: `agent_tools.py`
- **Purpose**: Semantic search across api_docs.md using RAG (MiniRAG)
- **Used By**: Researcher Agent (node_researcher)
- **Parameters**:
  - `query`: Search query for documentation
  - `top_k`: Number of results to return (default: 3)
- **Integration**: Called in researcher node with smart query generation
- **Example**:
  ```python
  doc_results = search_documentation.invoke({"query": search_query, "top_k": 3})
  ```

### 3. **check_platform_health**

- **Location**: `agent_tools.py`
- **Purpose**: Simulates platform health monitoring (currently returns mock data)
- **Used By**: Available but not actively used in current workflow
- **Parameters**: None
- **Integration**: Can be called by any agent for system status
- **Example**:
  ```python
  health = check_platform_health.invoke({})
  ```

### 4. **create_documentation_pr** ⭐ NEW

- **Location**: `agent_tools.py`
- **Purpose**: Automatically creates GitHub PR to update api_docs.md when documentation gaps are detected
- **Used By**: Responder Agent (node_responder)
- **Parameters**:
  - `incident_summary`: Summary of the incident and investigation findings
  - `gap_reasoning`: Explanation of why documentation improvement is needed
- **Integration**:
  - **Automatic Trigger**: When agent detects documentation gaps (docs_gap diagnosis OR docs_gap_prob >= 30%)
  - **Cross-Merchant Trigger**: When ≥3 merchants affected with confidence < 80%
- **Example**:
  ```python
  pr_result = create_documentation_pr.invoke({
      "incident_summary": "Incident details...",
      "gap_reasoning": "Documentation improvement needed because..."
  })
  ```

---

## Agent Workflow Integration

### Flow: Investigator → Researcher → Analyst → Responder

```
┌─────────────────┐
│  INVESTIGATOR   │ → Uses: fetch_merchant_logs()
│  (Data Gatherer)│    Collects merchant log data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   RESEARCHER    │ → Uses: search_documentation()
│  (Doc Explorer) │    Searches API docs with semantic RAG
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    ANALYST      │ → No tools (pure analysis)
│ (Root Cause)    │    Analyzes data + ML predictions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   RESPONDER     │ → Uses: create_documentation_pr() ⭐
│ (Draft Action)  │    Automatically creates PRs for doc gaps
└─────────────────┘
```

---

## Automatic PR Creation Logic

The Responder agent intelligently decides when to create documentation PRs:

### Trigger Conditions:

1. **Documentation Gap Diagnosis**
   - If `diagnosis == "docs_gap"` in root cause analysis
   - If `docs_gap_prob >= 30%` in probabilities

2. **Cross-Merchant Pattern**
   - If ≥3 merchants affected
   - AND confidence < 80%
   - Suggests systemic documentation issue

### Decision Flow:

```python
if diagnosis == 'docs_gap' or docs_gap_prob >= 30:
    create_pr = True
    reason = "Documentation gap detected in diagnosis"
elif len(affected_merchants) >= 3 and confidence < 0.8:
    create_pr = True
    reason = "Cross-merchant pattern suggests doc improvements needed"
```

---

## PR Workflow Behind the Scenes

When `create_documentation_pr()` is called:

1. **Analyze Gaps**: Scans active_incidents.json for patterns
2. **Generate Improvements**: Uses LLM to draft documentation updates
3. **Create GitHub PR**:
   - Creates new branch: `docs-improvement-{timestamp}`
   - Updates api_docs.md with improvements
   - Commits changes
   - Opens PR with detailed description
4. **Returns Result**: PR URL and status

---

## UI Integration Points

### Manual PR Creation (UI):

- **Sidebar Button**: "🤖 Create Documentation PR"
- **Full Pipeline Step 3/3**: Automatic after investigation completes

### Autonomous PR Creation (Agent):

- **During Investigation**: Responder agent automatically decides
- **No User Intervention**: Agent creates PR based on evidence
- **Logged**: Console output shows PR creation decision

---

## Tool Availability Verification

### All Tools Properly Registered:

✅ Imported in agent_graph.py:

```python
from agent_tools import (
    fetch_merchant_logs,
    search_documentation,
    check_platform_health,
    create_documentation_pr
)
```

✅ Decorated with @tool in agent_tools.py:

```python
@tool
def fetch_merchant_logs(merchant_ids: List[str]) -> str:
    ...

@tool
def search_documentation(query: str, top_k: int = 3) -> str:
    ...

@tool
def check_platform_health() -> str:
    ...

@tool
def create_documentation_pr(incident_summary: str, gap_reasoning: str) -> str:
    ...
```

---

## Benefits of Agent-Level PR Automation

### 🎯 Intelligence:

- Agent decides WHEN documentation needs updating
- Based on evidence, not just rules

### ⚡ Speed:

- No human intervention needed for obvious gaps
- PRs created during investigation, not after

### 📊 Context-Aware:

- PR includes full incident context
- Gap reasoning from AI analysis
- Cross-merchant patterns automatically detected

### 🔄 Self-Improving System:

- Documentation evolves with incident patterns
- Reduces future similar incidents
- Creates feedback loop

---

## Future Enhancements

### Potential Tool Additions:

1. **alert_engineering_team()**
   - Trigger PagerDuty/Slack for critical issues
   - Used by Responder when confidence < 50%

2. **query_database()**
   - Direct database queries for deeper investigation
   - Used by Investigator for complex data needs

3. **rollback_deployment()**
   - Automatic rollback for platform bugs
   - Used by Responder with high confidence platform issues

4. **update_monitoring_rules()**
   - Add new monitoring based on incident patterns
   - Used by Analyst after pattern detection

---

## Testing Recommendations

### Verify Agent Tool Usage:

```bash
# Run agent on incident with documentation gap
streamlit run sample_UI.py

# Check console for:
# "📝 RESPONDER: Documentation gap detected, creating PR..."
# "✅ PR Creation Result: {pr_url}"
```

### Manual Tool Testing:

```python
from agent_tools import create_documentation_pr

result = create_documentation_pr.invoke({
    "incident_summary": "Test incident with CORS issues across 5 merchants",
    "gap_reasoning": "CORS documentation lacks whitelist configuration examples"
})
print(result)
```

---

## Summary

✅ **4 Agent Tools Available**: fetch_merchant_logs, search_documentation, check_platform_health, create_documentation_pr

✅ **All Tools Properly Registered**: @tool decorated and imported

✅ **Smart Integration**: Each agent has access to tools it needs

✅ **Autonomous PR Creation**: Agent decides when to update docs

✅ **No Bottlenecks**: Tools work independently without blocking

---

## Questions? Issues?

- Check `agent_tools.py` for tool implementations
- Check `agent_graph.py` for agent integrations
- Check console logs for tool execution traces
- Check GitHub for created PRs

**Last Updated**: Agent enhancement with autonomous PR creation capability
