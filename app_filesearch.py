"""
FileSearch Chat - Chat with Pre-Uploaded Google Gemini File Search Stores
Read-only interface for querying documents and media files using AI
"""

import streamlit as st
import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def initialize_gemini_client():
    """Initialize Google Gemini client with API key."""
    api_key = get_credential("GOOGLE_GENAI_API_KEY")

    if not api_key:
        st.error("⚠️ GOOGLE_GENAI_API_KEY not configured in secrets")
        st.stop()

    genai.configure(api_key=api_key)
    return genai


def list_file_search_stores() -> List[Dict[str, Any]]:
    """List all available File Search stores (corpora)."""
    try:
        # List corpora using the Gemini API
        corpora = genai.list_corpora(page_size=20)

        store_list = []
        for corpus in corpora:
            store_list.append({
                "name": corpus.name,  # e.g., "corpora/abc123"
                "display_name": corpus.display_name,
                "create_time": corpus.create_time if hasattr(corpus, 'create_time') else None,
            })

        return store_list
    except Exception as e:
        st.error(f"Error fetching stores: {str(e)}")
        return []


def chat_with_file_search(
    store_name: str,
    messages: List[Dict[str, str]],
    model_name: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """
    Chat with a File Search store using Gemini.

    Args:
        store_name: Full store name (e.g., "fileSearchStores/abc123")
        messages: List of message dicts with 'role' and 'content'
        model_name: Gemini model to use

    Returns:
        Dict with answer, citations, media_files, and usage
    """
    try:
        # Build the contents array for Gemini
        contents = []

        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        # Configure the model with retrieval tool
        # Create a retrieval tool that uses the corpus
        retrieval_tool = genai.protos.Tool(
            retrieval=genai.protos.Retrieval(
                vertex_rag_store=genai.protos.VertexRagStore(
                    rag_corpora=[store_name]
                )
            )
        )

        model = genai.GenerativeModel(
            model_name=model_name,
            tools=[retrieval_tool],
            system_instruction="""You are a helpful AI assistant with access to uploaded documents and media files.

Answer questions accurately based on the retrieved information.

FORMATTING RULES:
- Use **bold** for emphasis when needed
- Use bullet points (-, *, or numbered lists) for lists
- Add clear paragraph breaks between sections
- When citing information, be specific about sources when possible
- Keep formatting clean and readable
- Provide detailed, comprehensive answers when appropriate"""
        )

        # Generate response
        response = model.generate_content(contents)

        # Extract answer text
        answer = response.text if response.text else "No response generated."

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
        return {
            "answer": f"Error: {str(e)}",
            "citations": [],
            "media_files": [],
            "usage": {},
            "success": False,
            "error": str(e)
        }


def render_filesearch_app():
    """Render the FileSearch Chat application."""

    # Initialize client
    initialize_gemini_client()

    # Page header
    st.markdown("## 📚 FileSearch Chat")
    st.markdown("Chat with pre-uploaded documents and media using Google Gemini AI")

    # Initialize session state
    if "filesearch_messages" not in st.session_state:
        st.session_state.filesearch_messages = []

    if "filesearch_selected_store" not in st.session_state:
        st.session_state.filesearch_selected_store = None

    if "filesearch_stores" not in st.session_state:
        st.session_state.filesearch_stores = []

    # Load stores on first render
    if not st.session_state.filesearch_stores:
        with st.spinner("Loading knowledge bases..."):
            st.session_state.filesearch_stores = list_file_search_stores()

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
        else:
            st.warning("No File Search stores found. Please create stores using Google AI Studio.")
            st.session_state.filesearch_selected_store = None

    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            with st.spinner("Refreshing..."):
                st.session_state.filesearch_stores = list_file_search_stores()
                st.rerun()

    if st.session_state.filesearch_selected_store and st.session_state.filesearch_stores:
        st.success(f"✅ Connected to: **{selected_display_name}**")

    st.markdown("---")

    # Sidebar - Settings
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        model_name = st.selectbox(
            "Model",
            options=["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
            index=0
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
        st.info("👆 Please select a knowledge base above to start chatting.")
        return

    # Display chat messages
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.filesearch_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Display citations for assistant messages
                if message["role"] == "assistant":
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
                else:
                    st.error(f"Error: {response.get('error', 'Unknown error')}")

        st.rerun()
