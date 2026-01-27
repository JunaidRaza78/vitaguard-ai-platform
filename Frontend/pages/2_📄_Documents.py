"""
Documents Page
Upload and search medical documents
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import init_session_state, is_authenticated
from components.api_client import upload_document, search_documents, logout

# Initialize
init_session_state()

# Page config
st.set_page_config(
    page_title="Documents - Family Health Manager",
    page_icon="📄",
    layout="wide"
)

# Check auth
if not is_authenticated():
    st.warning("Please login to access this page")
    st.switch_page("app.py")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .document-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border-left: 4px solid #0d9488;
    }
    .specialty-badge {
        display: inline-block;
        background: #0d9488;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
    }
    .score-badge {
        display: inline-block;
        background: #f59e0b;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📄 Documents")
    
    user = st.session_state.get("user", {})
    st.markdown(f"**👤 {user.get('first_name', 'User')}**")
    
    st.divider()
    
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.switch_page("app.py")

# Main content
st.title("📄 Document Management")

# Tabs
tab1, tab2 = st.tabs(["📤 Upload", "🔍 Search"])

# Upload Tab
with tab1:
    st.subheader("Upload Medical Documents")
    st.markdown("Upload PDF documents to add them to the medical knowledge base.")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload medical documents, research papers, or health records"
    )
    
    if uploaded_file:
        st.markdown(f"""
        **File Details:**
        - 📄 Name: `{uploaded_file.name}`
        - 📊 Size: `{uploaded_file.size / 1024:.1f} KB`
        """)
        
        if st.button("📤 Upload & Process", type="primary", use_container_width=True):
            with st.spinner("Uploading and processing document..."):
                result = upload_document(uploaded_file)
            
            if result.get("status") == "accepted":
                st.success(f"✅ {result.get('message', 'Document uploaded successfully!')}")
                st.info("The document will be processed in the background. You can search for its content shortly.")
            else:
                st.error(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
    
    st.divider()
    st.caption("""
    **Supported Documents:**
    - Medical research papers
    - Clinical guidelines
    - Patient information sheets
    - Health education materials
    """)

# Search Tab
with tab2:
    st.subheader("Search Documents")
    st.markdown("Search through your uploaded medical documents using AI-powered semantic search.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Search query",
            placeholder="e.g., symptoms of diabetes, heart disease treatment...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_btn = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Specialty filter
    specialty_filter = st.selectbox(
        "Filter by specialty",
        ["All", "cardiology", "endocrinology", "neurology", "oncology", 
         "pediatrics", "gastroenterology", "infectious_disease", 
         "pulmonology", "dermatology", "orthopedics"],
        index=0
    )
    
    top_k = st.slider("Number of results", 1, 10, 5)
    
    if search_btn and query:
        with st.spinner("Searching..."):
            specialty = None if specialty_filter == "All" else specialty_filter
            results = search_documents(query, specialty=specialty, top_k=top_k)
        
        if "error" in results:
            st.error(f"Search error: {results['error']}")
        else:
            result_list = results.get("results", [])
            st.markdown(f"**Found {len(result_list)} results**")
            
            if not result_list:
                st.info("No documents found matching your query.")
            
            for i, doc in enumerate(result_list, 1):
                with st.container():
                    st.markdown(f"""
                    <div class="document-card">
                        <div style="margin-bottom: 0.5rem;">
                            <strong>#{i}</strong> 
                            <span class="specialty-badge">{doc.get('agent', 'general')}</span>
                            <span class="score-badge">Score: {doc.get('score', 0):.1f}</span>
                        </div>
                        <div style="font-size: 0.9rem; color: #333;">
                            {doc.get('text', 'No content')[:300]}...
                        </div>
                        <div style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">
                            📄 {doc.get('source_file', 'Unknown file')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Disclaimer
st.divider()
st.caption("⚠️ Uploaded documents are processed for medical information retrieval only.")
