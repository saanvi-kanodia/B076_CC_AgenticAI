
# agent_tools.py
import json
import importlib.util
import sys
import numpy as np
from langchain_core.tools import tool
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

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

# Initialize Mini RAG System
class MiniRAG:
    def __init__(self):
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            self.model = None
            print("⚠️ RAG: Running without embeddings (offline mode)")
        
        self.chunks = self._chunk_docs()
        self.embeddings = self._embed_chunks() if self.model else None
    
    def _chunk_docs(self):
        """Split docs into semantic chunks"""
        # Split by sections (##) and subsections
        sections = re.split(r'\n#{1,3}\s+', DOCS_DB)
        chunks = []
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 50:  # Skip tiny sections
                # Add section headers for context
                if i > 0:
                    lines = section.split('\n')
                    header = lines[0] if lines else f"Section {i}"
                    chunks.append({
                        'id': f"chunk_{i}",
                        'header': header,
                        'content': section.strip(),
                        'keywords': self._extract_keywords(section)
                    })
        return chunks
    
    def _extract_keywords(self, text):
        """Extract key technical terms"""
        keywords = re.findall(r'\b(?:API|CORS|webhook|authentication|token|endpoint|schema|migration|error|404|500|401|403|product_image|images|V2|headless|Bearer)\b', text, re.IGNORECASE)
        return list(set([k.lower() for k in keywords]))
    
    def _embed_chunks(self):
        """Generate embeddings for all chunks"""
        if not self.model:
            return None
        
        texts = [f"{chunk['header']} {chunk['content']}" for chunk in self.chunks]
        return self.model.encode(texts)
    
    def search(self, query, top_k=2):
        """Semantic + keyword search"""
        query_lower = query.lower()
        results = []
        
        # Keyword matching first (fast)
        keyword_matches = []
        for chunk in self.chunks:
            score = 0
            # Direct keyword matches
            for keyword in chunk['keywords']:
                if keyword in query_lower:
                    score += 2
            
            # Content substring matches
            if any(term in chunk['content'].lower() for term in query_lower.split()):
                score += 1
                
            if score > 0:
                keyword_matches.append((chunk, score))
        
        # Semantic search if embeddings available
        if self.model and self.embeddings is not None:
            query_embedding = self.model.encode([query])
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Combine keyword and semantic scores
            for i, chunk in enumerate(self.chunks):
                semantic_score = similarities[i]
                keyword_score = next((score for c, score in keyword_matches if c['id'] == chunk['id']), 0)
                
                combined_score = (semantic_score * 0.6) + (keyword_score * 0.4)
                if combined_score > 0.1:  # Threshold
                    results.append((chunk, combined_score))
        else:
            # Fallback to keyword only
            results = [(chunk, score) for chunk, score in keyword_matches]
        
        # Sort by score and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in results[:top_k]]

# Initialize RAG instance
rag = MiniRAG()

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
    Searches the technical documentation using semantic similarity + keyword matching.
    Returns the most relevant documentation sections for the query.
    """
    print(f"   🔍 RAG: Searching docs for '{query}'...")
    
    try:
        # Use RAG system for intelligent search
        relevant_chunks = rag.search(query, top_k=3)
        
        if not relevant_chunks:
            return "No relevant documentation found. The query may be too specific or outside our knowledge base."
        
        # Format results
        formatted_results = []
        for chunk in relevant_chunks:
            formatted_results.append(f"## {chunk['header']}\n{chunk['content'][:500]}{'...' if len(chunk['content']) > 500 else ''}")
        
        result = "\n\n---\n\n".join(formatted_results)
        print(f"   ✅ RAG: Found {len(relevant_chunks)} relevant sections")
        return result
        
    except Exception as e:
        print(f"   ❌ RAG Error: {str(e)}")
        # Fallback to simple search
        sections = DOCS_DB.split("##")
        results = []
        for section in sections:
            if query.lower() in section.lower():
                results.append("##" + section)
        
        if not results:
            return "Documentation search failed. Manual investigation required."
        return "\n".join(results[:2])

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

# --- PR AGENT TOOLS ---

@tool
def validate_pr_code(files_changed: list[dict]):
    """
    Validates PR code for common issues.
    Returns list of issues found.
    """
    print(f"   🛠️ TOOL: Validating PR code ({len(files_changed)} files)...")
    issues = []
    
    for file_info in files_changed:
        filename = file_info.get('filename', '')
        if filename.endswith('.py'):
            # Python-specific checks
            if file_info.get('additions', 0) > 500:
                issues.append(f"{filename}: Large file change ({file_info['additions']} lines)")
            if file_info.get('deletions', 0) > file_info.get('additions', 1):
                issues.append(f"{filename}: More deletions than additions (potential breaking change)")
    
    return issues if issues else "No major issues found"

@tool
def check_merge_conflicts(base_branch: str, target_branch: str, files_list: list[str]):
    """
    Checks for potential merge conflicts between branches.
    """
    print(f"   🛠️ TOOL: Checking merge conflicts between {base_branch} and {target_branch}...")
    # In production, this would query git history
    conflicts = []
    
    # Simple heuristic: frequently changed files are more likely to conflict
    frequently_changed = ['requirements.txt', 'package.json', 'pom.xml', '.gitignore']
    for file in files_list:
        if any(freq in file for freq in frequently_changed):
            conflicts.append(f"High conflict risk in {file}")
    
    return conflicts if conflicts else "No likely merge conflicts detected"

@tool
def get_pr_context(pr_title: str, pr_description: str):
    """
    Extracts key context from PR title and description.
    Returns categorized information.
    """
    print(f"   🛠️ TOOL: Extracting PR context...")
    
    context = {
        "type": "feature",
        "category": "general",
        "has_breaking_changes": "BREAKING" in pr_title.upper() or "BREAKING" in pr_description.upper(),
        "has_security_changes": "security" in pr_title.lower() or "security" in pr_description.lower(),
        "has_tests": "test" in pr_title.lower() or "test" in pr_description.lower()
    }
    
    if "fix" in pr_title.lower():
        context["type"] = "bugfix"
    elif "feat" in pr_title.lower() or "feature" in pr_title.lower():
        context["type"] = "feature"
    elif "refactor" in pr_title.lower():
        context["type"] = "refactor"
    
    return context


@tool
def create_documentation_pr(incident_summary: str, gap_reasoning: str):
    """
    Creates a GitHub PR to update api_docs.md based on incident patterns.
    Use this when investigation reveals documentation gaps causing support issues.
    
    Args:
        incident_summary: Summary of the incident pattern
        gap_reasoning: Explanation of what's missing in documentation
    
    Returns:
        PR creation status and URL
    """
    print(f"   📚 TOOL: Creating documentation PR...")
    
    try:
        from docs_pr_automation import DocumentationPRAgent
        
        agent = DocumentationPRAgent()
        
        # Create custom gap analysis from agent's findings
        gap_analysis = {
            'gaps_found': True,
            'gap_count': 1,
            'critical_gaps': [incident_summary],
            'suggested_additions': ['Clarify based on incident pattern'],
            'priority': 'high',
            'reasoning': gap_reasoning
        }
        
        # Generate improvements
        improvements = agent.generate_documentation_improvements(gap_analysis)
        
        if not improvements:
            return {
                'status': 'no_improvements',
                'message': 'Could not generate documentation improvements'
            }
        
        # Create PR
        result = agent.create_pr_for_docs_update(
            improvements=improvements,
            gap_analysis=gap_analysis
        )
        
        return result
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Failed to create documentation PR'
        }