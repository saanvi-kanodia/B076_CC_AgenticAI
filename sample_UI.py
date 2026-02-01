import streamlit as st
import json
from dotenv import load_dotenv
from email_service import send_incident_response

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Agentic AI - Headless Migration Support",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, clean look
st.markdown("""
<style>
.header {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 12px;
}
.subheader {
    font-size: 20px;
    font-weight: 600;
    margin-top: 24px;
    margin-bottom: 8px;
}
.metric-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 18px 24px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.incident-card {
    background: #fff;
    border: 1px solid #e3e6ea;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 18px;
}
.message-container {
    background: #1e1e1e;
    color: #ffffff;
    border-radius: 8px;
    padding: 20px;
    margin: 15px 0;
    border-left: 4px solid #007bff;
    white-space: pre-wrap;
    font-family: 'Source Code Pro', monospace;
    line-height: 1.6;
}
.response-header {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    color: #495057;
}
.response-section {
    margin-bottom: 15px;
}
.api-block {
    background: #2d3748;
    color: #e2e8f0;
    padding: 12px;
    border-radius: 6px;
    font-family: 'Source Code Pro', monospace;
    margin: 8px 0;
}
.investigation-result {
    background: #fff;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 20px;
    margin: 10px 0;
}
.status-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}
.status-critical {
    background: #dc3545;
    color: white;
}
.status-high {
    background: #fd7e14;
    color: white;
}
.status-medium {
    background: #ffc107;
    color: black;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header">Agentic AI for Self-Healing Migration Support</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Advanced System: ML Clustering → Multi-Agent Investigation → Autonomous Resolution</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Documentation Viewer Modal
if 'show_docs' not in st.session_state:
    st.session_state['show_docs'] = False

if st.session_state['show_docs']:
    st.markdown("---")
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("### 📚 API Documentation Viewer")
    with col2:
        if st.button("✖ Close", key="close_docs"):
            st.session_state['show_docs'] = False
            st.rerun()
    
    try:
        with open('dataset/api_docs.md', 'r') as f:
            docs_content = f.read()
        
        # Display the documentation
        st.markdown(docs_content)
        
    except FileNotFoundError:
        st.error("Documentation file not found at dataset/api_docs.md")
    
    st.markdown("---")
    if st.button("✖ Close Documentation", key="close_docs_bottom"):
        st.session_state['show_docs'] = False
        st.rerun()

# Sidebar
with st.sidebar:
    st.header("🎛️ Control Center")

    # Documentation Viewer Button
    if st.button("📚 Open Documentation Viewer", use_container_width=True):
        st.session_state['show_docs'] = True
    
    # Documentation PR Button
    if st.button("🚀 Auto-Update Docs (Create PR)", use_container_width=True):
        from docs_pr_automation import DocumentationPRAgent
        
        with st.spinner("Analyzing documentation gaps..."):
            try:
                agent = DocumentationPRAgent()
                result = agent.run_full_workflow()
                
                if result and result['status'] == 'success':
                    st.success(f"✅ PR Created! #{result['pr_number']}")
                    st.markdown(f"[View PR]({result['pr_url']})")
                elif result and result['status'] == 'simulated':
                    st.info("📋 Simulated - Add GITHUB_TOKEN to .env")
                else:
                    st.warning("No documentation gaps found or already up to date")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Mode selection
    mode = st.selectbox(
        "System Operation Mode",
        ["Incident Detection (ML)", "Agent Investigation", "Full Pipeline"],
        index=0
    )

    st.divider()

    # Quick stats if incidents exist
    try:
        with open('dataset/active_incidents.json', 'r') as f:
            incidents_data = json.load(f)

        # Get total tickets from original dataset
        try:
            with open('dataset/tickets.json', 'r') as f:
                all_tickets = json.load(f)
            total_tickets_db = len(all_tickets)
        except:
            total_tickets_db = sum(inc.get('ticket_count', 0) for inc in incidents_data)

        st.subheader("📊 System Status")
        st.metric("Active Incidents", len(incidents_data))

        if incidents_data:
            critical_count = sum(1 for inc in incidents_data if inc.get('priority_level') == 'Critical')
            st.metric("Critical Issues", critical_count)

            st.metric("Total Tickets", total_tickets_db)
    except:
        st.info("Run detection to see system stats")


    # Main panel logic
if mode == "Incident Detection (ML)":
    st.markdown('### 🔍 ML-Powered Incident Detection')
    st.markdown("**Using DBSCAN clustering + Business rule classification** to group similar support tickets into actionable incidents.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("#### How It Works:")
        st.markdown("""
        1. **Feature Engineering**: Extract patterns, error codes, merchant frequencies
        2. **Ground Truth Labels**: Apply business rules for platform bugs, user errors, docs gaps  
        3. **ML Classification**: Train hybrid classifier for confidence scoring
        4. **Semantic Clustering**: Group similar tickets using sentence embeddings
        5. **Incident Generation**: Create actionable incidents with priority levels
        """)
    
    with col2:
        if st.button("🚀 Run Detection", type="primary", use_container_width=True):
            from agent_tools import run_ticket_clustering
            
            with st.spinner("Running ML incident detection..."):
                incidents = run_ticket_clustering.invoke({})
            
            if not incidents:
                st.warning("⚠️ No incidents detected. Check ticket data.")
            else:
                st.success(f"✅ Detected {len(incidents)} incidents from ticket analysis")
                st.rerun()
    
    # Display existing incidents
    try:
        with open('dataset/active_incidents.json', 'r') as f:
            incidents = json.load(f)
        
        if incidents:
            st.divider()
            st.markdown(f"### 🚨 Active Incidents ({len(incidents)})")
            
            for inc in incidents[:8]:  # Show top 8 incidents
                # Create status badge
                priority = inc.get('priority_level', 'Medium')
                status_class = f"status-{priority.lower()}" if priority in ['Critical', 'High', 'Medium'] else "status-medium"
                
                with st.expander(
                    f"**{inc.get('incident_id', 'N/A')}** | {inc.get('ticket_count', 0)} tickets | {inc.get('ml_category', 'unknown').replace('_', ' ').title()}",
                    expanded=False
                ):
                    # Metrics row
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Tickets", inc.get('ticket_count', 0))
                    with col2:
                        st.metric("Merchants", len(inc.get('affected_merchants', [])))
                    with col3:
                        st.metric("Priority", priority)
                    with col4:
                        st.metric("Confidence", f"{inc.get('category_confidence', 0.8):.1%}")
                    
                    # Summary and details
                    st.markdown(f"**Summary:** {inc.get('summary', 'No summary available')}")
                    
                    if inc.get('error_patterns'):
                        st.markdown(f"**Error Patterns:** {', '.join(inc.get('error_patterns', [])[:3])}")
                    
                    # Sample ticket
                    if inc.get('sample_tickets'):
                        sample = inc['sample_tickets'][0]
                        st.markdown("**Example Ticket:**")
                        st.info(f"**{sample.get('subject', 'No subject')}**\n\n{sample.get('body', 'No body')[:150]}...")
        
    except FileNotFoundError:
        st.info("💡 Click 'Run Detection' to analyze tickets and detect incidents.")

elif mode == "Agent Investigation":
    st.markdown('### Multi-Agent Investigation System')
    st.markdown("Architecture: Orchestrator → Investigator → Researcher → Analyst → Responder")
    
    # Initialize session state for investigation results
    if 'investigation_result' not in st.session_state:
        st.session_state['investigation_result'] = None
    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = False
    if 'edited_response' not in st.session_state:
        st.session_state['edited_response'] = ''
    
    try:
        with open('dataset/active_incidents.json', 'r') as f:
            incidents = json.load(f)
    except Exception:
        incidents = []
    if not incidents:
        st.warning("No incidents detected. Run 'Incident Detection' first.")
    else:
        incident_options = [f"{inc['incident_id']}: {inc.get('summary','')[:50]}..." for inc in incidents]
        selected_idx = st.selectbox("Select Incident to Investigate", range(len(incidents)), format_func=lambda x: incident_options[x])
        selected_incident = incidents[selected_idx]
        if st.button("Launch Investigation", type="primary", use_container_width=True):
            from agent_graph import run_agent_on_incident
            with st.spinner("Running agent investigation..."):
                result = run_agent_on_incident(selected_incident)
                st.session_state['investigation_result'] = result
                st.session_state['edit_mode'] = False  # Reset edit mode on new investigation
        
        # Display results if they exist
        result = st.session_state.get('investigation_result')
        if result:
            st.markdown('### 🔬 Investigation Results')
            
            # Key metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Confidence Score", f"{result.get('confidence_score', 0):.1%}")
            with col2:
                st.metric("Status", "Complete" if result.get('draft_response') else "Incomplete")
            
            # Root Cause Analysis
            if result.get('root_cause_analysis'):
                st.markdown("#### 🎯 Root Cause Analysis")
                
                root_cause = result.get('root_cause_analysis')
                
                # Try to parse if it's JSON-like, otherwise display as text
                try:
                    import json
                    if root_cause.strip().startswith('{'):
                        parsed = json.loads(root_cause)
                        
                        # Display probabilities
                        if 'probabilities' in parsed:
                            st.markdown("**Issue Classification:**")
                            probs = parsed['probabilities']
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("User Error", f"{probs.get('user_error', 0)}%")
                            with col2:
                                st.metric("Platform Bug", f"{probs.get('platform_bug', 0)}%")
                            with col3:
                                st.metric("Docs Gap", f"{probs.get('docs_gap', 0)}%")
                        
                        # Display evidence
                        if 'evidence' in parsed:
                            st.markdown("**Evidence:**")
                            for evidence in parsed['evidence']:
                                st.markdown(f"• {evidence}")
                        
                        # Display diagnosis
                        if 'diagnosis' in parsed:
                            st.success(f"**Diagnosis:** {parsed['diagnosis']}")
                        
                        # Display explanation
                        if 'explanation' in parsed:
                            st.info(parsed['explanation'])
                        
                        # Display recommended action
                        if 'recommended_action' in parsed:
                            st.warning(f"**Recommended Action:** {parsed['recommended_action']}")
                    else:
                        st.info(root_cause)
                except:
                    # Fallback to plain text display
                    st.info(root_cause)
            
            # Logs Analysis
            if result.get('logs_data'):
                with st.expander("📊 Log Analysis", expanded=True):
                    log_lines = result.get('logs_data', '').split('\n')
                    for line in log_lines[:10]:  # Show first 10 lines
                        if line.strip():
                            st.code(line)
            
            # Documentation Evidence
            if result.get('docs_data') and result['docs_data'] != "Documentation search failed. Using symptom analysis for diagnosis.":
                with st.expander("📚 Documentation Evidence", expanded=False):
                    # Clean up and format the documentation
                    docs_content = result.get('docs_data', '')
                    if "No specific documentation found" not in docs_content and "Documentation search failed" not in docs_content:
                        # Split by section separators for better formatting
                        sections = docs_content.split('---')
                        for i, section in enumerate(sections):
                            section = section.strip()
                            # Skip Troubleshooting Codes, HTTP Status Codes, and any table-only or pipe/dash-only sections
                            lower_section = section.lower()
                            if (
                                lower_section.startswith('## 7. troubleshooting codes') or
                                lower_section.startswith('### http status codes') or
                                'troubleshooting codes' in lower_section or
                                'http status codes' in lower_section or
                                # skip if section is just a table or pipes/dashes
                                all((not c.isalnum()) for c in section.replace('|','').replace('-','').replace('–','').replace('—','').replace(' ','').replace('\n','')) or
                                # skip if section is just a markdown table (starts with | and has multiple |)
                                (section.startswith('|') and section.count('|') > 2)
                            ):
                                continue
                            if section:
                                st.markdown(section)
                                if i < len(sections) - 1:  # Add separator between sections
                                    st.divider()
                    else:
                        st.info("No relevant documentation found for this specific issue.")
            else:
                # Always show the expander but indicate no results
                with st.expander("📚 Documentation Evidence", expanded=False):
                    st.info("Documentation search was not performed or returned no results.")
            
            # Response Handling based on confidence AND business logic
            confidence = result.get('confidence_score', 0)
            draft_response = result.get('draft_response', '')
            
            # Check for financial impact to override confidence thresholds
            is_financial = any(keyword in selected_incident.get('summary', '').lower() 
                             for keyword in ['payment', 'checkout', 'order', 'revenue', 'billing'])
            
            merchant_count = len(selected_incident.get('affected_merchants', []))
            is_cross_merchant = merchant_count >= 3
            
            if draft_response:
                # BUSINESS RULE: Financial issues cap confidence at 75%
                if is_financial and confidence >= 0.75:
                    st.markdown("#### 💰 Financial Impact - Human Review Required")
                    st.error(f"Financial impact detected. Confidence capped at 75% for safety. Manual review required.")
                    confidence = 0.74  # Force into manual review category
                
                # BUSINESS RULE: Cross-merchant issues need human oversight  
                elif is_cross_merchant and confidence >= 0.7:
                    st.markdown("#### 🏢 Cross-Merchant Pattern - Platform Review")
                    st.warning(f"Cross-merchant issue ({merchant_count} merchants) - likely platform bug. Engineering review required.")
                    confidence = 0.69  # Force manual review
                
                # Original confidence-based routing with business overrides
                if confidence >= 0.8:  # High confidence - auto-send
                    st.markdown("#### ✅ Response Sent to Merchants")
                    st.success("High confidence classification detected. Message automatically sent to affected merchants.")
                    
                    with st.container():
                        st.markdown("**Message Sent:**")
                        # Parse and format the response content
                        try:
                            import json
                            import re
                            if draft_response.strip().startswith('{'):
                                parsed = json.loads(draft_response)
                                message_content = parsed.get('message_body', draft_response)
                            else:
                                message_content = draft_response
                            
                            # Clean up escape characters
                            message_content = message_content.replace('\\n', '\n').replace('\\"', '"')
                            
                            # Split message into parts for better formatting
                            parts = message_content.split('\n')
                            formatted_parts = []
                            
                            i = 0
                            while i < len(parts):
                                part = parts[i].strip()
                                
                                # Check for API endpoints (GET, POST, etc.)
                                if re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s+/', part):
                                    # Collect the full API block
                                    api_block = [part]
                                    i += 1
                                    while i < len(parts) and (parts[i].strip().startswith('Headers:') or parts[i].strip().startswith('{') or parts[i].strip() == '}'):
                                        api_block.append(parts[i].strip())
                                        i += 1
                                    
                                    # Format as code block
                                    formatted_parts.append(f"```\n{chr(10).join(api_block)}\n```")
                                    continue
                                
                                # Check for URLs
                                if 'https://' in part:
                                    urls = re.findall(r'https://[^\s]+', part)
                                    for url in urls:
                                        part = part.replace(url, f'[{url}]({url})')
                                
                                # Check for deprecated field mentions
                                if 'product_image' in part and 'images' in part:
                                    part = part.replace('product_image', '`product_image`').replace(' images', ' `images`')
                                
                                formatted_parts.append(part)
                                i += 1
                            
                            # Join and display with structured formatting
                            formatted_message = '\n\n'.join(formatted_parts)
                            
                            st.markdown('<div class="response-container">', unsafe_allow_html=True)
                            st.markdown('<div class="response-header">📧 Message Sent to Merchants</div>', unsafe_allow_html=True)
                            
                            # Parse message into sections
                            sections = formatted_message.split('\n\n')
                            for section in sections:
                                if section.strip():
                                    if section.strip().startswith('```'):
                                        # Code block
                                        code_content = section.replace('```', '').strip()
                                        st.code(code_content, language='http')
                                    elif 'https://' in section:
                                        # URL section - make links clickable
                                        import re
                                        urls = re.findall(r'https://[^\s]+', section)
                                        formatted_section = section
                                        for url in urls:
                                            if url and url != 'https://':
                                                formatted_section = formatted_section.replace(url, f'[{url}]({url})')
                                        st.markdown(formatted_section)
                                    else:
                                        st.markdown(section)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                        except Exception as e:
                            # Fallback formatting with structure
                            formatted_response = draft_response.replace('\\n', '\n\n').replace('\\"', '"')
                            st.markdown('<div class="response-container">', unsafe_allow_html=True)
                            st.markdown('<div class="response-header">📧 Message Sent to Merchants</div>', unsafe_allow_html=True)
                            st.markdown(formatted_response)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Send email to merchants
                        email_result = send_incident_response(
                            incident_data=selected_incident,
                            response_content=message_content,
                            is_edited=False
                        )
                        
                        # Show timestamp and email status
                        import datetime
                        st.caption(f"Sent at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        if email_result.get('demo_mode'):
                            st.info(f"📧 Demo Mode: {email_result.get('message')} | Recipients: {', '.join(email_result.get('recipients', []))}")
                        elif email_result.get('success'):
                            st.success(f"📧 Email notifications sent to {len(email_result.get('recipients', []))} merchant(s)")
                        
                elif confidence >= 0.6:  # Medium confidence - require approval
                    st.markdown("#### ⚠️ Response Requires Approval")
                    st.warning(f"Medium confidence ({confidence:.1%}). Please review and approve or edit the suggested response.")
                    
                    # Parse and format the response content
                    try:
                        import json
                        import re
                        if draft_response.strip().startswith('{'):
                            parsed = json.loads(draft_response)
                            message_content = parsed.get('message_body', draft_response)
                        else:
                            message_content = draft_response
                        message_content = message_content.replace('\\n', '\n').replace('\\"', '"')
                    except Exception:
                        message_content = draft_response.replace('\\n', '\n').replace('\\"', '"')
                    
                    if not st.session_state['edit_mode']:
                        st.markdown('<div class="message-container">', unsafe_allow_html=True)
                        st.markdown(message_content)
                        st.markdown('</div>', unsafe_allow_html=True)
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button("Approve & Send", key="approve_send_btn", type="primary"):
                                # Send email to merchants
                                email_result = send_incident_response(
                                    incident_data=selected_incident,
                                    response_content=message_content,
                                    is_edited=False
                                )
                                
                                st.success("Response approved and sent to merchants!")
                                
                                if email_result.get('demo_mode'):
                                    st.info(f"📧 Demo Mode: {email_result.get('message')}")
                                elif email_result.get('success'):
                                    st.success(f"📧 Email sent to {len(email_result.get('recipients', []))} merchant(s)")
                                
                                st.balloons()
                        with col2:
                            if st.button("Reject", key="reject_btn"):
                                st.error("Response rejected. Escalated to human support team.")
                        with col3:
                            if st.button("Edit", key="edit_btn"):
                                st.session_state['edit_mode'] = True
                                st.session_state['edited_response'] = message_content
                                st.rerun()
                    else:
                        edited = st.text_area("Edit the response below:", value=st.session_state.get('edited_response', message_content), height=300, key="edit_area")
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Send", key="send_edit_btn", type="primary"):
                                # Send edited email to merchants
                                email_result = send_incident_response(
                                    incident_data=selected_incident,
                                    response_content=edited,
                                    is_edited=True
                                )
                                
                                # Update the investigation result with edited response
                                if st.session_state.get('investigation_result'):
                                    st.session_state['investigation_result']['draft_response'] = edited
                                
                                st.session_state['edit_mode'] = False
                                st.session_state['edited_response'] = edited
                                st.success("Edited response sent to merchants!")
                                
                                if email_result.get('demo_mode'):
                                    st.info(f"📧 Demo Mode: {email_result.get('message')}")
                                elif email_result.get('success'):
                                    st.success(f"📧 Email sent to {len(email_result.get('recipients', []))} merchant(s)")
                                
                                st.balloons()
                                st.rerun()
                        with col2:
                            if st.button("Cancel", key="cancel_edit_btn"):
                                st.session_state['edit_mode'] = False
                                st.session_state['edited_response'] = ''
                                st.rerun()
                else:  # Low confidence - escalate
                    st.markdown("#### 🚨 Low Confidence - Human Review Required")
                    st.error(f"Low confidence ({confidence:.1%}). This case has been escalated to human support.")
                    
                    with st.expander("📋 View AI Suggestion", expanded=False):
                        # Parse and format the draft response
                        try:
                            import json
                            import re
                            if draft_response.strip().startswith('{'):
                                parsed = json.loads(draft_response)
                                
                                if 'action_type' in parsed:
                                    st.markdown(f"**Action Type:** {parsed['action_type']}")
                                
                                message_content = parsed.get('message_body', draft_response)
                            else:
                                message_content = draft_response
                            
                            st.markdown("**Suggested Message:**")
                            
                            # Clean up escape characters
                            message_content = message_content.replace('\\n', '\n').replace('\\"', '"')
                            
                            # Split message into parts for better formatting
                            parts = message_content.split('\n')
                            formatted_parts = []
                            
                            i = 0
                            while i < len(parts):
                                part = parts[i].strip()
                                
                                # Check for API endpoints (GET, POST, etc.)
                                if re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s+/', part):
                                    # Collect the full API block
                                    api_block = [part]
                                    i += 1
                                    while i < len(parts) and (parts[i].strip().startswith('Headers:') or parts[i].strip().startswith('{') or parts[i].strip() == '}'):
                                        api_block.append(parts[i].strip())
                                        i += 1
                                    
                                    # Format as code block
                                    formatted_parts.append(f"```\n{chr(10).join(api_block)}\n```")
                                    continue
                                
                                # Check for URLs
                                if 'https://' in part:
                                    urls = re.findall(r'https://[^\s]+', part)
                                    for url in urls:
                                        part = part.replace(url, f'[{url}]({url})')
                                
                                # Check for deprecated field mentions
                                if 'product_image' in part and 'images' in part:
                                    part = part.replace('product_image', '`product_image`').replace(' images', ' `images`')
                                
                                formatted_parts.append(part)
                                i += 1
                            
                            # Join and display with structured formatting
                            formatted_message = '\n\n'.join(formatted_parts)
                            
                            st.markdown('<div class="response-container">', unsafe_allow_html=True)
                            st.markdown('<div class="response-header">🚨 AI Suggestion (Requires Human Review)</div>', unsafe_allow_html=True)
                            
                            # Parse message into sections
                            sections = formatted_message.split('\n\n')
                            for section in sections:
                                if section.strip():
                                    if section.strip().startswith('```'):
                                        # Code block
                                        code_content = section.replace('```', '').strip()
                                        st.code(code_content, language='http')
                                    elif 'https://' in section:
                                        # URL section - make links clickable
                                        import re
                                        urls = re.findall(r'https://[^\s]+', section)
                                        formatted_section = section
                                        for url in urls:
                                            if url and url != 'https://':
                                                formatted_section = formatted_section.replace(url, f'[{url}]({url})')
                                        st.markdown(formatted_section)
                                    else:
                                        st.markdown(section)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                        except Exception as e:
                            # Fallback formatting with structure
                            formatted_response = draft_response.replace('\\n', '\n\n').replace('\\"', '"')
                            st.markdown('<div class="response-container">', unsafe_allow_html=True)
                            st.markdown('<div class="response-header">🚨 AI Suggestion (Requires Human Review)</div>', unsafe_allow_html=True)
                            st.markdown(formatted_response)
                            st.markdown('</div>', unsafe_allow_html=True)
            
            # Proposed Action
            if result.get('proposed_action'):
                st.markdown("#### ⚡ Proposed Action")
                st.warning(result.get('proposed_action'))
            
            with st.expander("🔍 Complete Raw Output", expanded=False):
                st.json(result)

elif mode == "Full Pipeline":
    st.markdown('### Full Agentic Pipeline')
    st.markdown("End-to-End: Ticket Clustering → Incident Detection → Multi-Agent Investigation → Documentation Update")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Run Complete Pipeline", type="primary", use_container_width=True):
            from agent_tools import run_ticket_clustering
            from agent_graph import run_agent_on_incident
            from docs_pr_automation import DocumentationPRAgent
            
            progress = st.progress(0)
            status = st.empty()
            
            # Step 1: Clustering
            status.write("Step 1/3: ML-Powered Clustering")
            incidents = run_ticket_clustering.invoke({})
            progress.progress(33)
            
            # Step 2: Investigation (run on first incident for demo)
            status.write("Step 2/3: Multi-Agent Investigation")
            investigation_result = None
            if incidents:
                investigation_result = run_agent_on_incident(incidents[0])
            progress.progress(66)
            
            # Step 3: Documentation Update
            status.write("Step 3/3: Analyzing Documentation Gaps")
            try:
                docs_agent = DocumentationPRAgent()
                docs_result = docs_agent.run_full_workflow()
            except Exception as e:
                docs_result = {'status': 'error', 'error': str(e)}
            progress.progress(100)
            
            status.write("✅ Pipeline Complete!")
            st.markdown('### 📈 Pipeline Results Summary')
        
        if incidents:
            st.markdown("#### 🎯 Detected Incident")
            inc = incidents[0]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Incident ID", inc.get('incident_id', 'N/A'))
            with col2:
                st.metric("Tickets", inc.get('ticket_count', 0))
            with col3:
                st.metric("Priority", inc.get('priority_level', 'N/A').upper())
            
            st.markdown("**Summary:**")
            st.write(inc.get('summary', 'No summary available'))
        
        if investigation_result:
            st.markdown("#### 🔬 Investigation Outcome")
            
            # Quick summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Root Cause Found", "Yes" if investigation_result.get('root_cause_analysis') else "No")
            with col2:
                st.metric("Response Ready", "Yes" if investigation_result.get('draft_response') else "No")
            
            if investigation_result.get('root_cause_analysis'):
                st.markdown("**Root Cause:**")
                st.success(investigation_result.get('root_cause_analysis'))
            
            # Response handling for pipeline
            confidence = investigation_result.get('confidence_score', 0)
            draft_response = investigation_result.get('draft_response', '')
            
            if draft_response:
                if confidence >= 0.8:
                    st.markdown("**Status:** ✅ Response automatically sent (high confidence)")
                    with st.expander("📧 View sent message", expanded=False):
                        # Better formatting for pipeline output
                        try:
                            import json
                            import re
                            
                            # Parse JSON if it's structured
                            if draft_response.strip().startswith('{'):
                                parsed = json.loads(draft_response)
                                message_content = parsed.get('message_body', draft_response)
                            else:
                                message_content = draft_response
                            
                            # Clean up escape characters
                            message_content = message_content.replace('\\n', '\n').replace('\\"', '"')
                            
                            st.markdown('<div class="response-container">', unsafe_allow_html=True)
                            st.markdown('<div class="response-header">📧 Auto-Sent Message</div>', unsafe_allow_html=True)
                            
                            # Split into sections for better display
                            sections = message_content.split('\n\n')
                            for section in sections:
                                if section.strip():
                                    if re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s+/', section):
                                        st.code(section, language='http')
                                    elif 'https://' in section:
                                        # Handle URLs
                                        urls = re.findall(r'https://[^\s]+', section)
                                        formatted_section = section
                                        for url in urls:
                                            if url and url != 'https://':
                                                formatted_section = formatted_section.replace(url, f'[{url}]({url})')
                                        st.markdown(formatted_section)
                                    else:
                                        st.markdown(section)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                        except:
                            # Fallback
                            formatted_response = draft_response.replace('\\n', '\n\n').replace('\\"', '"')
                            st.markdown('<div class="message-container">', unsafe_allow_html=True)
                            st.markdown(formatted_response)
                            st.markdown('</div>', unsafe_allow_html=True)
                elif confidence >= 0.6:
                    st.markdown("**Status:** ⚠️ Awaiting approval")
                else:
                    st.markdown("**Status:** 🚨 Escalated to human support")
            
            # Documentation Update Results
            if docs_result:
                st.markdown("#### 📚 Documentation Update")
                if docs_result.get('status') == 'success':
                    st.success(f"✅ Documentation PR Created: #{docs_result.get('pr_number')}")
                    st.markdown(f"[View PR on GitHub]({docs_result.get('pr_url')})")
                elif docs_result.get('status') == 'simulated':
                    st.info("📋 Documentation gaps identified (simulation mode)")
                else:
                    st.warning("No significant documentation gaps found")
            
            with st.expander("🔍 Complete Pipeline Output", expanded=False):
                st.markdown("**Clustering Result:**")
                if incidents:
                    st.json(incidents[0])
                st.markdown("**Investigation Result:**")
                st.json(investigation_result)
                if docs_result:
                    st.markdown("**Documentation Update Result:**")
                    st.json(docs_result)

