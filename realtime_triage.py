import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class RealTimeTriage:
    def __init__(self, active_incidents):
        """
        active_incidents: List of objects from your previous script.
        Each must have 'embedding_centroid' (the average vector of tickets in that cluster).
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.active_clusters = active_incidents
        self.pending_buffer = []
        self.SIMILARITY_THRESHOLD = 0.85

    def handle_new_ticket(self, new_ticket_text):
        print(f"⚡ New Ticket Received: '{new_ticket_text[:40]}...'")
        
        # 1. Vectorize
        new_vector = self.model.encode([new_ticket_text]) # Shape (1, 384)
        
        best_match = None
        highest_score = -1
        
        # 2. Compare against Active Incidents
        for cluster in self.active_clusters:
            # Assume we stored the centroid in the cluster object
            cluster_vector = np.array(cluster['centroid']).reshape(1, -1)
            
            score = cosine_similarity(new_vector, cluster_vector)[0][0]
            
            if score > highest_score:
                highest_score = score
                best_match = cluster

        # 3. Decision Logic
        if highest_score >= self.SIMILARITY_THRESHOLD:
            print(f"   ✅ MATCH FOUND! Assigned to {best_match['incident_id']} (Score: {highest_score:.4f})")
            print(f"   🤖 ACTION: Apply Agent Logic from {best_match['incident_id']}")
            return {
                "action": "attach_to_incident",
                "incident_id": best_match['incident_id']
            }
        else:
            print(f"   ⚠️ NO MATCH (Max Score: {highest_score:.4f}). Added to Pending Buffer.")
            self.pending_buffer.append(new_ticket_text)
            
            # Check if we should form a new cluster
            if len(self.pending_buffer) >= 5:
                self._check_for_new_clusters()
            
            return {"action": "buffer"}

    def _check_for_new_clusters(self):
        print("   🔍 Buffer full. Running mini-clustering to find NEW incidents...")
        # Here you would run the DBSCAN logic again on self.pending_buffer
        # If a cluster forms -> Create Incident #8 -> Clear from buffer

# --- MOCK SETUP FOR DEMO ---
# Let's pretend we already found Incident #1 (The Checkout Error)
# We calculate its centroid (average of the tickets in it)
embedder = SentenceTransformer('all-MiniLM-L6-v2')
mock_cluster_text = [
    "API failing on product update",
    "Schema validation error on products",
    "Cannot update product images via API"
]
cluster_vectors = embedder.encode(mock_cluster_text)
centroid = np.mean(cluster_vectors, axis=0)

active_incidents = [{
    "incident_id": "INC-1",
    "summary": "Product Schema Validation Errors",
    "centroid": centroid
}]

# --- RUN REAL-TIME SIMULATION ---
triage = RealTimeTriage(active_incidents)

# Case 1: A ticket that matches the existing problem
triage.handle_new_ticket("Help! My product update script is getting 400 errors on the image field.")

# Case 2: A totally new, unrelated problem
triage.handle_new_ticket("I lost my password and cannot login.")