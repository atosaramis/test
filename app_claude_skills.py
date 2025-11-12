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


def extract_file_from_response(response):
    """Extract file information from API response."""
    if not response or not hasattr(response, 'content'):
        return None

    for block in response.content:
        if block.type == 'tool_use' and hasattr(block, 'content'):
            # Look for file in tool use content
            if isinstance(block.content, list):
                for item in block.content:
                    if hasattr(item, 'type') and item.type == 'file':
                        return {
                            'file_id': item.file_id,
                            'filename': item.filename if hasattr(item, 'filename') else 'output.docx'
                        }

    return None


def convert_to_document(content: str, container_id: str, format_type: str = "docx", model: str = "claude-sonnet-4-5-20250929", max_tokens: int = 4096):
    """
    Convert content to Word document or PDF using Anthropic pre-built skills.

    Args:
        content: The content to convert
        container_id: Container ID from previous execution
        format_type: "docx" or "pdf"
        model: Claude model to use
        max_tokens: Maximum tokens for response

    Returns:
        API response or None if error
    """
    api_key = get_credential("ANTHROPIC_API_KEY")

    if not api_key:
        st.error("❌ ANTHROPIC_API_KEY not configured")
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Execute conversion with pre-built skill
        response = client.beta.messages.create(
            model=model,
            max_tokens=max_tokens,
            betas=["code-execution-2025-08-25", "skills-2025-10-02", "files-api-2025-04-14"],
            container={
                "id": container_id,  # Reuse container
                "skills": [
                    {
                        "type": "anthropic",
                        "skill_id": format_type,
                        "version": "latest"
                    }
                ]
            },
            messages=[
                {
                    "role": "user",
                    "content": f"Convert this content to a {format_type.upper()} file:\n\n{content}"
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
        st.error("❌ Anthropic SDK not installed")
        return None
    except Exception as e:
        st.error(f"❌ Error converting to {format_type.upper()}: {str(e)}")
        return None


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


def download_file_from_api(file_id: str, filename: str):
    """Download file from Anthropic Files API."""
    api_key = get_credential("ANTHROPIC_API_KEY")

    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Download file content
        file_content = client.beta.files.download(
            file_id=file_id,
            betas=["files-api-2025-04-14"]
        )

        # Return file bytes
        return file_content.read()

    except Exception as e:
        st.error(f"❌ Error downloading file: {str(e)}")
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
                output_text, file_path = extract_text_from_response(response)
                container_id = response.container.id if hasattr(response, 'container') else None

                # If skill created a file in the container, read it
                if file_path and container_id:
                    with st.spinner("📥 Retrieving generated content from container..."):
                        file_content = read_file_from_container(file_path, container_id, model)
                        if file_content:
                            output = file_content
                            st.session_state.generated_content = output
                            st.session_state.container_id = container_id
                            st.session_state.content_type = "Blog Post"
                            st.markdown(output)
                        else:
                            st.error("❌ Could not read file from container")
                            output = None
                # Otherwise use text output
                elif output_text:
                    # Filter out Claude's meta-commentary, only keep substantive content
                    output = output_text
                    st.session_state.generated_content = output
                    st.session_state.container_id = container_id
                    st.session_state.content_type = "Blog Post"
                    st.markdown(output)
                else:
                    output = None

                # Debug output
                with st.expander("🔍 Debug - View API Response"):
                    st.json({
                        "has_output": bool(output) if 'output' in locals() else False,
                        "file_path": file_path,
                        "has_text": bool(output_text),
                        "container_id": container_id,
                        "response_type": str(type(response)),
                        "content_blocks": len(response.content) if hasattr(response, 'content') else 0
                    })
                    if file_path:
                        st.write("**File Path in Container:**", file_path)
                    if output_text:
                        st.write("**Text Output:**", output_text[:500] + "..." if len(output_text) > 500 else output_text)

                if output:

                    # Export options
                    st.markdown("### 📥 Export Options")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.download_button(
                            label="📋 Download as Text",
                            data=output,
                            file_name="samba_blog_post.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                    with col2:
                        if st.button("📄 Export to Word", use_container_width=True, key="export_word_blog"):
                            if st.session_state.container_id:
                                with st.spinner("📄 Creating Word document..."):
                                    doc_response = convert_to_document(
                                        st.session_state.generated_content,
                                        st.session_state.container_id,
                                        "docx",
                                        model,
                                        max_tokens
                                    )
                                    if doc_response:
                                        file_info = extract_file_from_response(doc_response)
                                        if file_info:
                                            file_bytes = download_file_from_api(file_info['file_id'], file_info['filename'])
                                            if file_bytes:
                                                st.download_button(
                                                    label="💾 Download Word Document",
                                                    data=file_bytes,
                                                    file_name="samba_blog_post.docx",
                                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                    use_container_width=True,
                                                    key="download_word_blog"
                                                )
                                            else:
                                                st.error("Failed to download Word document")
                                        else:
                                            st.error("No file generated")
                            else:
                                st.error("Container ID not available")

                    with col3:
                        if st.button("📕 Export to PDF", use_container_width=True, key="export_pdf_blog"):
                            if st.session_state.container_id:
                                with st.spinner("📕 Creating PDF..."):
                                    pdf_response = convert_to_document(
                                        st.session_state.generated_content,
                                        st.session_state.container_id,
                                        "pdf",
                                        model,
                                        max_tokens
                                    )
                                    if pdf_response:
                                        file_info = extract_file_from_response(pdf_response)
                                        if file_info:
                                            file_bytes = download_file_from_api(file_info['file_id'], file_info['filename'])
                                            if file_bytes:
                                                st.download_button(
                                                    label="💾 Download PDF",
                                                    data=file_bytes,
                                                    file_name="samba_blog_post.pdf",
                                                    mime="application/pdf",
                                                    use_container_width=True,
                                                    key="download_pdf_blog"
                                                )
                                            else:
                                                st.error("Failed to download PDF")
                                        else:
                                            st.error("No file generated")
                            else:
                                st.error("Container ID not available")
                else:
                    st.warning("⚠️ No text output generated")

    if linkedin_button and content_input and linkedin_skill_id:
        st.markdown("---")
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
                            output = file_content
                            st.session_state.generated_content = output
                            st.session_state.container_id = container_id
                            st.session_state.content_type = "LinkedIn Post"
                            st.markdown(output)
                        else:
                            st.error("❌ Could not read file from container")
                            output = None
                # Otherwise use text output
                elif output_text:
                    output = output_text
                    st.session_state.generated_content = output
                    st.session_state.container_id = container_id
                    st.session_state.content_type = "LinkedIn Post"
                    st.markdown(output)
                else:
                    output = None

                # Debug output
                with st.expander("🔍 Debug - View API Response"):
                    st.json({
                        "has_output": bool(output) if 'output' in locals() else False,
                        "file_path": file_path,
                        "has_text": bool(output_text),
                        "container_id": container_id,
                        "response_type": str(type(response)),
                        "content_blocks": len(response.content) if hasattr(response, 'content') else 0
                    })
                    if file_path:
                        st.write("**File Path in Container:**", file_path)
                    if output_text:
                        st.write("**Text Output:**", output_text[:500] + "..." if len(output_text) > 500 else output_text)

                if output:

                    # Export options
                    st.markdown("### 📥 Export Options")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.download_button(
                            label="📋 Download as Text",
                            data=output,
                            file_name="samba_linkedin_post.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                    with col2:
                        if st.button("📄 Export to Word", use_container_width=True, key="export_word_linkedin"):
                            if st.session_state.container_id:
                                with st.spinner("📄 Creating Word document..."):
                                    doc_response = convert_to_document(
                                        st.session_state.generated_content,
                                        st.session_state.container_id,
                                        "docx",
                                        model,
                                        max_tokens
                                    )
                                    if doc_response:
                                        file_info = extract_file_from_response(doc_response)
                                        if file_info:
                                            file_bytes = download_file_from_api(file_info['file_id'], file_info['filename'])
                                            if file_bytes:
                                                st.download_button(
                                                    label="💾 Download Word Document",
                                                    data=file_bytes,
                                                    file_name="samba_linkedin_post.docx",
                                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                                    use_container_width=True,
                                                    key="download_word_linkedin"
                                                )
                                            else:
                                                st.error("Failed to download Word document")
                                        else:
                                            st.error("No file generated")
                            else:
                                st.error("Container ID not available")

                    with col3:
                        if st.button("📕 Export to PDF", use_container_width=True, key="export_pdf_linkedin"):
                            if st.session_state.container_id:
                                with st.spinner("📕 Creating PDF..."):
                                    pdf_response = convert_to_document(
                                        st.session_state.generated_content,
                                        st.session_state.container_id,
                                        "pdf",
                                        model,
                                        max_tokens
                                    )
                                    if pdf_response:
                                        file_info = extract_file_from_response(pdf_response)
                                        if file_info:
                                            file_bytes = download_file_from_api(file_info['file_id'], file_info['filename'])
                                            if file_bytes:
                                                st.download_button(
                                                    label="💾 Download PDF",
                                                    data=file_bytes,
                                                    file_name="samba_linkedin_post.pdf",
                                                    mime="application/pdf",
                                                    use_container_width=True,
                                                    key="download_pdf_linkedin"
                                                )
                                            else:
                                                st.error("Failed to download PDF")
                                        else:
                                            st.error("No file generated")
                            else:
                                st.error("Container ID not available")
                else:
                    st.warning("⚠️ No text output generated")

    # Validation messages
    if (blog_button or linkedin_button) and not content_input:
        st.warning("⚠️ Please paste content to process")

    if blog_button and not blog_skill_id:
        st.error("❌ Blog Skill ID not configured. Add it in the sidebar or secrets.toml")

    if linkedin_button and not linkedin_skill_id:
        st.error("❌ LinkedIn Skill ID not configured. Add it in the sidebar or secrets.toml")
