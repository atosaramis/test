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


def extract_text_from_response(response) -> tuple:
    """
    Extract text content and file paths from API response.
    Returns: (text_content, file_path_in_container)
    """
    if not response or not hasattr(response, 'content'):
        return "", None

    text_parts = []
    file_path = None

    for block in response.content:
        # Look for file creation in server_tool_use blocks
        if block.type == 'server_tool_use':
            if hasattr(block, 'input'):
                input_data = block.input
                # Check for text_editor create command
                if isinstance(input_data, dict):
                    if input_data.get('command') == 'create' and input_data.get('path'):
                        file_path = input_data.get('path')

        # Extract text content
        if hasattr(block, 'text'):
            text_parts.append(block.text)
        elif block.type == 'text':
            text_parts.append(block.text if hasattr(block, 'text') else str(block))

    return "\n".join(text_parts), file_path


def read_file_from_container(file_path: str, container_id: str, model: str = "claude-sonnet-4-5-20250929") -> Optional[str]:
    """
    Read file content from container filesystem using bash.

    Args:
        file_path: Path to file in container (e.g., /tmp/output.md)
        container_id: Container ID to reuse
        model: Claude model to use

    Returns:
        File content as string or None if error
    """
    api_key = get_credential("ANTHROPIC_API_KEY")

    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Use bash to read the file
        response = client.beta.messages.create(
            model=model,
            max_tokens=4096,
            betas=["code-execution-2025-08-25", "skills-2025-10-02"],
            container={
                "id": container_id  # Reuse same container
            },
            messages=[
                {
                    "role": "user",
                    "content": f"cat {file_path}"
                }
            ],
            tools=[
                {
                    "type": "code_execution_20250825",
                    "name": "code_execution"
                }
            ]
        )

        # Extract bash output
        for block in response.content:
            if block.type == 'bash_code_execution_tool_result':
                if hasattr(block, 'content'):
                    content = block.content
                    # Content is a BetaBashCodeExecutionResultBlock object with stdout
                    if hasattr(content, 'stdout'):
                        return content.stdout
                    # Fallback for dict structure
                    elif isinstance(content, dict):
                        result = content.get('content', [])
                        if isinstance(result, list):
                            for item in result:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    return item.get('text', '')
                        elif isinstance(result, str):
                            return result

        return None

    except Exception as e:
        st.error(f"❌ Error reading file from container: {str(e)}")
        return None


def render_claude_skills_app():
    """Render the Claude Skills Content Generator interface."""

    st.markdown("## 📝 Samba Content Generator")
    st.caption("Generate blog posts or LinkedIn content from your text using AI")

    # Initialize session state
    if "generated_content" not in st.session_state:
        st.session_state.generated_content = None
    if "container_id" not in st.session_state:
        st.session_state.container_id = None
    if "content_type" not in st.session_state:
        st.session_state.content_type = None

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
    st.caption("Select one or both content types to generate")

    col1, col2 = st.columns(2)

    with col1:
        generate_blog = st.checkbox(
            "📄 Blog Post",
            disabled=not blog_skill_id,
            help="Generate a Samba blog post"
        )

    with col2:
        generate_linkedin = st.checkbox(
            "💼 LinkedIn Post",
            disabled=not linkedin_skill_id,
            help="Generate a LinkedIn post"
        )

    # Single generate button with key to prevent auto-trigger
    st.markdown("")

    # Only generate if button is explicitly clicked (not on checkbox changes)
    if st.button(
        "✨ Generate Content",
        type="primary",
        use_container_width=True,
        disabled=not content_input or (not generate_blog and not generate_linkedin),
        key="generate_content_button"
    ) and content_input:
        st.markdown("---")

        # Generate blog post
        if generate_blog and blog_skill_id:
            st.markdown("### 📄 Generated Blog Post")

            with st.spinner("🤖 Generating blog post..."):
                response = execute_skill(blog_skill_id, content_input, model, max_tokens)

                if response:
                    output_text, file_path = extract_text_from_response(response)
                    container_id = response.container.id if hasattr(response, 'container') else None

                    # If skill created a file in the container, read it
                    if file_path and container_id:
                        with st.spinner("📥 Retrieving generated content from container..."):
                            file_content = read_file_from_container(file_path, container_id, model)
                            if file_content:
                                st.markdown(file_content)

                                st.download_button(
                                    label="📄 Download Blog Post",
                                    data=file_content,
                                    file_name="samba_blog_post.txt",
                                    mime="text/plain",
                                    use_container_width=True,
                                    key="download_blog_file"
                                )
                            else:
                                st.error(f"❌ Could not read file from container. File path: {file_path}")
                                # Try to show any text output as fallback
                                if output_text:
                                    st.info("Showing text output instead:")
                                    st.markdown(output_text)
                                    st.download_button(
                                        label="📄 Download Blog Post",
                                        data=output_text,
                                        file_name="samba_blog_post.txt",
                                        mime="text/plain",
                                        use_container_width=True,
                                        key="download_blog_text_fallback"
                                    )
                    # Otherwise use text output
                    elif output_text:
                        st.markdown(output_text)

                        st.download_button(
                            label="📄 Download Blog Post",
                            data=output_text,
                            file_name="samba_blog_post.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="download_blog_text"
                        )
                    else:
                        st.warning("⚠️ No text output generated")

            st.markdown("---")  # Separator between outputs

        # LinkedIn Post Generation
        if generate_linkedin and linkedin_skill_id:
            st.markdown("### 💼 Generated LinkedIn Post")

            with st.spinner("🤖 Generating LinkedIn post..."):
                response = execute_skill(linkedin_skill_id, content_input, model, max_tokens)

                if response:
                    output_text, file_path = extract_text_from_response(response)
                    container_id = response.container.id if hasattr(response, 'container') else None

                    # If skill created a file in the container, read it
                    if file_path and container_id:
                        with st.spinner("📥 Retrieving generated content from container..."):
                            file_content = read_file_from_container(file_path, container_id, model)
                            if file_content:
                                st.markdown(file_content)

                                st.download_button(
                                    label="💼 Download LinkedIn Post",
                                    data=file_content,
                                    file_name="samba_linkedin_post.txt",
                                    mime="text/plain",
                                    use_container_width=True,
                                    key="download_linkedin_file"
                                )
                            else:
                                st.error(f"❌ Could not read file from container. File path: {file_path}")
                                # Try to show any text output as fallback
                                if output_text:
                                    st.info("Showing text output instead:")
                                    st.markdown(output_text)
                                    st.download_button(
                                        label="💼 Download LinkedIn Post",
                                        data=output_text,
                                        file_name="samba_linkedin_post.txt",
                                        mime="text/plain",
                                        use_container_width=True,
                                        key="download_linkedin_text_fallback"
                                    )
                    # Otherwise use text output
                    elif output_text:
                        st.markdown(output_text)

                        st.download_button(
                            label="💼 Download LinkedIn Post",
                            data=output_text,
                            file_name="samba_linkedin_post.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="download_linkedin_text"
                        )
                    else:
                        st.warning("⚠️ No text output generated")
