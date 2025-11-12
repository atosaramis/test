"""
Grok Collections Chat - Chat with Samba Sales Menu
Simple chat interface for existing xAI collection using xAI SDK
"""

import streamlit as st
import os
from typing import List


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def chat_with_collection_sdk(collection_ids: List[str], user_message: str):
    """
    Chat with collections using xAI Python SDK.

    Args:
        collection_ids: List of collection IDs to search
        user_message: User's message

    Yields:
        Response chunks with content and citations
    """
    api_key = get_credential("XAI_API_KEY")

    if not api_key:
        yield {"error": "XAI_API_KEY not configured in secrets"}
        return

    try:
        from xai_sdk import Client
        from xai_sdk.chat import user, system
        from xai_sdk.tools import collections_search

        client = Client(api_key=api_key)

        chat = client.chat.create(
            model="grok-4-fast",
            tools=[
                collections_search(
                    collection_ids=collection_ids,
                    limit=6,
                ),
            ],
        )

        chat.append(system("You are a helpful assistant with access to Samba Scientific's sales menu and services. Answer questions accurately based on the retrieved documents."))
        chat.append(user(user_message))

        # Stream the response
        is_first_chunk = True
        for response, chunk in chat.stream():
            if is_first_chunk:
                yield {"status": "streaming"}
                is_first_chunk = False

            if chunk.content:
                yield {"content": chunk.content}

        # Return final response with citations
        yield {
            "done": True,
            "citations": response.citations if hasattr(response, 'citations') else []
        }

    except ImportError:
        yield {"error": "xai_sdk not installed. Run: pip install xai-sdk"}
    except Exception as e:
        yield {"error": f"SDK error: {str(e)}"}


def render_sales_chat_app():
    """Render the Samba Sales Menu Chat interface."""

    st.markdown("## 🎯 Samba Sales Menu Chat")
    st.caption("Chat with Samba Scientific's sales menu and services using AI")

    # Get collection ID from secrets
    collection_id = get_credential("SAMBA_SALES_MENU_COLLECTION_ID")
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
        st.error("❌ SAMBA_SALES_MENU_COLLECTION_ID not configured in secrets.toml")
        st.info("💡 Add your Samba Sales Menu collection ID to secrets.toml:\n\n`SAMBA_SALES_MENU_COLLECTION_ID = \"your_collection_id\"`")
        return

    if not api_key:
        st.error("❌ XAI_API_KEY not configured in secrets.toml")
        return

    # Initialize chat history
    if "sales_messages" not in st.session_state:
        st.session_state.sales_messages = []

    # Display chat history
    for message in st.session_state.sales_messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(content)

    # Chat input
    user_input = st.chat_input("Ask a question about Samba's sales menu...")

    if user_input:
        # Add user message
        st.session_state.sales_messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        # Stream response using SDK with spinner
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            has_error = False

            with st.spinner("🔍 Searching Samba's sales menu..."):
                for chunk in chat_with_collection_sdk([collection_id], user_input):
                    if chunk.get("error"):
                        st.error(f"❌ {chunk['error']}")
                        has_error = True
                        break

                    if chunk.get("content"):
                        full_response += chunk["content"]
                        response_placeholder.markdown(full_response + "▌")

            if not has_error:
                # Final response
                if full_response:
                    response_placeholder.markdown(full_response)
                else:
                    response_placeholder.warning("⚠️ No response generated.")

        # Add assistant message to history (only if we got a response)
        if not has_error and full_response:
            st.session_state.sales_messages.append({
                "role": "assistant",
                "content": full_response
            })

            st.rerun()

    # Clear chat button in sidebar
    with st.sidebar:
        if st.session_state.sales_messages:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.sales_messages = []
                st.rerun()
