
# agent_tools.py
import json
import importlib.util
import sys
import numpy as np
from langchain_core.tools import tool

@tool
def run_ticket_clustering():
    """
    Runs the clustering model to detect active incidents from tickets.json.
    Returns the list of detected incidents.
    NOTE: To use real-time triage, ensure your clustering output includes 'centroid' for each incident.
    """
    spec = importlib.util.spec_from_file_location("models", "models.py")
    models = importlib.util.module_from_spec(spec)
    sys.modules["models"] = models
    spec.loader.exec_module(models)
    clusterer = models.TicketClusterer()
    clusterer.load_tickets()
    incidents = clusterer.run_clustering()
    return incidents

@tool
def run_realtime_triage(new_ticket_text: str):
    """
    Runs real-time triage for a new ticket using current active incidents.
    Returns triage result (attach to incident or buffer).
    """
    with open("dataset/active_incidents.json", "r") as f:
        incidents = json.load(f)
    incidents_with_centroids = [inc for inc in incidents if 'centroid' in inc]
    if not incidents_with_centroids:
        return "No active incidents with centroids available. Run clustering with centroids first."
    for inc in incidents_with_centroids:
        inc['centroid'] = np.array(inc['centroid'])
    spec = importlib.util.spec_from_file_location("realtime_triage", "realtime_triage.py")
    rt = importlib.util.module_from_spec(spec)
    sys.modules["realtime_triage"] = rt
    spec.loader.exec_module(rt)
    triage = rt.RealTimeTriage(incidents_with_centroids)
    result = triage.handle_new_ticket(new_ticket_text)
    return result

# Load our datasets into memory for the tools to access
with open("dataset/logs.json", "r") as f:
    LOGS_DB = json.load(f)

with open("dataset/api_docs.md", "r") as f:
    DOCS_DB = f.read()

@tool
def fetch_merchant_logs(merchant_ids: list[str]):
    """
    Fetches the recent API error logs for a specific list of merchant IDs.
    Useful for finding error codes (4xx, 5xx) and payloads.
    """
    print(f"   🛠️ TOOL: Fetching logs for {merchant_ids[:2]}...")
    results = []
    for log in LOGS_DB:
        if log['merchant_id'] in merchant_ids:
            # Return simplified logs to save token space
            results.append(f"[{log['timestamp']}] {log['status_code']} {log['endpoint']} - {log['message']} - Payload: {log.get('payload_snippet', '')}")
    
    if not results:
        return "No recent error logs found for these merchants."
    return "\n".join(results[:10]) # Limit to top 10 logs

@tool
def search_documentation(query: str):
    """
    Searches the technical documentation and migration guides.
    Useful for checking schema definitions, deprecated fields, and error meanings.
    """
    print(f"   🛠️ TOOL: Searching docs for '{query}'...")
    # In a real app, use a Vector DB (Chroma/FAISS). 
    # For Hackathon, we do a simple keyword match or return relevant sections.
    
    results = []
    sections = DOCS_DB.split("##")
    for section in sections:
        if query.lower() in section.lower():
            results.append("##" + section)
            
    if not results:
        return "No specific documentation found. Try a broader query."
    return "\n".join(results[:2]) # Return top 2 relevant sections

@tool
def check_platform_health():
    """
    Checks if there is a global platform outage. 
    Returns True if many merchants are failing, False otherwise.
    """
    # Mock logic: If logs have many 500s from different merchants
    error_counts = 0
    for log in LOGS_DB:
        if log['status_code'] >= 500:
            error_counts += 1
    
    if error_counts > 20:
        return "CRITICAL: Potential Platform Outage detected (High volume of 500s)."
    return "Platform Status: Healthy. All systems operational."