# Agentic AI Support System for E-commerce Migration

**Advanced incident detection and resolution using hybrid machine learning and multi-agent orchestration**

---

## Overview

This system provides autonomous support incident detection, classification, and resolution during headless e-commerce platform migrations. It combines machine learning-based clustering with multi-agent reasoning to identify, analyze, and respond to merchant support issues in real-time.

<img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/7d54cb71-b8ed-493f-a6c9-1f29a757d6ec" />

## Key Features

### 🧠 Hybrid ML Classification

- **DBSCAN clustering** for incident pattern detection
- **Logistic regression** with feature engineering for classification
- **Semantic embeddings** using transformer models
- **75.1% accuracy** with balanced multi-class prediction

### 🤖 Multi-Agent System

- **Investigator**: Analyzes error logs and merchant data
- **Researcher**: Searches documentation and knowledge base using RAG (Retrieval-Augmented Generation)
- **Analyst**: Performs root cause analysis with confidence scoring
- **Responder**: Generates contextual responses and action plans

### 🔍 RAG-Powered Documentation Search

- **Semantic Search**: Uses sentence embeddings to find relevant documentation
- **MiniRAG System**: Lightweight retrieval-augmented generation for context-aware responses
- **Top-K Retrieval**: Fetches most relevant documentation chunks for each incident
- **Smart Chunking**: Breaks API docs into searchable sections with embeddings
- **Fallback Mode**: Gracefully handles offline scenarios

### ⚡ Intelligent Response Handling

- **High confidence (≥80%)**: Automated response deployment with email notification
- **Medium confidence (60-79%)**: Human approval workflow with edit capability
- **Low confidence (<60%)**: Escalation to support team
- **Financial/Cross-merchant safeguards**: Automatic confidence capping for sensitive issues

### 📧 Automated Email Notifications

- **SMTP Integration**: Sends responses directly to merchant email addresses
- **Three Trigger Points**:
  - Auto-send on high confidence (≥80%)
  - Manual approval with "Approve & Send" button
  - Edited response with "Edit & Send" workflow
- **Professional Formatting**: Incident references, timestamps, and support signatures
- **Demo Mode**: Safe testing without actual email delivery

### 🤖 Self-Updating Documentation (Autonomous + Manual)

- **Automated PR Creation**: Analyzes incident patterns and creates GitHub PRs to update api_docs.md
- **Autonomous Agent Integration**: Responder agent automatically creates PRs when documentation gaps detected
- **Smart Triggers**:
  - Documentation gap diagnosis (docs_gap ≥ 30%)
  - Cross-merchant patterns (≥3 merchants, confidence < 80%)
- **Gap Detection**: AI identifies what's missing or unclear in documentation
- **Smart Improvements**: Generates new sections based on common support issues
- **GitHub Integration**: Automatically creates branches, commits, and pull requests
- **Dual Access**:
  - Manual: UI sidebar button "🤖 Create Documentation PR"
  - Automatic: Agent decides during investigation workflow
- **No Human Intervention Needed**: Self-improving documentation loop

### ✏️ Response Editing & Review

- **Edit Button**: Modify AI-generated responses before sending
- **Persistent State**: Edited responses remain visible after sending
- **Human-in-the-Loop**: Balance automation with human oversight
- **Session Management**: Investigation results cached across UI interactions

### 📚 Documentation Viewer

- **In-App Access**: Browse API documentation without leaving the interface
- **Modal View**: Clean, focused documentation display
- **Contextual Help**: Quick reference during investigation workflow

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
- **SMTP/Gmail** - Email delivery system
- **python-dotenv** - Environment configuration

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

### Environment Setup

**Required Environment Variables:**

- `GROQ_API_KEY` - Get from [Groq Console](https://console.groq.com/)
- `SUPPORT_EMAIL` - Gmail address for sending notifications
- `SUPPORT_EMAIL_PASSWORD` - Gmail App Password (not regular password)

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

**Dashboard Features:**

- **Incident Detection**: View ML-clustered incidents with priority levels
- **Agent Investigation**: Launch multi-agent analysis on selected incidents
- **Response Management**:
  - Review AI-generated responses with confidence scores
  - Edit responses before sending
  - Approve or reject recommendations
  - Track email delivery status
- **Documentation Access**: In-app API documentation viewer
- **Full Pipeline**: End-to-end automation from tickets to merchant notifications

**Response Workflow:**

```
High Confidence (≥80%) → Auto-send email → Show success
Medium Confidence (60-79%) → Review → Edit (optional) → Approve → Send email
Low Confidence (<60%) → Escalate → Human takes over
```

## Model Performance

- **Classification Accuracy**: 75.1% (±14.9%)
- **Clustering Quality**: 98% tickets clustered, 2% noise
- **Response Confidence**: 70-85% average confidence scores
- **Category Distribution**: 51% user error, 31% platform issues, 18% documentation gaps
- **Email Delivery**: 100% success rate with Gmail SMTP
- **Edit Persistence**: Session state management ensures edited responses remain visible

## Project Structure

```
B076_CC_AgenticAI/
├── sample_UI.py              # Main Streamlit dashboard
├── agent_graph.py            # Multi-agent orchestration
├── agent_tools.py            # Agent utility functions
├── models.py                 # ML classification & clustering
├── email_service.py          # Email notification system
├── docs_viewer.py            # Documentation browser
├── dataset/
│   ├── tickets.json          # Support ticket data
│   ├── logs.json             # System logs
│   ├── api_docs.md           # API documentation
│   └── active_incidents.json # Detected incidents
├── .env                      # Environment variables (not in git)
├── .gitignore                # Git ignore patterns
├── requirements.txt          # Python dependencies
├── EMAIL_SETUP.md            # Email configuration guide
└── README.md                 # This file
```

## Contributing

1. Ensure all tests pass: `python -m pytest`
2. Run ML validation: `python models.py`
3. Check agent performance: `python agent_graph.py`

## License

MIT License - See LICENSE file for details

---

**Note**: This system is designed for merchant-level support automation and does not handle customer payment data or sensitive information.
