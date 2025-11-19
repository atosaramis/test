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
            })

        return stores_list
    except Exception as e:
        st.error(f"Error fetching stores: {str(e)}")
        return []


def chat_with_file_search(
    client,
    store_name: str,
    messages: List[Dict[str, str]],
    model_name: str = "gemini-2.0-flash-exp"
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

        # Configure file search tool - using EXACT syntax from Google documentation
        from google.genai import types

        # Create the config exactly as shown in official docs
        response = client.models.generate_content(
            model=model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[store_name]
                        )
                    )
                ],
                system_instruction="You are a helpful AI assistant with access to uploaded documents. Answer questions accurately based on the retrieved information."
            )
        )

        # Extract answer text
        answer = response.text if hasattr(response, 'text') and response.text else "No response generated."

        # Extract citations from grounding metadata
        citations = []
        media_files = []

        if hasattr(response, 'candidates') and len(response.candidates) > 0:
            candidate = response.candidates[0]

            # Check for grounding metadata
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                grounding = candidate.grounding_metadata

                # Extract grounding chunks (document citations)
                if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                    for i, chunk in enumerate(grounding.grounding_chunks):
                        if hasattr(chunk, 'retrieved_context'):
                            retrieved = chunk.retrieved_context

                            citation = {
                                "id": f"citation-{i}",
                                "text": retrieved.text if hasattr(retrieved, 'text') else "",
                                "document_name": "Document",  # API limitation
                                "uri": retrieved.uri if hasattr(retrieved, 'uri') else ""
                            }
                            citations.append(citation)

        # Extract usage metadata
        usage = {}
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage_meta = response.usage_metadata
            usage = {
                "input_tokens": usage_meta.prompt_token_count if hasattr(usage_meta, 'prompt_token_count') else 0,
                "output_tokens": usage_meta.candidates_token_count if hasattr(usage_meta, 'candidates_token_count') else 0,
                "total_tokens": usage_meta.total_token_count if hasattr(usage_meta, 'total_token_count') else 0,
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
        st.success(f"✅ Connected to: **{selected_display_name}**")

    st.markdown("---")

    # Sidebar - Settings
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        model_name = st.selectbox(
            "Model",
            options=["gemini-2.0-flash-exp", "gemini-2.5-flash", "gemini-1.5-pro"],
            index=0,
            help="File Search requires Gemini 2.0+ models"
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
