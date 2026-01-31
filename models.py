import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import os

class TicketClusterer:
    def __init__(self, data_path="dataset/tickets.json"):
        self.data_path = data_path
        # Load a small, fast pre-trained model for embeddings
        # This runs locally on your CPU/GPU
        print("⏳ Loading embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def load_tickets(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Missing {self.data_path}. Please create the dataset first.")
        
        with open(self.data_path, 'r') as f:
            self.tickets = json.load(f)
        
        self.df = pd.DataFrame(self.tickets)
        print(f"✅ Loaded {len(self.df)} tickets.")

    def run_clustering(self):
        """
        1. Vectorize text
        2. Run DBSCAN
        3. Return structured incidents
        """
        # 1. Combine meaningful text for the model
        # We give more weight to the Subject by repeating it? No, just concat is fine.
        text_data = (self.df['subject'] + ". " + self.df['body']).tolist()
        
        print("🧠 Generating vector embeddings...")
        embeddings = self.model.encode(text_data, show_progress_bar=True)
        
        # 2. DBSCAN Config
        # eps=0.35: Distance threshold. Lower = stricter clusters. Higher = loose clusters.
        # min_samples=3: Need at least 3 similar tickets to call it an "Incident".
        # metric='cosine': Best for text similarity.
        print("xx Clustering vectors...")
        clustering = DBSCAN(eps=0.35, min_samples=3, metric='cosine').fit(embeddings)
        
        self.df['cluster_id'] = clustering.labels_
        
        # 3. Analyze Results
        return self._structure_output()

    def _structure_output(self):
        incidents = []
        unique_clusters = set(self.df['cluster_id'])
        
        for cluster_id in unique_clusters:
            # -1 in DBSCAN means "Noise" (unique tickets that don't fit a pattern)
            if cluster_id == -1:
                continue
                
            cluster_df = self.df[self.df['cluster_id'] == cluster_id]
            
            # Find the most representative ticket (center of cluster) - simplified here by taking first
            example_ticket = cluster_df.iloc[0]
            
            incident_obj = {
                "incident_id": f"INC-{cluster_id}",
                "status": "DETECTED",
                "ticket_count": int(len(cluster_df)),
                "priority_level": cluster_df['priority'].mode()[0], # Most frequent priority
                "affected_merchants": cluster_df['merchant_id'].unique().tolist(),
                "summary": f"Cluster of {len(cluster_df)} tickets related to: {example_ticket['subject']}",
                "example_ticket_text": f"Subject: {example_ticket['subject']}\nBody: {example_ticket['body']}",
                "ticket_ids": cluster_df['ticket_id'].tolist()
            }
            incidents.append(incident_obj)
            
        # Sort by ticket count (biggest fires first)
        incidents.sort(key=lambda x: x['ticket_count'], reverse=True)
        return incidents

# --- EXECUTION ---
if __name__ == "__main__":
    ai = TicketClusterer()
    ai.load_tickets()
    
    # Run the model
    detected_incidents = ai.run_clustering()
    
    print("\n" + "="*50)
    print(f"🚨 AGENT REPORT: DETECTED {len(detected_incidents)} ACTIVE INCIDENTS")
    print("="*50)
    
    for inc in detected_incidents:
        print(f"\n[ID: {inc['incident_id']}] Count: {inc['ticket_count']} | Priority: {inc['priority_level']}")
        print(f"Summary: {inc['summary']}")
        print(f"Affected: {inc['affected_merchants']}")
        
    # Save this for the Agent to use in the next step
    with open("dataset/active_incidents.json", "w") as f:
        json.dump(detected_incidents, f, indent=2)
    print("\n✅ Saved incident report to 'dataset/active_incidents.json'")