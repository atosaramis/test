"""
Claude Skills Content Generator - Generate Samba blog posts and LinkedIn content
Processes text content using custom Claude skills via Anthropic API
"""

import streamlit as st
import os
from typing import Optional, Dict, Any


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def execute_skill(skill_id: str, content: str, model: str = "claude-sonnet-4-5-20250929", max_tokens: int = 4096) -> Optional[Dict[str, Any]]:
    """
    Execute a Claude skill with provided content.

    Args:
        skill_id: The skill ID to execute
        content: The content to process
        model: Claude model to use
        max_tokens: Maximum tokens for response

    Returns:
        API response or None if error
    """
    api_key = get_credential("ANTHROPIC_API_KEY")

    if not api_key:
        st.error("❌ ANTHROPIC_API_KEY not configured")
        st.info("💡 Add ANTHROPIC_API_KEY to secrets.toml")
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Execute skill
        response = client.beta.messages.create(
            model=model,
            max_tokens=max_tokens,
            betas=["code-execution-2025-08-25", "skills-2025-10-02"],
            container={
                "skills": [
                    {
                        "type": "custom",
                        "skill_id": skill_id,
                        "version": "latest"
                    }
                ]
            },
            messages=[
                {
                    "role": "user",
                    "content": f"Process this content:\n\n{content}"
                }
            ],
            tools=[
                {
                    "type": "code_execution_20250825",
                    "name": "code_execution"
                }
            ]
        )

        return response

    except ImportError:
        st.error("❌ Anthropic SDK not installed. Run: pip install anthropic")
        return None
    except Exception as e:
        st.error(f"❌ Error executing skill: {str(e)}")
        return None


def extract_text_from_response(response) -> str:
    """Extract text content from API response."""
    if not response or not hasattr(response, 'content'):
        return ""

    text_parts = []
    for block in response.content:
        if hasattr(block, 'text'):
            text_parts.append(block.text)
        elif block.type == 'text':
            text_parts.append(block.text if hasattr(block, 'text') else str(block))

    return "\n".join(text_parts)


def render_claude_skills_app():
    """Render the Claude Skills Content Generator interface."""

    st.markdown("## 📝 Samba Content Generator")
    st.caption("Generate blog posts or LinkedIn content from your text using AI")

    # Check API key in sidebar
    with st.sidebar:
        st.markdown("### Configuration")
        api_key = get_credential("ANTHROPIC_API_KEY")

        if api_key:
            st.success(f"✅ Anthropic API: {api_key[:10]}...{api_key[-5:]}")
        else:
            st.error("❌ Anthropic API key missing")

        st.markdown("### Settings")
        model = st.selectbox(
            "Model",
            ["claude-sonnet-4-5-20250929"],
            help="Claude model to use for generation"
        )

        max_tokens = st.slider(
            "Max Tokens",
            min_value=1000,
            max_value=8000,
            value=4096,
            step=500,
            help="Maximum length of generated content"
        )

        st.markdown("### Skill IDs")
        st.caption("Enter your custom skill IDs:")

        blog_skill_id = st.text_input(
            "Blog Skill ID",
            value=get_credential("SAMBA_BLOG_SKILL_ID", ""),
            help="Format: skill_01AbC..."
        )

        linkedin_skill_id = st.text_input(
            "LinkedIn Skill ID",
            value=get_credential("SAMBA_LINKEDIN_SKILL_ID", ""),
            help="Format: skill_01AbC..."
        )

    # Main content area
    st.markdown("### Input Content")
    st.caption("Paste your content below (transcripts, articles, notes, etc.)")

    content_input = st.text_area(
        "Content",
        placeholder="Paste your content here...",
        height=300,
        label_visibility="collapsed"
    )

    # Skill selection
    st.markdown("### Select Output Type")

    col1, col2 = st.columns(2)

    with col1:
        blog_button = st.button(
            "📄 Generate Blog Post",
            type="primary",
            use_container_width=True,
            disabled=not content_input or not blog_skill_id
        )

    with col2:
        linkedin_button = st.button(
            "💼 Generate LinkedIn Post",
            type="primary",
            use_container_width=True,
            disabled=not content_input or not linkedin_skill_id
        )

    # Handle generation
    if blog_button and content_input and blog_skill_id:
        st.markdown("---")
        st.markdown("### 📄 Generated Blog Post")

        with st.spinner("🤖 Generating blog post..."):
            response = execute_skill(blog_skill_id, content_input, model, max_tokens)

            if response:
                output = extract_text_from_response(response)

                if output:
                    st.markdown(output)

                    # Copy button
                    st.download_button(
                        label="📋 Download as Text",
                        data=output,
                        file_name="samba_blog_post.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ No text output generated")

    if linkedin_button and content_input and linkedin_skill_id:
        st.markdown("---")
        st.markdown("### 💼 Generated LinkedIn Post")

        with st.spinner("🤖 Generating LinkedIn post..."):
            response = execute_skill(linkedin_skill_id, content_input, model, max_tokens)

            if response:
                output = extract_text_from_response(response)

                if output:
                    st.markdown(output)

                    # Copy button
                    st.download_button(
                        label="📋 Download as Text",
                        data=output,
                        file_name="samba_linkedin_post.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ No text output generated")

    # Validation messages
    if (blog_button or linkedin_button) and not content_input:
        st.warning("⚠️ Please paste content to process")

    if blog_button and not blog_skill_id:
        st.error("❌ Blog Skill ID not configured. Add it in the sidebar or secrets.toml")

    if linkedin_button and not linkedin_skill_id:
        st.error("❌ LinkedIn Skill ID not configured. Add it in the sidebar or secrets.toml")

    # Help section
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        **Steps:**
        1. Configure your skill IDs in the sidebar (or add to secrets.toml)
        2. Paste your content (transcripts, articles, notes)
        3. Click "Generate Blog Post" or "Generate LinkedIn Post"
        4. Review the generated content
        5. Download as text file or copy to use

        **Tips:**
        - Longer, more detailed input = better output
        - Include context about the topic and audience
        - You can regenerate with different content anytime

        **Skill IDs:**
        - Get these from your Anthropic API console after uploading skills
        - Format: `skill_01AbcDefGhIjKlMnOpQrStUv`
        - Store in `.streamlit/secrets.toml` for persistence:
          ```
          SAMBA_BLOG_SKILL_ID = "skill_01..."
          SAMBA_LINKEDIN_SKILL_ID = "skill_01..."
          ```
        """)
