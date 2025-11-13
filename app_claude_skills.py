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
    Extract text content and file paths from API response using multiple detection methods.
    Returns: (text_content, file_path_in_container, detection_method)
    """
    if not response or not hasattr(response, 'content'):
        return "", None, None

    text_parts = []
    file_path = None
    detection_method = None

    # Collect all text content first
    for block in response.content:
        if hasattr(block, 'text'):
            text_parts.append(block.text)
        elif block.type == 'text':
            text_parts.append(block.text if hasattr(block, 'text') else str(block))

    text_content = "\n".join(text_parts)

    # Method 1: Look for file creation in server_tool_use blocks (text_editor create)
    for block in response.content:
        if block.type == 'server_tool_use':
            if hasattr(block, 'input'):
                input_data = block.input
                if isinstance(input_data, dict):
                    if input_data.get('command') == 'create' and input_data.get('path'):
                        file_path = input_data.get('path')
                        detection_method = "server_tool_use:text_editor:create"
                        break

    # Method 2: Check tool_use blocks for file paths
    if not file_path:
        for block in response.content:
            if block.type == 'tool_use':
                if hasattr(block, 'input'):
                    input_data = block.input
                    if isinstance(input_data, dict) and 'path' in input_data:
                        file_path = input_data['path']
                        detection_method = "tool_use:path"
                        break

    # Method 3: Search for /tmp/ file paths in text output using regex
    if not file_path:
        import re
        # Look for patterns like /tmp/filename.md or /tmp/filename-name.md
        matches = re.findall(r'/tmp/[a-zA-Z0-9_\-]+\.md', text_content)
        if matches:
            file_path = matches[0]  # Use first match
            detection_method = "regex:text_content"

    # Method 4: Check bash execution inputs for file creation
    if not file_path:
        for block in response.content:
            if block.type == 'tool_use' and hasattr(block, 'input'):
                input_data = block.input
                if isinstance(input_data, dict) and 'command' in input_data:
                    command = input_data['command']
                    # Look for output redirection in bash commands
                    import re
                    redirect_match = re.search(r'>\s*(/tmp/[a-zA-Z0-9_\-]+\.md)', str(command))
                    if redirect_match:
                        file_path = redirect_match.group(1)
                        detection_method = "bash:redirect"
                        break

    return text_content, file_path, detection_method


def read_file_from_container(file_path: str, container_id: str, model: str = "claude-sonnet-4-5-20250929", max_attempts: int = 3) -> Optional[str]:
    """
    Read file content from container filesystem using bash with retry logic.

    Args:
        file_path: Path to file in container (e.g., /tmp/output.md)
        container_id: Container ID to reuse
        model: Claude model to use
        max_attempts: Maximum number of retry attempts (default: 3)

    Returns:
        File content as string or None if error
    """
    import time

    api_key = get_credential("ANTHROPIC_API_KEY")

    # Store debug info in session state
    if 'file_read_debug' not in st.session_state:
        st.session_state.file_read_debug = []

    if not api_key:
        st.session_state.file_read_debug.append("❌ API key not found")
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Try reading file with retries (handles race conditions where file isn't fully written)
        for attempt in range(max_attempts):
            st.session_state.file_read_debug.append(f"Attempt {attempt + 1}/{max_attempts}: Reading {file_path}")
            if attempt > 0:
                # Add delay between retries (0.5s, 1s, 1.5s...)
                time.sleep(0.5 * attempt)

            try:
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

                # Extract bash output - ONLY from the FIRST bash result (ignore Claude's helpful follow-ups)
                st.session_state.file_read_debug.append(f"  Response has {len(response.content)} blocks")

                bash_result_count = 0
                for block in response.content:
                    st.session_state.file_read_debug.append(f"    Block type: {block.type}")

                    if block.type == 'bash_code_execution_tool_result':
                        bash_result_count += 1
                        st.session_state.file_read_debug.append(f"    Bash result #{bash_result_count}")

                        # ONLY process the FIRST bash result (from our cat command)
                        # Ignore subsequent results (Claude's helpful ls commands)
                        if bash_result_count > 1:
                            st.session_state.file_read_debug.append(f"    ⚠️ Skipping - not the first bash result (likely Claude's helpful debugging)")
                            continue

                        if hasattr(block, 'content'):
                            content = block.content
                            st.session_state.file_read_debug.append(f"    Has content attr: {hasattr(content, 'stdout')}")

                            # Check for errors in bash execution
                            if hasattr(content, 'return_code'):
                                st.session_state.file_read_debug.append(f"    Return code: {content.return_code}")
                                if content.return_code != 0:
                                    error_msg = getattr(content, 'stderr', 'Unknown error')
                                    st.session_state.file_read_debug.append(f"    ❌ Bash failed: {error_msg}")
                                    # Don't return - let retry logic handle it
                                    break  # Exit loop to retry

                            # Content is a BetaBashCodeExecutionResultBlock object with stdout
                            if hasattr(content, 'stdout'):
                                stdout = content.stdout
                                stdout_len = len(stdout.strip()) if stdout else 0
                                st.session_state.file_read_debug.append(f"    Stdout length: {stdout_len}")

                                # Check if we got actual content (not empty)
                                if stdout and stdout_len > 0:
                                    st.session_state.file_read_debug.append(f"    ✅ SUCCESS - Got content ({stdout_len} chars)")
                                    return stdout
                                else:
                                    st.session_state.file_read_debug.append(f"    ⚠️ Stdout is empty")

                            # Fallback for dict structure
                            elif isinstance(content, dict):
                                st.session_state.file_read_debug.append(f"    Content is dict")
                                result = content.get('content', [])
                                if isinstance(result, list):
                                    for item in result:
                                        if isinstance(item, dict) and item.get('type') == 'text':
                                            text = item.get('text', '')
                                            if text and len(text.strip()) > 0:
                                                st.session_state.file_read_debug.append(f"    ✅ SUCCESS - Got text from dict")
                                                return text
                                elif isinstance(result, str) and len(result.strip()) > 0:
                                    st.session_state.file_read_debug.append(f"    ✅ SUCCESS - Got string result")
                                    return result

                # If we didn't find valid bash result
                if bash_result_count == 0:
                    st.session_state.file_read_debug.append(f"  ❌ No bash_code_execution_tool_result found")

            except Exception as attempt_error:
                if attempt == max_attempts - 1:  # Last attempt
                    st.error(f"❌ Attempt {attempt + 1}/{max_attempts} failed: {str(attempt_error)}")
                    raise

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
                    output_text, file_path, detection_method = extract_text_from_response(response)
                    container_id = response.container.id if hasattr(response, 'container') else None

                    # Debug info
                    with st.expander("🔍 Debug Info", expanded=False):
                        st.write(f"**File Path Detected:** {file_path}")
                        st.write(f"**Detection Method:** {detection_method}")
                        st.write(f"**Container ID:** {container_id}")
                        st.write(f"**Text Output Length:** {len(output_text)} chars")
                        st.write(f"**Response Blocks:** {len(response.content)}")
                        for i, block in enumerate(response.content):
                            st.write(f"  Block {i}: {block.type}")

                    # If skill created a file in the container, read it
                    if file_path and container_id:
                        with st.spinner("📥 Retrieving generated content from container..."):
                            # Clear previous debug info
                            st.session_state.file_read_debug = []

                            file_content = read_file_from_container(file_path, container_id, model)

                            # ALWAYS show debug log
                            with st.expander("🐛 File Reading Debug Log", expanded=False):
                                if 'file_read_debug' in st.session_state and st.session_state.file_read_debug:
                                    for debug_line in st.session_state.file_read_debug:
                                        st.text(debug_line)
                                else:
                                    st.write("No debug info available")

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
                    output_text, file_path, detection_method = extract_text_from_response(response)
                    container_id = response.container.id if hasattr(response, 'container') else None

                    # Debug info
                    with st.expander("🔍 Debug Info", expanded=False):
                        st.write(f"**File Path Detected:** {file_path}")
                        st.write(f"**Detection Method:** {detection_method}")
                        st.write(f"**Container ID:** {container_id}")
                        st.write(f"**Text Output Length:** {len(output_text)} chars")
                        st.write(f"**Response Blocks:** {len(response.content)}")
                        for i, block in enumerate(response.content):
                            st.write(f"  Block {i}: {block.type}")

                    # If skill created a file in the container, read it
                    if file_path and container_id:
                        with st.spinner("📥 Retrieving generated content from container..."):
                            # Clear previous debug info
                            st.session_state.file_read_debug = []

                            file_content = read_file_from_container(file_path, container_id, model)

                            # ALWAYS show debug log
                            with st.expander("🐛 File Reading Debug Log", expanded=False):
                                if 'file_read_debug' in st.session_state and st.session_state.file_read_debug:
                                    for debug_line in st.session_state.file_read_debug:
                                        st.text(debug_line)
                                else:
                                    st.write("No debug info available")

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
