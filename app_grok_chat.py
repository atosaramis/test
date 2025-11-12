"""
Grok Collections Chat - Chat with Samba Scientific Knowledge Base
Uses xAI Collections API for RAG (Retrieval Augmented Generation)
"""

import streamlit as st
import os
import requests
from typing import Dict, List, Optional
import json
import time


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def create_collection(name: str, description: str = None) -> Optional[Dict]:
    """
    Create a new collection using xAI API.

    Args:
        name: Name of the collection
        description: Optional description

    Returns:
        Collection object or None if error
    """
    api_key = get_credential("XAI_API_KEY")

    if not api_key:
        return {"error": "XAI_API_KEY not configured in secrets"}

    url = "https://api.x.ai/v1/collections"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "description": description or f"Collection: {name}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to create collection: {str(e)}"}


def list_collections() -> Dict:
    """List all collections."""
    api_key = get_credential("XAI_API_KEY")

    if not api_key:
        return {"error": "XAI_API_KEY not configured in secrets"}

    url = "https://api.x.ai/v1/collections"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to list collections: {str(e)}"}


def upload_file_to_collection(collection_id: str, file_content: bytes, filename: str) -> Optional[Dict]:
    """
    Upload a file to a collection.

    Args:
        collection_id: ID of the collection
        file_content: File content as bytes
        filename: Name of the file

    Returns:
        File object or None if error
    """
    api_key = get_credential("XAI_API_KEY")

    if not api_key:
        return {"error": "XAI_API_KEY not configured in secrets"}

    url = f"https://api.x.ai/v1/collections/{collection_id}/files"
    headers = {"Authorization": f"Bearer {api_key}"}

    files = {"file": (filename, file_content)}

    try:
        response = requests.post(url, headers=headers, files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to upload file: {str(e)}"}


def chat_with_collection(
    collection_ids: List[str],
    messages: List[Dict],
    stream: bool = True
):
    """
    Chat with collections using xAI API.

    Args:
        collection_ids: List of collection IDs to search
        messages: Chat messages
        stream: Whether to stream response

    Yields:
        Response chunks if streaming, or returns full response
    """
    api_key = get_credential("XAI_API_KEY")

    if not api_key:
        yield {"error": "XAI_API_KEY not configured in secrets"}
        return

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-4-fast",
        "messages": messages,
        "stream": stream,
        "tools": [
            {
                "type": "collections_search",
                "collections_search": {
                    "collection_ids": collection_ids,
                    "limit": 6
                }
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120, stream=stream)
        response.raise_for_status()

        if stream:
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            yield chunk
                        except json.JSONDecodeError:
                            continue
        else:
            yield response.json()

    except requests.exceptions.RequestException as e:
        yield {"error": f"Chat failed: {str(e)}"}


def render_grok_chat_app():
    """Render the Grok Collections Chat interface."""

    st.markdown("## 🤖 Chat with Samba Scientific Knowledge Base")
    st.caption("Powered by Grok and xAI Collections - RAG (Retrieval Augmented Generation)")

    # Tabs: Chat, Manage Collections, Upload Files
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📚 Collections", "📤 Upload Files"])

    # ============================================================================
    # TAB 1: CHAT INTERFACE
    # ============================================================================
    with tab1:
        st.markdown("### Chat with Your Knowledge Base")
        st.caption("Ask questions and Grok will search your collections to provide accurate answers with citations")

        # Load collections
        collections_response = list_collections()

        if collections_response.get("error"):
            st.error(f"❌ {collections_response['error']}")
            st.info("💡 Make sure XAI_API_KEY is set in your secrets.toml")
            return

        collections = collections_response.get("data", [])

        if not collections:
            st.warning("📭 No collections yet. Go to the 'Collections' tab to create one!")
            return

        # Collection selector
        collection_options = {f"{c.get('name', 'Unknown')} ({c.get('id', '')[:8]}...)": c.get('id') for c in collections}

        selected_collection_names = st.multiselect(
            "Select collections to search",
            options=list(collection_options.keys()),
            default=list(collection_options.keys())[:1],
            help="Choose which knowledge bases to search"
        )

        if not selected_collection_names:
            st.warning("⚠️ Please select at least one collection to chat with")
            return

        selected_collection_ids = [collection_options[name] for name in selected_collection_names]

        st.divider()

        # Initialize chat history
        if "grok_messages" not in st.session_state:
            st.session_state.grok_messages = []

        # Display chat history
        for message in st.session_state.grok_messages:
            role = message["role"]
            content = message["content"]

            if role == "user":
                st.markdown(f"**You:** {content}")
            elif role == "assistant":
                st.markdown(f"**Grok:** {content}")
                if message.get("citations"):
                    with st.expander("📎 Sources"):
                        for i, citation in enumerate(message["citations"], 1):
                            st.caption(f"{i}. {citation}")

        # Chat input
        user_input = st.chat_input("Ask a question about Samba Scientific...")

        if user_input:
            # Add user message
            st.session_state.grok_messages.append({"role": "user", "content": user_input})
            st.markdown(f"**You:** {user_input}")

            # Prepare messages for API
            api_messages = [
                {"role": "system", "content": "You are a helpful assistant with access to Samba Scientific's knowledge base. Answer questions accurately based on the retrieved documents and provide citations."},
            ]

            for msg in st.session_state.grok_messages:
                if msg["role"] in ["user", "assistant"]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})

            # Stream response
            response_placeholder = st.empty()
            full_response = ""
            citations = []

            with st.spinner("🤔 Searching knowledge base..."):
                for chunk in chat_with_collection(selected_collection_ids, api_messages, stream=True):
                    if chunk.get("error"):
                        st.error(f"❌ {chunk['error']}")
                        break

                    if "choices" in chunk:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")

                        if content:
                            full_response += content
                            response_placeholder.markdown(f"**Grok:** {full_response}▌")

                    # Capture citations if present
                    if "citations" in chunk:
                        citations = chunk["citations"]

            # Final response
            response_placeholder.markdown(f"**Grok:** {full_response}")

            # Show citations
            if citations:
                with st.expander("📎 Sources"):
                    for i, citation in enumerate(citations, 1):
                        st.caption(f"{i}. {citation}")

            # Add assistant message to history
            st.session_state.grok_messages.append({
                "role": "assistant",
                "content": full_response,
                "citations": citations
            })

            st.rerun()

        # Clear chat button
        if st.session_state.grok_messages:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.grok_messages = []
                st.rerun()

    # ============================================================================
    # TAB 2: MANAGE COLLECTIONS
    # ============================================================================
    with tab2:
        st.markdown("### Your Collections")
        st.caption("Collections are knowledge bases that store your files with searchable embeddings")

        # Create new collection
        with st.expander("➕ Create New Collection"):
            new_collection_name = st.text_input("Collection Name", placeholder="e.g., Samba Scientific Knowledge Base")
            new_collection_desc = st.text_area("Description", placeholder="Optional description of this collection")

            if st.button("Create Collection", type="primary"):
                if not new_collection_name.strip():
                    st.error("Please enter a collection name")
                else:
                    with st.spinner("Creating collection..."):
                        result = create_collection(new_collection_name, new_collection_desc)

                        if result.get("error"):
                            st.error(f"❌ {result['error']}")
                        else:
                            st.success(f"✅ Created collection: {new_collection_name}")
                            time.sleep(1)
                            st.rerun()

        st.divider()

        # List existing collections
        collections_response = list_collections()

        if collections_response.get("error"):
            st.error(f"❌ {collections_response['error']}")
        else:
            collections = collections_response.get("data", [])

            if not collections:
                st.info("📭 No collections yet. Create one above!")
            else:
                st.write(f"**{len(collections)} collections**")

                for collection in collections:
                    with st.expander(f"📚 {collection.get('name', 'Unknown')}"):
                        st.write(f"**ID:** `{collection.get('id', 'N/A')}`")
                        st.write(f"**Description:** {collection.get('description', 'No description')}")
                        st.write(f"**Created:** {collection.get('created_at', 'Unknown')}")
                        st.write(f"**Files:** {collection.get('file_count', 0)} files")

    # ============================================================================
    # TAB 3: UPLOAD FILES
    # ============================================================================
    with tab3:
        st.markdown("### Upload Files to Collection")
        st.caption("Upload documents to your collection - supports PDFs, text files, CSVs, and more")

        # Load collections
        collections_response = list_collections()

        if collections_response.get("error"):
            st.error(f"❌ {collections_response['error']}")
            return

        collections = collections_response.get("data", [])

        if not collections:
            st.warning("📭 No collections yet. Go to the 'Collections' tab to create one first!")
            return

        # Collection selector
        collection_options = {f"{c.get('name', 'Unknown')} ({c.get('id', '')[:8]}...)": c.get('id') for c in collections}

        selected_collection_name = st.selectbox(
            "Select collection to upload to",
            options=list(collection_options.keys()),
            help="Choose which collection to add files to"
        )

        selected_collection_id = collection_options[selected_collection_name]

        st.divider()

        # File uploader
        uploaded_files = st.file_uploader(
            "Upload files",
            accept_multiple_files=True,
            type=["txt", "pdf", "csv", "md", "json"],
            help="Upload multiple files at once"
        )

        if uploaded_files:
            st.write(f"**{len(uploaded_files)} files selected**")

            if st.button("📤 Upload Files", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Uploading {uploaded_file.name}...")

                    file_content = uploaded_file.read()
                    result = upload_file_to_collection(selected_collection_id, file_content, uploaded_file.name)

                    if result.get("error"):
                        st.error(f"❌ Failed to upload {uploaded_file.name}: {result['error']}")
                    else:
                        st.success(f"✅ Uploaded {uploaded_file.name}")

                    progress_bar.progress((i + 1) / len(uploaded_files))

                status_text.text("Upload complete!")
                time.sleep(1)
                st.rerun()
