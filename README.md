# Agentic AI Support System for E-commerce Migration: Helix

**Advanced incident detection and resolution using hybrid machine learning and multi-agent orchestration**

---

## Overview

This system provides autonomous support incident detection, classification, and resolution during headless e-commerce platform migrations. It combines machine learning-based clustering with multi-agent reasoning to identify, analyze, and respond to merchant support issues in real-time.

## Key Features

### 🧠 Hybrid ML Classification

- **DBSCAN clustering** for incident pattern detection
- **Logistic regression** with feature engineering for classification
- **Semantic embeddings** using transformer models
- **75.1% accuracy** with balanced multi-class prediction

### 🤖 Multi-Agent System

- **Investigator**: Analyzes error logs and merchant data
- **Researcher**: Searches documentation and knowledge base
- **Analyst**: Performs root cause analysis with confidence scoring
- **Responder**: Generates contextual responses and action plans

### ⚡ Intelligent Response Handling

- **High confidence (≥80%)**: Automated response deployment
- **Medium confidence (60-79%)**: Human approval workflow
- **Low confidence (<60%)**: Escalation to support team

### 📊 Real-Time Analytics

- Live incident clustering and classification
- Confidence-based decision routing
- Technical indicator extraction
- Performance metrics and model evaluation

## Architecture

```
Support Tickets → ML Classification → Incident Clustering → Multi-Agent Analysis → Response Generation
                     ↓                        ↓                      ↓                    ↓
               Feature Engineering    Semantic Grouping    Root Cause Analysis    Automated Actions
```

## Technical Stack

- **Python 3.11** - Core runtime
- **scikit-learn** - Machine learning pipeline
- **sentence-transformers** - Semantic embeddings
- **LangChain/LangGraph** - Multi-agent orchestration
- **Streamlit** - Interactive dashboard
- **Groq API** - LLM inference

## Installation

```bash
# Clone repository
git clone <repository-url>
cd B076_CC_AgenticAI

# Install dependencies
pip install -r requirements.txt

# Run ML training and clustering
python models.py

# Launch web interface
streamlit run sample_UI.py

# View documentation
streamlit run docs_viewer.py
```

## Usage

### 1. Incident Detection

The ML model automatically processes support tickets and generates incidents:

```python
from models import HybridTicketClassifier

classifier = HybridTicketClassifier()
classifier.load_tickets()
incidents = classifier.run_clustering()
```

### 2. Agent Investigation

Multi-agent system analyzes incidents and provides recommendations:

```python
from agent_graph import run_agent_on_incident

result = run_agent_on_incident(incident_data)
confidence = result['confidence_score']
response = result['draft_response']
```

### 3. Dashboard Monitoring

Access the Streamlit dashboard for real-time monitoring and manual oversight.

## Model Performance

- **Classification Accuracy**: 75.1% (±14.9%)
- **Clustering Quality**: 98% tickets clustered, 2% noise
- **Response Confidence**: 70-85% average confidence scores
- **Category Distribution**: 51% user error, 31% platform issues, 18% documentation gaps


## Contributing

1. Ensure all tests pass: `python -m pytest`
2. Run ML validation: `python models.py`
3. Check agent performance: `python agent_graph.py`

## License

MIT License - See LICENSE file for details

---

**Note**: This system is designed for merchant-level support automation and does not handle customer payment data or sensitive information.
