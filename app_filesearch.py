"""
FileSearch Chat - Chat with Pre-Uploaded Google Gemini File Search Stores
Read-only interface for querying documents and media files using AI
"""

import streamlit as st
import os
from typing import List, Dict, Any, Optional
from google import genai


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def get_genai_client():
    """Get Google Gen AI client with API key."""
    api_key = get_credential("GOOGLE_GENAI_API_KEY")

    if not api_key:
        st.error("⚠️ GOOGLE_GENAI_API_KEY not configured in secrets")
        st.stop()

    client = genai.Client(api_key=api_key)
    return client


def list_file_search_stores(client) -> List[Dict[str, Any]]:
    """List all available File Search stores."""
    try:
        # List stores using the new Gen AI SDK (like Node.js version)
        stores_list = []

        # client.file_search_stores.list() returns a pager
        for store in client.file_search_stores.list(config={"page_size": 20}):
            stores_list.append({
                "name": store.name,
                "display_name": store.display_name,
                "active_documents_count": store.active_documents_count,
                "pending_documents_count": store.pending_documents_count,
                "failed_documents_count": store.failed_documents_count,
            })

        return stores_list
    except Exception as e:
        st.error(f"Error fetching stores: {str(e)}")
        return []


def chat_with_file_search(
    client,
    store_name: str,
    messages: List[Dict[str, str]],
    model_name: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """
    Chat with a File Search store using Gemini.

    Args:
        client: Google Gen AI client
        store_name: Full store name (e.g., "file_search_stores/abc123")
        messages: List of message dicts with 'role' and 'content'
        model_name: Gemini model to use

    Returns:
        Dict with answer, citations, media_files, and usage
    """
    try:
        # Get the latest user message
        user_message = messages[-1]["content"] if messages else ""
        # Clean up message - remove quotes and whitespace
        user_message = user_message.strip().strip('"').strip("'")

        # Call REST API directly since Python SDK file_search support is broken
        import requests
        import os

        api_key = os.environ.get("GOOGLE_GENAI_API_KEY") or st.secrets.get("GOOGLE_GENAI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }

        payload = {
            "contents": [{
                "parts": [{"text": user_message}]
            }],
            "tools": [{
                "file_search": {
                    "file_search_store_names": [store_name]
                }
            }]
        }

        # DEBUG: Log what we're sending
        st.write("DEBUG - Store name:", store_name)
        st.write("DEBUG - Payload:", payload)

        rest_response = requests.post(url, headers=headers, json=payload)

        # DEBUG: Log response
        st.write("DEBUG - Response status:", rest_response.status_code)
        st.write("DEBUG - Response:", rest_response.text[:500])

        rest_response.raise_for_status()
        response_data = rest_response.json()

        # Extract answer text from REST response
        answer = "No response generated."
        if "candidates" in response_data and len(response_data["candidates"]) > 0:
            candidate = response_data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                text_parts = [part.get("text", "") for part in candidate["content"]["parts"] if "text" in part]
                answer = "".join(text_parts)

        # Extract citations from grounding metadata
        citations = []
        media_files = []

        if "candidates" in response_data and len(response_data["candidates"]) > 0:
            candidate = response_data["candidates"][0]

            # Check for grounding metadata
            if "groundingMetadata" in candidate:
                grounding = candidate["groundingMetadata"]

                # Extract grounding chunks (document citations)
                if "groundingChunks" in grounding:
                    for i, chunk in enumerate(grounding["groundingChunks"]):
                        if "retrievedContext" in chunk:
                            retrieved = chunk["retrievedContext"]

                            citation = {
                                "id": f"citation-{i}",
                                "text": retrieved.get("text", ""),
                                "document_name": "Document",  # API limitation
                                "uri": retrieved.get("uri", "")
                            }
                            citations.append(citation)

        # Extract usage metadata
        usage = {}
        if "usageMetadata" in response_data:
            usage_meta = response_data["usageMetadata"]
            usage = {
                "input_tokens": usage_meta.get("promptTokenCount", 0),
                "output_tokens": usage_meta.get("candidatesTokenCount", 0),
                "total_tokens": usage_meta.get("totalTokenCount", 0),
            }

        return {
            "answer": answer,
            "citations": citations,
            "media_files": media_files,
            "usage": usage,
            "success": True
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            "answer": f"Error: {str(e)}",
            "citations": [],
            "media_files": [],
            "usage": {},
            "success": False,
            "error": str(e),
            "error_details": error_details
        }


def render_filesearch_app():
    """Render the FileSearch Chat application."""

    # Initialize client
    client = get_genai_client()

    # Page header
    st.markdown("## 📚 FileSearch Chat")
    st.markdown("Chat with pre-uploaded documents and media using Google Gemini AI")

    # Initialize session state
    if "filesearch_messages" not in st.session_state:
        st.session_state.filesearch_messages = []

    if "filesearch_selected_store" not in st.session_state:
        st.session_state.filesearch_selected_store = None

    if "filesearch_last_store" not in st.session_state:
        st.session_state.filesearch_last_store = None

    if "filesearch_stores" not in st.session_state:
        st.session_state.filesearch_stores = []

    # Load stores on first render
    if not st.session_state.filesearch_stores:
        with st.spinner("Loading file search stores..."):
            st.session_state.filesearch_stores = list_file_search_stores(client)

    # Main page - Knowledge Base Selection
    st.markdown("### 📂 Select Knowledge Base")

    col1, col2 = st.columns([3, 1])

    with col1:
        if st.session_state.filesearch_stores:
            store_options = {
                store["display_name"]: store["name"]
                for store in st.session_state.filesearch_stores
            }

            selected_display_name = st.selectbox(
                "Knowledge Base",
                options=list(store_options.keys()),
                index=0,
                label_visibility="collapsed"
            )

            st.session_state.filesearch_selected_store = store_options[selected_display_name]

            # Clear messages if store changed
            if st.session_state.filesearch_last_store != st.session_state.filesearch_selected_store:
                st.session_state.filesearch_messages = []
                st.session_state.filesearch_last_store = st.session_state.filesearch_selected_store
        else:
            st.warning("No File Search stores found. Please create stores using Google AI Studio.")
            st.session_state.filesearch_selected_store = None

    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            with st.spinner("Refreshing..."):
                st.session_state.filesearch_stores = list_file_search_stores(client)
                st.rerun()

    if st.session_state.filesearch_selected_store and st.session_state.filesearch_stores:
        # Find the selected store details
        selected_store = next(
            (s for s in st.session_state.filesearch_stores if s["name"] == st.session_state.filesearch_selected_store),
            None
        )

        st.success(f"✅ Connected to: **{selected_display_name}**")

        # Display document counts
        if selected_store:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Active Documents", selected_store.get("active_documents_count", 0))
            with col2:
                st.metric("⏳ Pending", selected_store.get("pending_documents_count", 0))
            with col3:
                st.metric("❌ Failed", selected_store.get("failed_documents_count", 0))

            # Warning if no active documents
            if selected_store.get("active_documents_count", 0) == 0:
                if selected_store.get("pending_documents_count", 0) > 0:
                    st.warning("⏳ Files are still being indexed. Please wait and refresh.")
                else:
                    st.warning("⚠️ This store has no documents. Upload files to this store in Google AI Studio.")

    st.markdown("---")

    # Sidebar - Settings
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        model_name = st.selectbox(
            "Model",
            options=["gemini-2.5-flash", "gemini-2.5-pro"],
            index=0,
            help="⚠️ ONLY Gemini 2.5 models support File Search"
        )

        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.filesearch_messages = []
            st.rerun()

        # Token usage summary
        if st.session_state.filesearch_messages:
            st.divider()
            st.markdown("### 📊 Token Usage")

            total_input = 0
            total_output = 0

            for msg in st.session_state.filesearch_messages:
                if "usage" in msg and msg["usage"]:
                    total_input += msg["usage"].get("input_tokens", 0)
                    total_output += msg["usage"].get("output_tokens", 0)

            st.metric("Input Tokens", f"{total_input:,}")
            st.metric("Output Tokens", f"{total_output:,}")
            st.metric("Total Tokens", f"{total_input + total_output:,}")

    # Main chat area
    if not st.session_state.filesearch_selected_store:
        st.info("👆 Please enter your corpus name above to start chatting.")
        st.markdown("""
        **How to get your corpus name:**
        1. Go to [Google AI Studio](https://aistudio.google.com/)
        2. Navigate to your File Search stores/corpora
        3. Copy the corpus ID (e.g., `corpora/abc123xyz`)
        4. Paste it above and click Connect
        """)
        return

    # Display chat messages
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.filesearch_messages:
            with st.chat_message(message["role"]):
                # Check if this is an error message
                if message.get("error"):
                    st.error(message["content"])
                    if message.get("error_details"):
                        with st.expander("🔍 Error Details"):
                            st.code(message["error_details"])
                else:
                    st.markdown(message["content"])

                # Display citations for assistant messages
                if message["role"] == "assistant" and not message.get("error"):
                    # Media files (images)
                    if "media_files" in message and message["media_files"]:
                        st.markdown("---")
                        st.markdown("**📷 Images Provided:**")

                        cols = st.columns(min(len(message["media_files"]), 3))
                        for i, media in enumerate(message["media_files"]):
                            with cols[i % 3]:
                                st.markdown(
                                    f'<span style="background-color: #ff6b6b; color: white; '
                                    f'padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">'
                                    f'{media["name"]}</span>',
                                    unsafe_allow_html=True
                                )

                    # Document citations
                    if "citations" in message and message["citations"]:
                        st.markdown("---")
                        st.markdown("**📄 Document Sources:**")

                        for citation in message["citations"]:
                            with st.expander(f"📖 {citation['document_name']}", expanded=False):
                                st.markdown(f"_{citation['text']}_")

                    # Token usage
                    if "usage" in message and message["usage"]:
                        usage = message["usage"]
                        st.caption(
                            f"_Tokens: {usage.get('input_tokens', 0):,} in / "
                            f"{usage.get('output_tokens', 0):,} out / "
                            f"{usage.get('total_tokens', 0):,} total_"
                        )

    # Chat input
    user_input = st.chat_input("Ask a question about your documents...")

    if user_input:
        # Add user message
        st.session_state.filesearch_messages.append({
            "role": "user",
            "content": user_input
        })

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Prepare message history for API
                api_messages = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state.filesearch_messages
                ]

                # Call File Search API
                response = chat_with_file_search(
                    client=client,
                    store_name=st.session_state.filesearch_selected_store,
                    messages=api_messages,
                    model_name=model_name
                )

                if response["success"]:
                    # Display answer
                    st.markdown(response["answer"])

                    # Display media files
                    if response["media_files"]:
                        st.markdown("---")
                        st.markdown("**📷 Images Provided:**")

                        cols = st.columns(min(len(response["media_files"]), 3))
                        for i, media in enumerate(response["media_files"]):
                            with cols[i % 3]:
                                st.markdown(
                                    f'<span style="background-color: #ff6b6b; color: white; '
                                    f'padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">'
                                    f'{media["name"]}</span>',
                                    unsafe_allow_html=True
                                )

                    # Display citations
                    if response["citations"]:
                        st.markdown("---")
                        st.markdown("**📄 Document Sources:**")

                        for citation in response["citations"]:
                            with st.expander(f"📖 {citation['document_name']}", expanded=False):
                                st.markdown(f"_{citation['text']}_")

                    # Display usage
                    if response["usage"]:
                        usage = response["usage"]
                        st.caption(
                            f"_Tokens: {usage.get('input_tokens', 0):,} in / "
                            f"{usage.get('output_tokens', 0):,} out / "
                            f"{usage.get('total_tokens', 0):,} total_"
                        )

                    # Add assistant message to history
                    st.session_state.filesearch_messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "citations": response["citations"],
                        "media_files": response["media_files"],
                        "usage": response["usage"]
                    })

                    # Only rerun on success
                    st.rerun()
                else:
                    # Display error
                    error_msg = f"❌ Error: {response.get('error', 'Unknown error')}"
                    st.error(error_msg)
                    if "error_details" in response:
                        with st.expander("🔍 Error Details"):
                            st.code(response["error_details"])

                    # Save error to session state so it persists
                    st.session_state.filesearch_messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "citations": [],
                        "media_files": [],
                        "usage": {},
                        "error": True,
                        "error_details": response.get("error_details", "")
                    })
                    # Rerun to show the error in history
                    st.rerun()
