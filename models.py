import json
import numpy as np
import pandas as pd
import re
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.model_selection import cross_val_score
import os
import warnings
warnings.filterwarnings('ignore')

class HybridTicketClassifier:
    def __init__(self, data_path="dataset/tickets.json"):
        self.data_path = data_path
        print("⏳ Loading embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ML components
        self.tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        self.classifier = LogisticRegression(random_state=42, max_iter=1000)
        
        # Log parsing patterns (regex-based)
        self.log_patterns = {
            'error_codes': r'(\b[4-5][0-9]{2}\b)',
            'api_endpoints': r'(/api/v[0-9]/[a-zA-Z0-9/_-]+)',
            'schema_errors': r'(schema|validation|additional properties)',
            'cors_errors': r'(cors|origin|preflight|access-control)',
            'auth_errors': r'(unauthorized|forbidden|api key|token)',
            'timeout_errors': r'(timeout|connection|pool|exhausted)',
            'platform_errors': r'(500|502|503|504|internal server|database)',
            'user_errors': r'(400|401|403|404|validation|schema|cors)',
        }
        
    def load_tickets(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Missing {self.data_path}. Please create the dataset first.")
        
        with open(self.data_path, 'r') as f:
            self.tickets = json.load(f)
        
        self.df = pd.DataFrame(self.tickets)
        print(f"✅ Loaded {len(self.df)} tickets.")
        
        # Feature engineering
        self._engineer_features()
        
    def _engineer_features(self):
        """Extract structured features from ticket text using regex and ML"""
        print("🔧 Engineering features...")
        
        # Combine text fields
        self.df['full_text'] = self.df['subject'] + ". " + self.df['body']
        
        # Extract log patterns using regex
        for pattern_name, pattern in self.log_patterns.items():
            self.df[f'has_{pattern_name}'] = self.df['full_text'].str.contains(pattern, case=False, regex=True).astype(int)
            
        # Extract specific features
        self.df['error_code'] = self.df['full_text'].str.extract(r'\b([4-5][0-9]{2})\b')[0]
        self.df['endpoint'] = self.df['full_text'].str.extract(r'(/api/v[0-9]/[a-zA-Z0-9/_-]+)')[0]
        
        # Priority encoding
        priority_map = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
        self.df['priority_score'] = self.df['priority'].map(priority_map)
        
        # Merchant impact (number of affected merchants)
        merchant_counts = self.df['merchant_id'].value_counts()
        self.df['merchant_frequency'] = self.df['merchant_id'].map(merchant_counts)
        
        # Text length features
        self.df['text_length'] = self.df['full_text'].str.len()
        self.df['word_count'] = self.df['full_text'].str.split().str.len()
        
    def classify_incidents(self):
        """Hybrid classification: Ground truth labels + ML prediction"""
        print("🎯 Running hybrid classification...")
        
        # Create ground truth labels based on expert rules
        self.df['true_category'] = self._create_ground_truth_labels()
        
        # Prepare features for ML model
        feature_columns = [col for col in self.df.columns if col.startswith('has_')]
        feature_columns.extend(['priority_score', 'merchant_frequency', 'text_length', 'word_count'])
        
        X = self.df[feature_columns].fillna(0)
        y = self.df['true_category']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train classifier
        self.classifier.fit(X_scaled, y)
        
        # Predict probabilities
        probabilities = self.classifier.predict_proba(X_scaled)
        
        # Add prediction confidence
        self.df['prediction_confidence'] = np.max(probabilities, axis=1)
        self.df['predicted_category'] = self.classifier.predict(X_scaled)
        
        # Evaluate model
        cv_scores = cross_val_score(self.classifier, X_scaled, y, cv=3, scoring='accuracy')
        print(f"📊 Classification Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        return X_scaled, feature_columns
        
    def _create_ground_truth_labels(self):
        """Create expert-rule based ground truth labels"""
        labels = []
        
        for _, row in self.df.iterrows():
            text = row['full_text'].lower()
            priority = row['priority']
            
            # Calculate feature scores for balanced classification
            platform_score = 0
            user_score = 0 
            docs_score = 0
            
            # Platform bug indicators
            if any(code in text for code in ['500', '502', '503', '504']):
                platform_score += 3
            if any(word in text for word in ['database', 'connection pool', 'timeout', 'internal server']):
                platform_score += 2
            if priority == 'Critical' and row['merchant_frequency'] >= 3:
                platform_score += 2
            if 'outage' in text or 'system down' in text:
                platform_score += 3
                
            # User error indicators  
            if any(code in text for code in ['400', '401', '403', '404']):
                user_score += 2
            if any(word in text for word in ['schema', 'validation', 'cors', 'preflight']):
                user_score += 3
            if any(word in text for word in ['api key', 'authentication', 'forbidden']):
                user_score += 2
            if 'failing' in text and any(word in text for word in ['script', 'request', 'payload']):
                user_score += 2
                
            # Documentation gap indicators
            if any(phrase in text for phrase in ['where is', 'where are', 'missing', 'outdated']):
                docs_score += 3
            if any(phrase in text for phrase in ['documentation', 'guide says', 'docs seem']):
                docs_score += 2
            if any(phrase in text for phrase in ['api keys', 'settings > general', 'hide']):
                docs_score += 2
            if 'worked fine yesterday' in text:
                docs_score += 1
                
            # Classify based on highest score with thresholds
            max_score = max(platform_score, user_score, docs_score)
            
            if max_score == 0:
                # Default classification based on priority
                if priority in ['Critical', 'High']:
                    labels.append('platform_bug')
                else:
                    labels.append('user_error')
            elif platform_score == max_score and platform_score >= 2:
                labels.append('platform_bug')
            elif user_score == max_score and user_score >= 2:
                labels.append('user_error')
            elif docs_score == max_score and docs_score >= 2:
                labels.append('docs_gap')
            else:
                # Tie-breaker: default to user error for low scores
                labels.append('user_error')
                    
        return labels

    def run_clustering(self):
        """
        Hybrid approach:
        1. Feature engineering and classification
        2. Semantic clustering with embeddings  
        3. Quality metrics and validation
        4. Structured incident output
        """
        # Step 1: Classification
        X_scaled, feature_columns = self.classify_incidents()
        
        # Step 2: Semantic embeddings for clustering
        print("🧠 Generating semantic embeddings...")
        text_data = self.df['full_text'].tolist()
        embeddings = self.model.encode(text_data, show_progress_bar=True)
        
        # Step 3: DBSCAN clustering with optimized parameters
        print("🔍 Running DBSCAN clustering...")
        
        # Find optimal eps using knee method
        eps_optimal = self._find_optimal_eps(embeddings)
        
        clustering = DBSCAN(
            eps=eps_optimal, 
            min_samples=2,  # Minimum incident size
            metric='cosine'
        ).fit(embeddings)
        
        self.df['cluster_id'] = clustering.labels_
        
        # Step 4: Evaluate clustering quality
        self._evaluate_clustering(embeddings)
        
        # Step 5: Structure incidents with ML insights
        return self._structure_incidents_with_ml(embeddings, feature_columns)
    
    def _find_optimal_eps(self, embeddings, k=4):
        """Find optimal eps parameter using k-distance graph"""
        from sklearn.neighbors import NearestNeighbors
        
        nbrs = NearestNeighbors(n_neighbors=k, metric='cosine').fit(embeddings)
        distances, indices = nbrs.kneighbors(embeddings)
        
        # Sort distances to find knee
        distances = np.sort(distances[:, k-1], axis=0)
        
        # Simple knee detection: find largest gap
        diffs = np.diff(distances)
        knee_idx = np.argmax(diffs)
        optimal_eps = distances[knee_idx]
        
        print(f"📐 Optimal eps found: {optimal_eps:.3f}")
        return optimal_eps
    
    def _evaluate_clustering(self, embeddings):
        """Comprehensive clustering evaluation"""
        labels = self.df['cluster_id']
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        print(f"📊 Clustering Results:")
        print(f"   • Clusters found: {n_clusters}")
        print(f"   • Noise points: {n_noise} ({n_noise/len(labels)*100:.1f}%)")
        print(f"   • Clustered points: {len(labels) - n_noise} ({(len(labels)-n_noise)/len(labels)*100:.1f}%)")
        
        # Silhouette analysis (only if we have clusters)
        if n_clusters > 1 and n_noise < len(labels):
            # Filter out noise points for silhouette score
            clustered_mask = labels != -1
            if np.sum(clustered_mask) > 1:
                sil_score = silhouette_score(embeddings[clustered_mask], labels[clustered_mask])
                print(f"   • Silhouette Score: {sil_score:.3f}")
        
        # Category distribution per cluster
        print(f"\n📈 Cluster Analysis:")
        for cluster_id in unique_labels:
            if cluster_id == -1:
                continue
            cluster_data = self.df[self.df['cluster_id'] == cluster_id]
            categories = cluster_data['true_category'].value_counts()
            avg_confidence = cluster_data['prediction_confidence'].mean()
            
            print(f"   • Cluster {cluster_id}: {len(cluster_data)} tickets")
            print(f"     - Categories: {dict(categories)}")
            print(f"     - Avg Confidence: {avg_confidence:.2f}")
            print(f"     - Priority: {cluster_data['priority'].value_counts().to_dict()}")

    def _structure_output_with_centroids(self, embeddings):
        incidents = []
        unique_clusters = set(self.df['cluster_id'])
        for cluster_id in unique_clusters:
            if cluster_id == -1:
                continue
            cluster_df = self.df[self.df['cluster_id'] == cluster_id]
            cluster_indices = cluster_df.index.tolist()
    def _structure_incidents_with_ml(self, embeddings, feature_columns):
        """Structure incidents using ML insights and confidence scores"""
        incidents = []
        unique_clusters = set(self.df['cluster_id'])
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Skip noise
                continue
                
            cluster_df = self.df[self.df['cluster_id'] == cluster_id]
            cluster_indices = cluster_df.index.tolist()
            
            # Calculate centroid
            cluster_embeddings = [embeddings[i] for i in cluster_indices]
            centroid = np.mean(cluster_embeddings, axis=0).tolist()
            
            # ML-based incident analysis
            incident_analysis = self._analyze_incident_ml(cluster_df)
            
            # Build incident object with ML insights
            incident_obj = {
                "incident_id": f"INC-{cluster_id}",
                "status": "DETECTED",
                "ticket_count": int(len(cluster_df)),
                "priority_level": incident_analysis['priority'],
                "affected_merchants": cluster_df['merchant_id'].unique().tolist(),
                "summary": incident_analysis['summary'],
                "centroid": centroid,
                
                # ML Classification Results
                "ml_category": incident_analysis['dominant_category'],
                "category_confidence": incident_analysis['avg_confidence'],
                "category_distribution": incident_analysis['category_dist'],
                
                # Feature Analysis
                "error_patterns": incident_analysis['error_patterns'],
                "technical_indicators": incident_analysis['technical_indicators'],
                
                # Evidence
                "sample_tickets": cluster_df.head(2)[['subject', 'body', 'true_category', 'prediction_confidence']].to_dict('records'),
                "ticket_ids": cluster_df['ticket_id'].tolist(),
            }
            
            incidents.append(incident_obj)
            
        # Sort by ML confidence and impact
        incidents.sort(key=lambda x: (x['ticket_count'], x['category_confidence']), reverse=True)
        return incidents
    
    def _analyze_incident_ml(self, cluster_df):
        """ML-based incident analysis"""
        # Category analysis
        categories = cluster_df['true_category'].value_counts()
        dominant_category = categories.index[0]
        category_dist = categories.to_dict()
        
        # Confidence analysis
        avg_confidence = cluster_df['prediction_confidence'].mean()
        
        # Priority determination (ML-enhanced)
        priority_scores = cluster_df['priority_score'].values
        merchant_count = len(cluster_df['merchant_id'].unique())
        
        if dominant_category == 'platform_bug' or avg_confidence > 0.8:
            priority = 'Critical' if merchant_count >= 3 else 'High'
        elif dominant_category == 'user_error' and avg_confidence > 0.7:
            priority = 'Medium'
        else:
            priority = cluster_df['priority'].mode()[0]  # Fallback to most common
        
        # Extract error patterns
        error_patterns = []
        for _, row in cluster_df.iterrows():
            if row.get('error_code'):
                error_patterns.append(f"HTTP {row['error_code']}")
            if row.get('endpoint'):
                error_patterns.append(f"Endpoint: {row['endpoint']}")
                
        # Technical indicators
        tech_indicators = {}
        pattern_cols = [col for col in cluster_df.columns if col.startswith('has_')]
        for col in pattern_cols:
            if cluster_df[col].sum() > 0:
                pattern_name = col.replace('has_', '').replace('_', ' ').title()
                tech_indicators[pattern_name] = int(cluster_df[col].sum())
        
        # Generate summary
        example_subject = cluster_df.iloc[0]['subject']
        summary = f"{len(cluster_df)} {dominant_category.replace('_', ' ')} incidents: {example_subject}"
        
        return {
            'dominant_category': dominant_category,
            'category_dist': category_dist,
            'avg_confidence': round(avg_confidence, 3),
            'priority': priority,
            'summary': summary,
            'error_patterns': list(set(error_patterns))[:5],  # Top 5 unique patterns
            'technical_indicators': tech_indicators
        }

# --- EXECUTION ---
if __name__ == "__main__":
    print("🚀 Starting Hybrid ML-Based Incident Classification...\n")
    
    # Initialize hybrid classifier
    classifier = HybridTicketClassifier()
    classifier.load_tickets()
    
    # Run hybrid ML pipeline
    detected_incidents = classifier.run_clustering()
    
    print("\n" + "="*60)
    print(f"🎯 ML ANALYSIS COMPLETE: {len(detected_incidents)} INCIDENTS DETECTED")
    print("="*60)
    
    for inc in detected_incidents:
        print(f"\n[{inc['incident_id']}] {inc['ml_category'].upper()} (confidence: {inc['category_confidence']:.2f})")
        print(f"  📊 Tickets: {inc['ticket_count']} | Priority: {inc['priority_level']} | Merchants: {len(inc['affected_merchants'])}")
        print(f"  🎯 Summary: {inc['summary'][:100]}...")
        
        if inc['error_patterns']:
            print(f"  ⚠️  Patterns: {', '.join(inc['error_patterns'][:3])}")
        
        if inc['technical_indicators']:
            top_indicators = list(inc['technical_indicators'].items())[:3]
            indicators_str = ', '.join([f"{k}: {v}" for k, v in top_indicators])
            print(f"  🔧 Tech Indicators: {indicators_str}")
        
        print(f"  📈 Category Distribution: {inc['category_distribution']}")
        
    # Save enhanced output
    with open("dataset/active_incidents.json", "w") as f:
        json.dump(detected_incidents, f, indent=2)
    print(f"\n✅ Enhanced ML analysis saved to 'dataset/active_incidents.json'")
    
    # Print ML model insights
    print(f"\n🤖 Model Performance Summary:")
    total_tickets = len(classifier.df)
    categories = classifier.df['true_category'].value_counts()
    print(f"  📊 Total tickets analyzed: {total_tickets}")
    print(f"  🏷️  Category breakdown: {dict(categories)}")
    print(f"  🎯 Average prediction confidence: {classifier.df['prediction_confidence'].mean():.3f}")
    
    # Feature importance (top features)
    feature_columns = [col for col in classifier.df.columns if col.startswith('has_')]
    feature_columns.extend(['priority_score', 'merchant_frequency'])
    
    if hasattr(classifier.classifier, 'coef_') and len(feature_columns) > 0:
        feature_importance = np.abs(classifier.classifier.coef_[0])
        if len(feature_importance) == len(feature_columns):
            top_features_idx = np.argsort(feature_importance)[-5:][::-1]
            
            print(f"  🔍 Top predictive features:")
            for idx in top_features_idx:
                if idx < len(feature_columns):
                    feature_name = feature_columns[idx].replace('has_', '').replace('_', ' ').title()
                    print(f"    • {feature_name}: {feature_importance[idx]:.3f}")

# For backward compatibility
TicketClusterer = HybridTicketClassifier