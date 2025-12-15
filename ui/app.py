# ... Placeholder ...
import uuid
import time
from config import config
from api_client import api_client
import requests
import streamlit as st

# Page Config
st.set_page_config(
    page_title=config.PAGE_TITLE, 
    page_icon=config.PAGE_ICON, 
    layout="wide"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "backend_reachable" not in st.session_state:
    st.session_state.backend_reachable = True # Assume true initially

# Helper: Check Backend Health
def check_backend():
    try:
        # Simple health check URL construction
        health_url = config.API_BASE_url.replace("/api/v1", "/health")
        requests.get(health_url, timeout=2)
        return True
    except:
        return False

# Sidebar
# Sidebar
# Sidebar
with st.sidebar:
    st.title("RAG Pipeline")
    
    # Refresh logic first to ensure categories are up to date
    if "doc_list" not in st.session_state:
         try:
            res = requests.get(f"{config.API_BASE_url}/docs/documents", timeout=5)
            if res.status_code == 200:
                st.session_state["doc_list"] = res.json().get("documents", [])
         except: pass

    # Derive existing categories
    existing_cats = set(d.get("category", "Uncategorized") for d in st.session_state.get("doc_list", []))
    existing_cats.update(["Uncategorized", "Legal", "Medical", "Financial", "Research"])
    sorted_cats = sorted(list(existing_cats))

    # --- 1. Ingestion ---
    with st.expander("📥 Ingest Documents", expanded=True):
        ingest_mode = st.radio("Category:", ["Existing", "New"], horizontal=True, label_visibility="collapsed")
        if ingest_mode == "Existing":
            target_category = st.selectbox("Select Category", sorted_cats)
        else:
            target_category = st.text_input("New Category", value="NewCategory")

        uploaded_files = st.file_uploader("Files", accept_multiple_files=True, label_visibility="collapsed")
        
        if uploaded_files:
            if st.button(f"Upload to '{target_category}'", use_container_width=True):
                progress_bar = st.progress(0)
                for idx, file_obj in enumerate(uploaded_files):
                    try:
                        api_client.ingest_file(file_obj, category=target_category)
                        st.toast(f"Ingested {file_obj.name}")
                    except Exception as e:
                        st.error(f"Error {file_obj.name}: {e}")
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                time.sleep(1)
                st.rerun()

    # --- 2. Knowledge Base ---
    st.markdown("### Knowledge Base")
    col_ref, col_info = st.columns([0.3, 0.7])
    if col_ref.button("🔄", help="Refresh Documents"):
        try:
            res = requests.get(f"{config.API_BASE_url}/docs/documents", timeout=5)
            if res.status_code == 200:
                st.session_state["doc_list"] = res.json().get("documents", [])
                st.rerun()
        except: pass

    selected_docs = []
    
    if "doc_list" in st.session_state and st.session_state["doc_list"]:
        # Group Docs
        docs_by_cat = {}
        for d in st.session_state["doc_list"]:
            c = d.get("category", "Uncategorized")
            if c not in docs_by_cat: docs_by_cat[c] = []
            docs_by_cat[c].append(d)
        
        # Display Categories
        for cat in sorted(docs_by_cat.keys()):
            docs = docs_by_cat[cat]
            if not docs: continue # Skip empty if any

            with st.expander(f"📂 {cat} ({len(docs)})", expanded=False):
                # Category Header Actions
                h_col1, h_col2 = st.columns([0.8, 0.2])
                if h_col1.checkbox("Select All", key=f"sel_all_{cat}"):
                     for d in docs: selected_docs.append(d['filename'])
                
                # Delete Category Button
                if h_col2.button("🗑️", key=f"del_cat_{cat}", help="Delete Entire Category"):
                     try:
                         # Backend call to delete category
                         requests.delete(f"{config.API_BASE_url}/docs/category", params={"category": cat})
                         st.toast(f"Deleted category {cat}")
                         time.sleep(1)
                         st.rerun()
                     except Exception as e:
                         st.error(f"Failed: {e}")

                # List Docs
                for d in docs:
                     if st.checkbox(f"📄 {d['filename']}", key=f"chk_{d['filename']}"):
                         if d['filename'] not in selected_docs:
                             selected_docs.append(d['filename'])
    else:
        st.caption("No documents.")

    # Actions on Selection
    if selected_docs:
        st.markdown("---")
        st.caption(f"Selected: {len(set(selected_docs))} docs")
        
        if st.button("🗑️ Delete Selected", use_container_width=True):
            for fname in set(selected_docs):
                    requests.delete(f"{config.API_BASE_url}/docs/delete", params={"filename": fname})
            st.success("Deleted selection.")
            time.sleep(0.5)
            st.rerun()

    # --- 3. Settings ---
    st.markdown("---")
    with st.expander("⚙️ Advanced Settings"):
        model_name = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4-turbo-preview", "local-test"], index=0)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        top_k = st.slider("Top-K Documents", 1, 10, 3)
        use_reranker = st.checkbox("Enable Reranking", value=True)
        citation_mode = st.checkbox("Show Citations", value=True)
        st.session_state["show_sources"] = citation_mode

    # --- 4. Chat Management ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()
    with col2:
        if st.button("Clear History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()

# Main Chat Interface
st.title(f"{config.PAGE_ICON} {config.PAGE_TITLE}")

# Backend Health Warning
if not st.session_state.get("backend_checked", False):
    if not check_backend():
        st.error("⚠️ Backend API is not reachable. Please ensure the server is running.")
        st.session_state.backend_reachable = False
    else:
        st.session_state.backend_reachable = True
    st.session_state.backend_checked = True

if not st.session_state.backend_reachable:
    st.warning("Running in offline mode. Interactions may fail.")

# Empty State
if not st.session_state.messages:
    st.markdown(
        """
        ### Welcome to the Multimodal RAG Demo! 👋
        
        Get started by **uploading documents** in the sidebar. 
        Supported formats:
        - 📄 PDFs
        - 🖼️ Images
        - 🎧 Audio/Video
        
        Then ask questions regarding your documents below.
        """
    )

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
input_disabled = st.session_state.get("generating", False) or not st.session_state.backend_reachable
if prompt := st.chat_input("Ask about your documents...", disabled=input_disabled):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        st.session_state["generating"] = True
        
        try:
            # Gather options
            options = {
                "model": model_name,
                "temperature": temperature,
                "top_k": top_k,
                "use_reranker": use_reranker,
                "citation_mode": citation_mode,
                "filters": {"source_filename": selected_docs} if selected_docs else None # Pass list of filenames
            }
            
            # Stream generator
            stream = api_client.chat_stream(prompt, st.session_state.session_id, options=options)
            
            for packet in stream:
                if "error" in packet:
                    full_response = packet['error']
                    # Friendly error formatting
                    st.error(f"Backend Error: {full_response}")
                    message_placeholder.markdown("🚨 *An error occurred while generating response.*")
                    break
                
                if "session_id" in packet:
                    if not st.session_state.session_id:
                        st.session_state.session_id = packet["session_id"]
                    continue
                
                if "sources" in packet and st.session_state.get("show_sources", True):
                    with st.expander("Retrieved Sources", expanded=False):
                        if not packet["sources"]:
                            st.info("No relevant documents found.")
                        for src in packet["sources"]:
                             st.markdown(f"- **{src.get('source_filename', 'Doc')}** (Page {src.get('page_number', '-')}) - Score: {src.get('score', 0):.2f}")

                if "content" in packet:
                    full_response += packet["content"]
                    # Add cursor
                    message_placeholder.markdown(full_response + "▌")
            
            if full_response and not full_response.startswith("Error"):
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Application Error: {str(e)}")
        finally:
             st.session_state["generating"] = False
             st.rerun() # Force rerun to re-enable input immediately
