"""
Grok Collections Chat - Chat with Samba Scientific Knowledge Base
Simple chat interface for existing xAI collection
"""

import streamlit as st
import os
import requests
from typing import Dict, List
import json


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


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

        # Check for HTTP errors
        if response.status_code != 200:
            error_text = response.text
            yield {"error": f"API Error {response.status_code}: {error_text}"}
            return

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
                        except json.JSONDecodeError as e:
                            # Yield parsing error for debugging
                            yield {"error": f"JSON parse error: {str(e)}, data: {data[:100]}"}
                            continue
        else:
            yield response.json()

    except requests.exceptions.Timeout:
        yield {"error": "Request timed out after 120 seconds"}
    except requests.exceptions.RequestException as e:
        yield {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        yield {"error": f"Unexpected error: {str(e)}"}


def render_grok_chat_app():
    """Render the Grok Collections Chat interface."""

    st.markdown("## 🤖 Chat with Samba Scientific Knowledge Base")
    st.caption("Powered by Grok and xAI Collections - Ask questions about Samba Scientific")

    # Get collection ID from secrets
    collection_id = get_credential("SAMBA_COLLECTION_ID")
    api_key = get_credential("XAI_API_KEY")

    # Debug info in sidebar
    with st.sidebar:
        st.markdown("### Debug Info")
        if api_key:
            st.success(f"✅ API Key: {api_key[:10]}...{api_key[-5:]}")
        else:
            st.error("❌ No API Key")

        if collection_id:
            st.success(f"✅ Collection: {collection_id[:8]}...")
        else:
            st.error("❌ No Collection ID")

    if not collection_id:
        st.error("❌ SAMBA_COLLECTION_ID not configured in secrets.toml")
        st.info("💡 Add your Samba Scientific collection ID to secrets.toml:\n\n`SAMBA_COLLECTION_ID = \"your_collection_id\"`")
        return

    if not api_key:
        st.error("❌ XAI_API_KEY not configured in secrets.toml")
        return

    # Initialize chat history
    if "grok_messages" not in st.session_state:
        st.session_state.grok_messages = []

    # Display chat history
    for message in st.session_state.grok_messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(content)
                if message.get("citations"):
                    with st.expander("📎 Sources"):
                        for i, citation in enumerate(message["citations"], 1):
                            st.caption(f"{i}. {citation}")

    # Chat input
    user_input = st.chat_input("Ask a question about Samba Scientific...")

    if user_input:
        # Add user message
        st.session_state.grok_messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        # Prepare messages for API
        api_messages = [
            {"role": "system", "content": "You are a helpful assistant with access to Samba Scientific's knowledge base. Answer questions accurately based on the retrieved documents and provide citations."},
        ]

        for msg in st.session_state.grok_messages:
            if msg["role"] in ["user", "assistant"]:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Stream response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            debug_placeholder = st.empty()
            full_response = ""
            citations = []
            has_error = False

            chunk_count = 0
            for chunk in chat_with_collection([collection_id], api_messages, stream=True):
                chunk_count += 1
                debug_placeholder.caption(f"Processing chunk {chunk_count}...")

                if chunk.get("error"):
                    st.error(f"❌ {chunk['error']}")
                    has_error = True
                    break

                if "choices" in chunk:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")

                    if content:
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")

                # Capture citations if present
                if "citations" in chunk:
                    citations = chunk["citations"]

            debug_placeholder.empty()

            if not has_error:
                # Final response
                if full_response:
                    response_placeholder.markdown(full_response)
                else:
                    response_placeholder.warning("⚠️ No response generated. Grok may still be processing or there was an issue.")

                # Show citations
                if citations:
                    with st.expander("📎 Sources"):
                        for i, citation in enumerate(citations, 1):
                            st.caption(f"{i}. {citation}")

        # Add assistant message to history (only if we got a response)
        if not has_error and full_response:
            st.session_state.grok_messages.append({
                "role": "assistant",
                "content": full_response,
                "citations": citations
            })

            st.rerun()

    # Clear chat button in sidebar
    with st.sidebar:
        if st.session_state.grok_messages:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.grok_messages = []
                st.rerun()
