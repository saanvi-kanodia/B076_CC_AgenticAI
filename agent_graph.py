import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from agent_tools import fetch_merchant_logs, search_documentation, check_platform_health
from pr_agent import process_pr_task, PRAnalysisRequest
from typing import TypedDict, List, Optional

# Load environment variables from .env file
load_dotenv()

# --- SETUP ---
# Initialize LLM - Using Groq Kimi K2 model
# Make sure to set GROQ_API_KEY environment variable
llm = ChatGroq(
    model="moonshotai/kimi-k2-instruct-0905",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

# Define State (same as above)
class AgentState(TypedDict):
    # Inputs
    incident_id: str
    symptom_description: str
    affected_merchants: List[str]
    task_type: str  # 'incident', 'pr', etc.
    
    # PR-specific inputs
    pr_request: Optional[dict] = None
    
    # Internal Memory (The Clipboard)
    logs_data: str              # Evidence found by Investigator
    docs_data: str              # Knowledge found by Researcher
    root_cause_analysis: str    # Thoughts from Orchestrator
    
    # PR Agent output
    pr_analysis_result: Optional[dict] = None
    
    # Outputs
    proposed_action: str        # What we want to do
    draft_response: str         # The email/ticket content
    confidence_score: float     # 0.0 to 1.0
    
    # Message History (for the LLM context)
    messages: List[str]

# --- NODES (The Agents) ---

def node_investigator(state: AgentState):
    """Worker 1: Looks at logs"""
    print("🕵️ INVESTIGATOR: Analyzing logs...")
    
    # Logic: If merchants are provided, check their logs.
    if state.get('affected_merchants'):
        tool_result = fetch_merchant_logs.invoke({"merchant_ids": state['affected_merchants']})
        return {"logs_data": tool_result}
    return {"logs_data": "No specific merchant data provided."}

def node_researcher(state: AgentState):
    """Worker 2: Looks at docs based on log findings"""
    print("📚 RESEARCHER: Checking documentation...")
    
    logs = state.get('logs_data', "")
    symptom = state.get('symptom_description', "")
    
    # Dynamic Query Generation using LLM
    query_prompt = f"Based on error logs: '{logs[:200]}' and symptom: '{symptom}', what should I search in the docs?"
    search_query = llm.invoke(query_prompt).content
    
    # Clean up query (LLM might be chatty)
    search_result = search_documentation.invoke({"query": search_query})
    return {"docs_data": search_result}

def node_analyst(state: AgentState):
    """The Brain: Synthesizes Logs + Docs into a Diagnosis"""
    print("🧠 ANALYST: Reasoning about root cause (structured)...")

    # Include platform health check to avoid assuming platform outage
    try:
        platform_status = check_platform_health.invoke({})
    except Exception:
        platform_status = "Platform status unknown"

    prompt = f"""
You are a Senior DevOps Engineer analyzing a support incident. The incident has been pre-analyzed using ML classification.

ML CLASSIFICATION RESULTS:
- ML Category: {state.get('ml_category', 'unknown')}
- ML Confidence: {state.get('category_confidence', 0):.2f}
- Category Distribution: {state.get('category_distribution', {})}
- Technical Indicators: {state.get('technical_indicators', {})}
- Error Patterns: {state.get('error_patterns', [])}

INCI

DENT DETAILS:
- Symptoms: {state.get('symptom_description', 'No symptoms provided')}
- Affected Merchants: {len(state.get('affected_merchants', []))} merchants
- Ticket Count: {state.get('ticket_count', 'Unknown')}
- Priority: {state.get('priority_level', 'Unknown')}

EVIDENCE:
- Error Logs: {state.get('logs_data', 'No logs available')}
- Documentation: {state.get('docs_data', 'No docs found')}
- Platform Status: {platform_status}

ANALYSIS INSTRUCTIONS:
1. **Trust the ML classification** - it's trained on patterns and has {state.get('category_confidence', 0):.1%} confidence
2. Use the technical indicators and error patterns as primary evidence
3. Assign probabilities based on ML confidence:
   - If ML confidence > 0.8: Give ML category 80-90% probability
   - If ML confidence 0.6-0.8: Give ML category 60-80% probability  
   - If ML confidence < 0.6: Distribute more evenly but still favor ML category

Evaluate THREE hypotheses and assign probabilities that sum to 100%:
A) User Error (wrong schema, bad API key, misconfiguration, incorrect usage)
B) Platform Bug (system outage, DB issues, deployment problems, service failures)  
C) Documentation Gap (missing docs, outdated examples, unclear instructions)

REQUIRED JSON FORMAT:
{{
  "probabilities": {{"user_error": 20, "platform_bug": 75, "docs_gap": 5}},
  "evidence": ["ML detected platform error patterns", "Multiple merchants affected"],
  "diagnosis": "platform_bug",
  "explanation": "ML classification shows high confidence platform issue with supporting evidence",
  "recommended_action": "escalate to engineering team"
}}

Respond with ONLY valid JSON. Use ML insights as your primary evidence source."""

    response = llm.invoke(prompt)

    # Try to use structured JSON if available, otherwise fall back to raw text
    root_cause = response.content
    confidence_score = 0.0
    
    # Try to parse JSON and extract confidence from probabilities
    try:
        import json
        if root_cause.strip().startswith('{'):
            parsed_analysis = json.loads(root_cause)
            if 'probabilities' in parsed_analysis:
                probs = parsed_analysis['probabilities']
                # Confidence is the highest probability among the three hypotheses
                max_prob = max(
                    probs.get('user_error', 0),
                    probs.get('platform_bug', 0), 
                    probs.get('docs_gap', 0)
                )
                confidence_score = max_prob / 100.0  # Convert percentage to 0.0-1.0
                print(f"📊 Calculated confidence: {confidence_score:.1%} (max prob: {max_prob}%)")
    except Exception as e:
        print(f"⚠️ Could not parse confidence from analysis: {e}")
        # Fallback: estimate confidence from content analysis
        if any(word in root_cause.lower() for word in ['clear', 'obvious', 'definitely', 'certainly']):
            confidence_score = 0.9
        elif any(word in root_cause.lower() for word in ['likely', 'probably', 'appears']):
            confidence_score = 0.7
        elif any(word in root_cause.lower() for word in ['possible', 'might', 'unclear']):
            confidence_score = 0.5
        else:
            confidence_score = 0.6  # Default reasonable confidence
    
    return {
        "root_cause_analysis": root_cause,
        "confidence_score": confidence_score
    }

def node_responder(state: AgentState):
    """The Writer: Drafts the action"""
    print("✍️ RESPONDER: Drafting response...")
    
    prompt = f"""
    Based on the diagnosis: "{state.get('root_cause_analysis', '')}"
    
    Draft a response to the merchant.
    - If user error: Be polite, point to the docs, provide a JSON snippet fix.
    - If platform error: Apologize, say we are fixing it.
    
    Format: JSON with keys 'action_type' (reply/escalate) and 'message_body'.
    """
    response = llm.invoke(prompt)
    return {"draft_response": response.content}

def node_pr_agent(state: AgentState):
    """Specialized Agent: Handles Pull Request analysis tasks"""
    print("🔀 PR_AGENT: Processing PR request...")
    
    if not state.get('pr_request'):
        return {"pr_analysis_result": {"status": "error", "error": "No PR request provided"}}
    
    try:
        # Convert dict to PRAnalysisRequest if needed
        pr_data = state['pr_request']
        if isinstance(pr_data, dict):
            pr_request = PRAnalysisRequest(
                task_type=pr_data.get('task_type', 'analyze'),
                pr_title=pr_data.get('pr_title', ''),
                pr_description=pr_data.get('pr_description', ''),
                pr_files_changed=pr_data.get('pr_files_changed', []),
                pr_author=pr_data.get('pr_author', ''),
                base_branch=pr_data.get('base_branch', 'main'),
                target_branch=pr_data.get('target_branch', 'develop'),
                additional_context=pr_data.get('additional_context')
            )
        else:
            pr_request = pr_data
        
        # Process the PR task
        task_id = state.get('incident_id', 'PR_TASK_AUTO')
        result = process_pr_task(task_id, pr_request)
        
        return {"pr_analysis_result": result}
    except Exception as e:
        print(f"❌ PR_AGENT Error: {str(e)}")
        return {"pr_analysis_result": {"status": "error", "error": str(e)}}

def router_by_task_type(state: AgentState) -> str:
    """
    Routes to appropriate agent based on task type.
    Returns node name to execute next.
    """
    task_type = state.get('task_type', 'incident').lower()
    
    if task_type == 'pr':
        return "pr_agent"
    else:
        return "investigator"

# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("investigator", node_investigator)
workflow.add_node("researcher", node_researcher)
workflow.add_node("analyst", node_analyst)
workflow.add_node("responder", node_responder)
workflow.add_node("pr_agent", node_pr_agent)

# Define Entry Point (Router)
# Start -> Route to appropriate agent based on task type
workflow.set_entry_point("router")

# Add conditional routing
def router_node(state):
    task_type = state.get('task_type', 'incident').lower()
    if task_type == 'pr':
        return "pr_agent"
    else:
        return "investigator"

workflow.add_node("router", lambda state: {"_routing_done": True})

# Define Edges (The Flow)
# For incident handling path
workflow.add_edge("investigator", "researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "responder")
workflow.add_edge("responder", END)

# For PR handling path
workflow.add_edge("pr_agent", END)

# Router should be able to send to the appropriate starting node
workflow.add_conditional_edges("router", router_by_task_type, path_map=["investigator", "pr_agent"])

# Compile
app = workflow.compile()

# --- TEST FUNCTION ---
def run_agent_on_incident(incident_data):
    initial_state = {
        "incident_id": incident_data['incident_id'],
        "symptom_description": incident_data.get('summary', ''),
        "affected_merchants": incident_data['affected_merchants'],
        "task_type": "incident",
        "pr_request": None,
        "logs_data": "",
        "docs_data": "",
        "root_cause_analysis": "",
        "draft_response": "",
        "proposed_action": "",
        "confidence_score": 0.0,
        "messages": [],
        "pr_analysis_result": None,
        
        # ML Classification Data
        "ml_category": incident_data.get('ml_category', 'unknown'),
        "category_confidence": incident_data.get('category_confidence', 0.0),
        "category_distribution": incident_data.get('category_distribution', {}),
        "technical_indicators": incident_data.get('technical_indicators', {}),
        "error_patterns": incident_data.get('error_patterns', []),
        "ticket_count": incident_data.get('ticket_count', 0),
        "priority_level": incident_data.get('priority_level', 'Unknown')
    }
    
    result = app.invoke(initial_state)
    return result

def run_agent_on_pr(pr_data):
    """Process a Pull Request through the PR agent"""
    initial_state = {
        "incident_id": pr_data.get('task_id', 'PR_TASK_AUTO'),
        "symptom_description": "",
        "affected_merchants": [],
        "task_type": "pr",
        "pr_request": pr_data,
        "logs_data": "",
        "docs_data": "",
        "root_cause_analysis": "",
        "draft_response": "",
        "proposed_action": "",
        "confidence_score": 0.0,
        "messages": [],
        "pr_analysis_result": None
    }
    
    result = app.invoke(initial_state)
    return result

# Mock run
if __name__ == "__main__":
    # Load all real incidents from clustering output
    import json
    with open("dataset/active_incidents.json", "r") as f:
        incidents = json.load(f)
    print(f"\n🚦 Running agent on {len(incidents)} detected incidents...\n")
    for incident in incidents:
        print(f"\n--- Processing {incident['incident_id']} ---")
        final_output = run_agent_on_incident(incident)
        print(f"DIAGNOSIS: {final_output.get('root_cause_analysis', 'N/A')}")
        print(f"RESPONSE: {final_output.get('draft_response', 'N/A')}")