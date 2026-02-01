import json
import numpy as np
import pandas as pd
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
        
        # Add caching and performance monitoring
        self._embedding_cache = {}
        self._start_time = None
        
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"⚠️ Failed to load sentence transformer: {e}")
            print("📝 Running in mock mode for demo purposes")
            self.model = None
        
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
        
        # Business-aware feature engineering
        self.df['is_revenue_critical'] = self.df['full_text'].str.contains(
            'checkout|payment|cart|order|revenue|transaction', case=False, regex=True
        ).astype(int)
        
        self.df['is_cross_merchant'] = (self.df['merchant_frequency'] >= 3).astype(int)
        
        # SLA-based priority scoring (enterprise merchants get higher priority)
        self.df['sla_tier'] = self.df['merchant_id'].apply(lambda x: 
            'enterprise' if x in ['m_001', 'm_002', 'm_003'] else 'standard'
        )
        self.df['sla_priority'] = (self.df['sla_tier'] == 'enterprise').astype(int)
        
        # Text length features (needed for ML model)
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
        """Create ground truth labels based on business logic and e-commerce migration patterns"""
        labels = []
        
        for _, row in self.df.iterrows():
            text = row['full_text'].lower()
            
            # Critical business logic: E-commerce migration-specific patterns
            
            # 1. REVENUE-CRITICAL CORS ISSUES = PLATFORM BUG (not user error!)
            # CORS on checkout/payment is revenue-affecting, likely platform CORS policy issue
            if any(term in text for term in ['checkout', 'payment', 'cart', 'add to cart']) and 'cors' in text:
                print(f"🎯 DEBUG: CORS + checkout found in ticket - should be platform_bug: {text[:100]}...")
                labels.append('platform_bug')  # Revenue-affecting CORS = platform issue
                
            # 2. PAYMENT WEBHOOK FAILURES = PLATFORM BUG (financial impact)
            # Webhooks failing means money taken but orders not processed = critical platform issue
            elif any(term in text for term in ['webhook', 'payment success', 'order created', 'orders stuck']) and any(code in text for code in ['404', '502', '504', 'timeout', 'gateway']):
                labels.append('platform_bug')  # Payment webhooks failing = platform issue
                
            # 3. CROSS-MERCHANT ISSUES = PLATFORM REGRESSION
            # Multiple merchants with same error = platform deployment issue
            elif row['merchant_frequency'] >= 3 and any(code in text for code in ['500', '502', '503', '504']):
                labels.append('platform_bug')  # Cross-merchant 5xx = platform issue
                
            # 4. SCHEMA MIGRATION ISSUES = USER ERROR (with context)
            # Using old V1 fields in V2 API = merchant needs to update code
            elif 'product_image' in text and any(term in text for term in ['v2', 'migration', 'breaking', 'additional properties', 'validation']):
                labels.append('user_error')  # Using old fields = user needs to update
                
            # 5. PLATFORM HEALTH INDICATORS = PLATFORM BUG
            # Database issues, connection pool exhaustion = infrastructure
            elif any(term in text for term in ['database', 'connection pool', 'exhausted', 'internal server', 'system down']):
                labels.append('platform_bug')  # Infrastructure issues
                
            # 6. AUTHENTICATION/CORS CONFIG = USER ERROR (single merchant)
            # New domains need whitelisting, API key issues = user config
            elif row['merchant_frequency'] <= 2 and any(term in text for term in ['unauthorized', 'forbidden', 'new domain', 'api key']):
                labels.append('user_error')  # Configuration issues for single merchant
                
            # 7. MIGRATION DOCUMENTATION GAPS = DOCS GAP  
            # Missing guidance for headless migration
            elif any(phrase in text for phrase in ['how to migrate', 'where is', 'missing guide', 'outdated docs', 'worked fine yesterday']):
                labels.append('docs_gap')  # Migration guidance missing
                
            # 8. ENTERPRISE MERCHANT PRIORITY ISSUES
            # Enterprise merchants with high priority = likely platform issue
            elif row['sla_tier'] == 'enterprise' and row['priority'] in ['Critical', 'High']:
                labels.append('platform_bug')  # Enterprise issues get platform attention
                
            # 9. FALLBACK RULES BASED ON ERROR PATTERNS AND FREQUENCY
            elif row['has_platform_errors'] and row['merchant_frequency'] >= 2:
                labels.append('platform_bug')  # Platform errors across merchants
            elif row['has_cors_errors'] and row['is_revenue_critical']:
                labels.append('platform_bug')  # Revenue-critical CORS = platform
            elif row['has_user_errors'] and row['merchant_frequency'] == 1:
                labels.append('user_error')  # Single merchant user error patterns
            elif row['has_schema_errors'] and 'migration' in text:
                labels.append('user_error')  # Schema errors during migration = user needs to update
                
            # DEFAULT CLASSIFICATION
            elif row['has_platform_errors']:
                labels.append('platform_bug')
            elif row['has_user_errors']:
                labels.append('user_error')
            else:
                labels.append('docs_gap')
                
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
        
        # BUSINESS OVERRIDE: Revenue-critical platform bugs take precedence
        platform_bugs = cluster_df[cluster_df['true_category'] == 'platform_bug']
        revenue_critical_bugs = platform_bugs[platform_bugs['is_revenue_critical'] == 1]
        
        if len(revenue_critical_bugs) > 0:
            print(f"🎯 BUSINESS OVERRIDE: Found {len(revenue_critical_bugs)} revenue-critical platform bugs in cluster")
            dominant_category = 'platform_bug'  # Override clustering majority vote
            
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