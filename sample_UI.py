

import streamlit as st
import json
from agent_tools import check_platform_health


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
</style>
""", unsafe_allow_html=True)




# Header
st.markdown('<div class="header">Agentic AI for Self-Healing Migration Support</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Advanced System: ML Clustering → Multi-Agent Investigation → Autonomous Resolution</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown('<div class="subheader">Control Center</div>', unsafe_allow_html=True)
    mode = st.radio(
        "Select Operation",
        ["Incident Detection (ML)", "Agent Investigation", "Full Pipeline"],
        index=2
    )
    st.divider()
    st.markdown('<div class="subheader">Platform Health</div>', unsafe_allow_html=True)
    health = check_platform_health.invoke({})


    # Main panel logic
if mode == "Incident Detection (ML)":
    st.markdown('### ML-Powered Ticket Clustering')
    st.markdown("Detects and clusters incidents from support tickets using the latest model.")
    if st.button("Run Clustering", type="primary", use_container_width=True):
        from agent_tools import run_ticket_clustering
        with st.spinner("Running clustering model..."):
            incidents = run_ticket_clustering.invoke({})
        if not incidents:
            st.warning("No incidents detected.")
        else:
            st.success(f"Detected {len(incidents)} incidents.")
            for inc in incidents:
                with st.expander(f"📋 {inc.get('incident_id','N/A')} - {inc.get('summary','No summary')[:80]}...", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Ticket Count", inc.get('ticket_count', 0))
                    with col2:
                        st.metric("Priority", inc.get('priority_level', 'N/A').upper())
                    with col3:
                        st.metric("Merchants", len(inc.get('affected_merchants', [])))
                    
                    st.markdown("**Summary:**")
                    st.write(inc.get('summary', 'No summary available'))
                    
                    if inc.get('affected_merchants'):
                        st.markdown("**Affected Merchants:**")
                        st.code(', '.join(inc.get('affected_merchants', [])))
                    
                    if inc.get('sample_tickets'):
                        st.markdown("**Sample Tickets:**")
                        for i, ticket in enumerate(inc.get('sample_tickets', [])[:3]):
                            st.markdown(f"*Ticket {i+1}:* {ticket}")
                    
                    with st.expander("🔍 Raw Data", expanded=False):
                        st.json(inc)

elif mode == "Agent Investigation":
    st.markdown('### Multi-Agent Investigation System')
    st.markdown("Architecture: Orchestrator → Investigator → Researcher → Analyst → Responder")
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
            if result.get('docs_data'):
                with st.expander("📚 Documentation Evidence", expanded=False):
                    st.markdown(result.get('docs_data'))
            
            # Response Handling based on confidence
            confidence = result.get('confidence_score', 0)
            draft_response = result.get('draft_response', '')
            
            if draft_response:
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
                            
                            # Join and display
                            formatted_message = '\n\n'.join(formatted_parts)
                            st.markdown(f"""
                            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; border-left: 4px solid #1f77b4;">
                            {formatted_message}
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            # Fallback formatting
                            formatted_response = draft_response.replace('\\n', '\n\n').replace('\\"', '"')
                            st.markdown(f"""
                            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; border-left: 4px solid #1f77b4;">
                            {formatted_response}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Show timestamp
                        import datetime
                        st.caption(f"Sent at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                elif confidence >= 0.6:  # Medium confidence - require approval
                    st.markdown("#### ⚠️ Response Requires Approval")
                    st.warning(f"Medium confidence ({confidence:.1%}). Please review and approve the suggested response.")
                    
                    with st.container():
                        st.markdown("**Suggested Response:**")
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
                            
                            # Join and display
                            formatted_message = '\n\n'.join(formatted_parts)
                            st.markdown(f"""
                            <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                            {formatted_message}
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            # Fallback formatting
                            formatted_response = draft_response.replace('\\n', '\n\n').replace('\\"', '"')
                            st.markdown(f"""
                            <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
                            {formatted_response}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Approval buttons
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            if st.button("✅ Approve & Send", type="primary"):
                                st.success("✅ Response approved and sent to merchants!")
                                st.balloons()
                        with col2:
                            if st.button("❌ Reject"):
                                st.error("❌ Response rejected. Escalated to human support team.")
                        with col3:
                            if st.button("📝 Edit & Send"):
                                st.info("📝 Redirecting to response editor...")
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
                            
                            # Join and display
                            formatted_message = '\n\n'.join(formatted_parts)
                            st.markdown(f"""
                            <div style="background-color: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545;">
                            {formatted_message}
                            </div>
                            """, unsafe_allow_html=True)
                            
                        except Exception as e:
                            # Fallback formatting
                            formatted_response = draft_response.replace('\\n', '\n\n').replace('\\"', '"')
                            st.markdown(f"""
                            <div style="background-color: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545;">
                            {formatted_response}
                            </div>
                            """, unsafe_allow_html=True)
            
            # Proposed Action
            if result.get('proposed_action'):
                st.markdown("#### ⚡ Proposed Action")
                st.warning(result.get('proposed_action'))
            
            with st.expander("🔍 Complete Raw Output", expanded=False):
                st.json(result)

elif mode == "Full Pipeline":
    st.markdown('### Full Agentic Pipeline')
    st.markdown("End-to-End: Ticket Clustering → Incident Detection → Multi-Agent Investigation")
    if st.button("Run Complete Pipeline", type="primary", use_container_width=True):
        from agent_tools import run_ticket_clustering
        from agent_graph import run_agent_on_incident
        progress = st.progress(0)
        status = st.empty()
        # Step 1: Clustering
        status.write("Step 1: ML-Powered Clustering")
        incidents = run_ticket_clustering.invoke({})
        progress.progress(40)
        # Step 2: Investigation (run on first incident for demo)
        status.write("Step 2: Multi-Agent Investigation")
        investigation_result = None
        if incidents:
            investigation_result = run_agent_on_incident(incidents[0])
        progress.progress(100)
        status.write("Pipeline Complete!")
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
                        formatted_response = draft_response.replace('\n', '\n\n')
                        st.markdown(f"""
                        <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px; border-left: 4px solid #1f77b4;">
                        {formatted_response}
                        </div>
                        """, unsafe_allow_html=True)
                elif confidence >= 0.6:
                    st.markdown("**Status:** ⚠️ Awaiting approval")
                else:
                    st.markdown("**Status:** 🚨 Escalated to human support")
            
            with st.expander("🔍 Complete Pipeline Output", expanded=False):
                st.markdown("**Clustering Result:**")
                if incidents:
                    st.json(incidents[0])
                st.markdown("**Investigation Result:**")
                st.json(investigation_result)


else:  # Full Pipeline
    st.markdown('<div class="subheader">Full Agentic Pipeline</div>', unsafe_allow_html=True)
    st.markdown("End-to-End: Ticket Clustering → Incident Detection → Multi-Agent Investigation")
    if st.button("Run Complete Pipeline", type="primary", use_container_width=True):
        progress = st.progress(0)
        status = st.empty()
        # Step 1: Clustering
        status.write("Step 1: ML-Powered Clustering")
        # You will need to adapt this to your new clustering logic
        # ...clustering logic here...
        progress.progress(40)
        # Step 2: Investigation
        status.write("Step 2: Multi-Agent Investigation")
        # ...investigation logic here...
        progress.progress(100)
        status.write("Pipeline Complete!")
        st.divider()
        st.markdown('<div class="subheader">Results Summary</div>', unsafe_allow_html=True)
        # ...display results summary here...