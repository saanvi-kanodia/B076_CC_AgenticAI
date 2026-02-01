"""
NexusCommerce API Documentation Viewer
Interactive documentation with search and navigation
"""

import streamlit as st
import re

st.set_page_config(
    page_title="NexusCommerce API Documentation",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for documentation styling
st.markdown("""
<style>
.doc-header {
    background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 2rem;
}

.doc-section {
    background: #f8fafc;
    border-left: 4px solid #3b82f6;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 0 8px 8px 0;
}

.code-example {
    background: #1e293b;
    color: #e2e8f0;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.endpoint {
    background: #22c55e;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.875rem;
}

.warning {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.error-code {
    background: #fee2e2;
    border: 1px solid #ef4444;
    padding: 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    display: inline-block;
    margin: 0.25rem;
}

.nav-section {
    background: #f1f5f9;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

def load_documentation():
    """Load the API documentation"""
    try:
        with open('dataset/api_docs.md', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return "# Documentation Not Found\nPlease ensure api_docs.md exists in the dataset folder."

def extract_sections(content):
    """Extract sections from markdown content"""
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line[3:].strip()
            current_content = [line]
        else:
            if current_section:
                current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections

def search_content(content, query):
    """Search for content in documentation"""
    if not query:
        return []
    
    matches = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if query.lower() in line.lower():
            # Get context around the match
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            context = '\n'.join(lines[start:end])
            matches.append({
                'line': i + 1,
                'content': line,
                'context': context
            })
    
    return matches

def main():
    # Header
    st.markdown("""
    <div class="doc-header">
        <h1>🚀 NexusCommerce API Documentation</h1>
        <p>Complete guide for headless e-commerce integration</p>
        <p><strong>Version 2.4.0</strong> • Last Updated: December 15, 2023</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load documentation
    doc_content = load_documentation()
    sections = extract_sections(doc_content)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown('<div class="nav-section">', unsafe_allow_html=True)
        st.markdown("### 📋 Navigation")
        
        # Search
        search_query = st.text_input("🔍 Search documentation", placeholder="e.g., CORS, rate limit, webhook")
        
        # Section selection
        if sections:
            section_names = list(sections.keys())
            selected_section = st.selectbox("📖 Jump to section", ["Overview"] + section_names)
        else:
            selected_section = "Overview"
        
        st.markdown("### 🔗 Quick Links")
        st.markdown("""
        - [Authentication](#2-authentication-security)
        - [Products API](#3-products-api) 
        - [Orders API](#4-orders-api)
        - [Rate Limits](#6-rate-limits-throttling)
        - [Error Codes](#7-error-codes-troubleshooting)
        - [Migration Guide](#8-migration-guide-v23-v24)
        """)
        
        st.markdown("### ⚡ Common Issues")
        st.markdown("""
        - **CORS Errors**: Add domain to Settings > Security > CORS Origins
        - **401 Unauthorized**: Generate new API token
        - **Schema Validation**: Remove `product_image`, use `images` array
        - **Rate Limits**: Implement exponential backoff
        - **Missing Orders**: Check webhook configuration
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content area
    if search_query:
        st.markdown(f"### 🔍 Search Results for '{search_query}'")
        matches = search_content(doc_content, search_query)
        
        if matches:
            for match in matches[:10]:  # Limit to 10 results
                with st.expander(f"Line {match['line']}: {match['content'][:100]}..."):
                    st.markdown(f"**Context:**")
                    st.code(match['context'])
        else:
            st.info("No matches found. Try different keywords.")
            
        st.divider()
    
    # Display selected section
    if selected_section == "Overview":
        # Split content by first section
        if '## ' in doc_content:
            overview_content = doc_content.split('## ')[0]
        else:
            overview_content = doc_content
        st.markdown(overview_content)
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📚 Sections", len(sections))
        with col2:
            st.metric("🔗 Endpoints", doc_content.count('**Endpoint:**'))
        with col3:
            st.metric("⚠️ Error Codes", doc_content.count('**Error:**'))
        with col4:
            st.metric("💡 Examples", doc_content.count('```'))
            
    elif selected_section in sections:
        section_content = sections[selected_section]
        
        # Process markdown for better display
        section_content = section_content.replace('**Endpoint:**', '<span class="endpoint">ENDPOINT</span>')
        section_content = section_content.replace('⚠️ **BREAKING CHANGES:**', '<div class="warning">⚠️ <strong>BREAKING CHANGES:</strong>')
        section_content = section_content.replace('**Error:**', '<div class="error-code">ERROR:</div>')
        
        st.markdown(section_content, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.875rem;">
        📞 Need help? Contact support@nexuscommerce.com | 🌐 Status: status.nexuscommerce.com
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()