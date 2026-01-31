import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from agent_tools import fetch_merchant_logs, search_documentation, check_platform_health
from typing import TypedDict, List

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
    
    # Internal Memory (The Clipboard)
    logs_data: str              # Evidence found by Investigator
    docs_data: str              # Knowledge found by Researcher
    root_cause_analysis: str    # Thoughts from Orchestrator
    
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
    print("🧠 ANALYST: Reasoning about root cause...")
    
    prompt = f"""
    You are a Senior DevOps Engineer. 
    
    1. SYMPTOMS: {state.get('symptom_description', '')}
    2. EVIDENCE (LOGS): {state.get('logs_data', '')}
    3. GROUND TRUTH (DOCS): {state.get('docs_data', '')}
    
    Task: Determine the root cause.
    - Is it a User Error? (e.g., using old schema, wrong API key)
    - Is it a Platform Bug? (e.g., 500 errors, database down)
    - Is it a Documentation Gap?
    
    Output ONLY the diagnosis and a brief explanation.
    """
    response = llm.invoke(prompt)
    return {"root_cause_analysis": response.content}

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

# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("investigator", node_investigator)
workflow.add_node("researcher", node_researcher)
workflow.add_node("analyst", node_analyst)
workflow.add_node("responder", node_responder)

# Define Edges (The Flow)
# Start -> Investigator -> Researcher -> Analyst -> Responder -> End
workflow.set_entry_point("investigator")
workflow.add_edge("investigator", "researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "responder")
workflow.add_edge("responder", END)

# Compile
app = workflow.compile()

# --- TEST FUNCTION ---
def run_agent_on_incident(incident_data):
    initial_state = {
        "incident_id": incident_data['incident_id'],
        "symptom_description": incident_data['summary'],
        "affected_merchants": incident_data['affected_merchants'],
        "logs_data": "",
        "docs_data": "",
        "root_cause_analysis": "",
        "draft_response": "",
        "proposed_action": "",
        "confidence_score": 0.0,
        "messages": []
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