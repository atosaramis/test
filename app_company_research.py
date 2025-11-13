"""
Company Intelligence Research Tool

Uses multiple AI agents to research companies:
- Grok (xAI) - Agentic web + X search
- Claude - Web fetch + search
- LinkedIn API - Company posts & engagement

Synthesizes all sources into comprehensive intelligence report.
"""

import streamlit as st
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_functions import fetch_linkedin_posts, get_credential

def render_company_research_app():
    """Main function to render the Company Research app."""

    st.title("🔍 Company Intelligence Research")
    st.caption("Multi-source AI research combining Grok, Claude, and LinkedIn data")

    # Initialize session state for storing research results
    if "research_results" not in st.session_state:
        st.session_state.research_results = None
    if "grok_output" not in st.session_state:
        st.session_state.grok_output = None
    if "claude_output" not in st.session_state:
        st.session_state.claude_output = None
    if "linkedin_data" not in st.session_state:
        st.session_state.linkedin_data = None

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📝 Input & Research", "🔬 AI Search Outputs", "📊 Final Report"])

    # ========================================================================
    # TAB 1: INPUT & RESEARCH
    # ========================================================================
    with tab1:
        st.markdown("### Company Research Inputs")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Company Website URL**")
            company_url = st.text_input(
                "Company URL",
                placeholder="https://anthropic.com",
                help="The company's main website URL",
                label_visibility="collapsed"
            )

        with col2:
            st.markdown("**Company LinkedIn URL**")
            linkedin_url = st.text_input(
                "LinkedIn URL",
                placeholder="https://www.linkedin.com/company/anthropic-ai/",
                help="The company's LinkedIn company page",
                label_visibility="collapsed"
            )

        st.markdown("**Competitor LinkedIn URLs** (Optional)")
        st.caption("Enter one URL per line")
        competitor_urls = st.text_area(
            "Competitors",
            placeholder="https://www.linkedin.com/company/openai/\nhttps://www.linkedin.com/company/google-deepmind/",
            height=100,
            help="LinkedIn URLs of key competitors (one per line)",
            label_visibility="collapsed"
        )

        st.divider()

        # Show what will be researched
        with st.expander("ℹ️ What will be researched?"):
            st.markdown("""
            **Grok Agentic Search** (xAI):
            - Web search with iterative query refinement
            - X/Twitter search for company mentions and sentiment
            - Social media presence analysis
            - Industry trends and discussions

            **Claude Web Research** (Anthropic):
            - Direct web fetch of company website content
            - Web search for industry reports and articles
            - Reddit/Quora discussions
            - Competitor analysis

            **LinkedIn Data** (RapidAPI):
            - 50 recent company posts
            - Engagement metrics
            - Content themes

            **Final Synthesis**:
            - Claude AI analyzes all sources
            - Generates comprehensive Company Intelligence Report
            """)

        # Research button
        if st.button("🚀 Start Research", type="primary", use_container_width=True):
            if not company_url.strip():
                st.error("❌ Please enter company website URL")
            elif not linkedin_url.strip():
                st.error("❌ Please enter LinkedIn URL")
            else:
                # Parse competitor URLs
                competitors = []
                if competitor_urls.strip():
                    competitors = [url.strip() for url in competitor_urls.strip().split('\n') if url.strip()]

                # Extract company name from URL
                company_name = company_url.replace('https://', '').replace('http://', '').split('/')[0].split('.')[0].title()

                st.success(f"✅ Starting multi-source research for **{company_name}**")

                # ==============================================================
                # STEP 1: GROK RESEARCH
                # ==============================================================
                with st.spinner("🤖 Grok: Running agentic web + X search... (this may take 30-60 seconds)"):
                    grok_result = run_grok_research(
                        company_url=company_url,
                        company_name=company_name,
                        competitors=competitors
                    )

                if grok_result.get("error"):
                    st.warning(f"⚠️ Grok search error: {grok_result['error']}")
                    st.session_state.grok_output = {"error": grok_result["error"]}
                else:
                    st.session_state.grok_output = grok_result
                    st.success(f"✅ Grok research complete ({grok_result.get('total_tokens', 0)} tokens)")

                # ==============================================================
                # STEP 2: CLAUDE RESEARCH
                # ==============================================================
                with st.spinner("🔍 Claude: Running web fetch + search... (this may take 30-60 seconds)"):
                    claude_result = run_claude_research(
                        company_url=company_url,
                        company_name=company_name,
                        competitors=competitors
                    )

                if claude_result.get("error"):
                    st.warning(f"⚠️ Claude search error: {claude_result['error']}")
                    st.session_state.claude_output = {"error": claude_result["error"]}
                else:
                    st.session_state.claude_output = claude_result
                    st.success(f"✅ Claude research complete ({claude_result.get('total_tokens', 0)} tokens)")

                # ==============================================================
                # STEP 3: LINKEDIN DATA
                # ==============================================================
                with st.spinner("📊 Fetching LinkedIn posts via RapidAPI..."):
                    linkedin_result = fetch_linkedin_posts(linkedin_url)

                if linkedin_result.get("error"):
                    st.warning(f"⚠️ LinkedIn error: {linkedin_result['error']}")
                    st.session_state.linkedin_data = {"error": linkedin_result["error"]}
                else:
                    posts_data = linkedin_result.get("data", {}).get("data", [])
                    st.session_state.linkedin_data = {
                        "posts": posts_data,
                        "count": len(posts_data)
                    }
                    st.success(f"✅ LinkedIn data fetched ({len(posts_data)} posts)")

                # ==============================================================
                # STEP 4: SYNTHESIS
                # ==============================================================
                with st.spinner("🧠 Claude: Synthesizing all sources into final report... (this may take 60-90 seconds)"):
                    final_report = synthesize_company_report(
                        company_name=company_name,
                        company_url=company_url,
                        grok_output=st.session_state.grok_output,
                        claude_output=st.session_state.claude_output,
                        linkedin_data=st.session_state.linkedin_data,
                        competitors=competitors
                    )

                if final_report.get("error"):
                    st.error(f"❌ Synthesis failed: {final_report['error']}")
                else:
                    st.session_state.research_results = final_report
                    st.success("✅ Company Intelligence Report complete!")
                    st.balloons()

                    st.info("👉 View AI outputs in **'AI Search Outputs'** tab")
                    st.info("👉 View final report in **'Final Report'** tab")

    # ========================================================================
    # TAB 2: AI SEARCH OUTPUTS
    # ========================================================================
    with tab2:
        st.markdown("### Raw AI Search Outputs")
        st.caption("Compare research from both AI agents")

        if not st.session_state.grok_output and not st.session_state.claude_output:
            st.info("📭 No research data yet. Start research in the 'Input & Research' tab.")
        else:
            # Grok Output
            st.markdown("#### 🤖 Grok Research Output")
            if st.session_state.grok_output:
                if st.session_state.grok_output.get("error"):
                    st.error(f"Error: {st.session_state.grok_output['error']}")
                else:
                    with st.expander("View Grok Research", expanded=True):
                        st.markdown(st.session_state.grok_output.get("response", "No response"))

                        if st.session_state.grok_output.get("citations"):
                            st.markdown("**Citations:**")
                            for citation in st.session_state.grok_output["citations"]:
                                st.markdown(f"- {citation}")

                        st.caption(f"Tokens used: {st.session_state.grok_output.get('total_tokens', 0)}")
            else:
                st.info("Grok research not yet run")

            st.divider()

            # Claude Output
            st.markdown("#### 🔍 Claude Research Output")
            if st.session_state.claude_output:
                if st.session_state.claude_output.get("error"):
                    st.error(f"Error: {st.session_state.claude_output['error']}")
                else:
                    with st.expander("View Claude Research", expanded=True):
                        st.markdown(st.session_state.claude_output.get("response", "No response"))

                        if st.session_state.claude_output.get("citations"):
                            st.markdown("**Citations:**")
                            for citation in st.session_state.claude_output["citations"]:
                                st.markdown(f"- {citation}")

                        st.caption(f"Tokens used: {st.session_state.claude_output.get('total_tokens', 0)}")
            else:
                st.info("Claude research not yet run")

            st.divider()

            # LinkedIn Data
            st.markdown("#### 📊 LinkedIn Data")
            if st.session_state.linkedin_data:
                if st.session_state.linkedin_data.get("error"):
                    st.error(f"Error: {st.session_state.linkedin_data['error']}")
                else:
                    st.metric("Posts Fetched", st.session_state.linkedin_data.get("count", 0))

                    with st.expander("View LinkedIn Posts Sample"):
                        posts = st.session_state.linkedin_data.get("posts", [])
                        for i, post in enumerate(posts[:5], 1):
                            st.markdown(f"**Post {i}:**")
                            st.caption(post.get("text", "")[:200] + "...")
                            st.markdown(f"Engagement: {post.get('likes', 0)} likes, {post.get('comments', 0)} comments")
                            st.markdown("---")
            else:
                st.info("LinkedIn data not yet fetched")

    # ========================================================================
    # TAB 3: FINAL REPORT
    # ========================================================================
    with tab3:
        st.markdown("### Company Intelligence Report")
        st.caption("Synthesized analysis from all sources")

        if not st.session_state.research_results:
            st.info("📭 No report generated yet. Start research in the 'Input & Research' tab.")
        else:
            report = st.session_state.research_results

            if report.get("error"):
                st.error(f"❌ Report generation failed: {report['error']}")
            else:
                # Display report sections
                st.markdown(report.get("report", "No report content available"))

                # Download button
                st.download_button(
                    label="📥 Download Report (Markdown)",
                    data=report.get("report", ""),
                    file_name=f"company_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

                # JSON export
                export_data = {
                    "generated_at": datetime.now().isoformat(),
                    "grok_output": st.session_state.grok_output,
                    "claude_output": st.session_state.claude_output,
                    "linkedin_data": st.session_state.linkedin_data,
                    "final_report": report.get("report", "")
                }

                st.download_button(
                    label="📥 Download Full Data (JSON)",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"company_research_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )


# =============================================================================
# RESEARCH FUNCTIONS
# =============================================================================

def run_grok_research(company_url: str, company_name: str, competitors: list) -> dict:
    """
    Run Grok agentic search (web + X) for company research.

    Returns:
        dict with 'response', 'citations', 'total_tokens', or 'error'
    """
    try:
        import os
        from xai_sdk import Client
        from xai_sdk.chat import user
        from xai_sdk.tools import web_search, x_search

        # Get API key
        xai_api_key = get_credential("XAI_API_KEY")
        if not xai_api_key:
            return {"error": "XAI_API_KEY not configured in secrets"}

        client = Client(api_key=xai_api_key)

        # Build research prompt
        competitor_text = ""
        if competitors:
            competitor_text = f"\n\nKey competitors to research:\n" + "\n".join(f"- {comp}" for comp in competitors)

        research_prompt = f"""Research {company_name} ({company_url}) comprehensively.{competitor_text}

Provide detailed information on:
1. Company overview (mission, products/services, team size, stage)
2. Social media presence (especially on X/Twitter - follower counts, engagement, content themes)
3. Industry trends and discussions related to this company
4. Competitive landscape and how they compare to competitors
5. Recent news, announcements, or significant mentions
6. Community sentiment and key discussions

Use both web search and X search to gather comprehensive information."""

        # Create chat with both search tools
        chat = client.chat.create(
            model="grok-4-fast",
            tools=[
                web_search(enable_image_understanding=False),
                x_search(enable_image_understanding=False, enable_video_understanding=False)
            ]
        )

        chat.append(user(research_prompt))

        # Stream response and collect
        response_text = ""
        for response, chunk in chat.stream():
            if chunk.content:
                response_text += chunk.content

        # Get final response data
        citations = []
        if hasattr(response, 'citations') and response.citations:
            citations = response.citations

        total_tokens = 0
        if hasattr(response, 'usage'):
            total_tokens = response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0

        return {
            "response": response_text,
            "citations": citations,
            "total_tokens": total_tokens,
            "model": "grok-4-fast"
        }

    except Exception as e:
        return {"error": str(e)}


def run_claude_research(company_url: str, company_name: str, competitors: list) -> dict:
    """
    Run Claude web research (fetch + search) for company intel.

    Returns:
        dict with 'response', 'citations', 'total_tokens', or 'error'
    """
    try:
        import anthropic

        # Get API key
        anthropic_api_key = get_credential("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            return {"error": "ANTHROPIC_API_KEY not configured in secrets"}

        client = anthropic.Anthropic(api_key=anthropic_api_key)

        # Build research prompt
        competitor_text = ""
        if competitors:
            competitor_text = f"\n\nKey competitors to analyze:\n" + "\n".join(f"- {comp}" for comp in competitors)

        research_prompt = f"""Research {company_name} ({company_url}) comprehensively using web fetch and web search.{competitor_text}

Please analyze:
1. Fetch the company website and extract: mission statement, core values, products/services, team information, recent blog posts
2. Search for industry reports and trends related to this company's sector
3. Find discussions on Reddit, Quora, or forums about this company or industry
4. Research competitors and their positioning
5. Identify gaps, opportunities, and strategic insights

Provide a detailed analysis with citations."""

        # Call with web tools
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": research_prompt
            }],
            tools=[
                {
                    "type": "web_fetch_20250910",
                    "name": "web_fetch",
                    "max_uses": 10,
                    "citations": {"enabled": True}
                },
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 10
                }
            ],
            extra_headers={
                "anthropic-beta": "web-fetch-2025-09-10"
            }
        )

        # Extract response text
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text

        # Extract citations
        citations = []
        for block in response.content:
            if hasattr(block, 'citations') and block.citations:
                for citation in block.citations:
                    if hasattr(citation, 'url'):
                        citations.append(citation.url)

        total_tokens = response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0

        return {
            "response": response_text,
            "citations": list(set(citations)),  # Remove duplicates
            "total_tokens": total_tokens,
            "model": "claude-sonnet-4-5"
        }

    except Exception as e:
        return {"error": str(e)}


def synthesize_company_report(
    company_name: str,
    company_url: str,
    grok_output: dict,
    claude_output: dict,
    linkedin_data: dict,
    competitors: list
) -> dict:
    """
    Use Claude to synthesize all research sources into final report.

    Returns:
        dict with 'report' (markdown) or 'error'
    """
    try:
        import anthropic

        # Get API key
        anthropic_api_key = get_credential("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            return {"error": "ANTHROPIC_API_KEY not configured in secrets"}

        client = anthropic.Anthropic(api_key=anthropic_api_key)

        # Build synthesis prompt
        synthesis_prompt = f"""You are a strategic business analyst creating a comprehensive Company Intelligence Report.

**Company:** {company_name}
**Website:** {company_url}
**Competitors:** {', '.join(competitors) if competitors else 'Not provided'}

You have been provided research from multiple AI agents and data sources. Synthesize ALL of this information into a comprehensive, well-structured Company Intelligence Report.

**GROK RESEARCH OUTPUT:**
{grok_output.get('response', 'Not available') if not grok_output.get('error') else f"Error: {grok_output.get('error')}"}

**CLAUDE RESEARCH OUTPUT:**
{claude_output.get('response', 'Not available') if not claude_output.get('error') else f"Error: {claude_output.get('error')}"}

**LINKEDIN DATA:**
{f"{linkedin_data.get('count', 0)} posts fetched" if not linkedin_data.get('error') else f"Error: {linkedin_data.get('error')}"}

---

Create a comprehensive report with the following sections:

## 1. Company Overview
- Mission statement and core values
- Products/services offered
- Current marketing messaging
- Team/leadership information
- Company stage and maturity

## 2. Digital Presence Audit
Platform-by-platform analysis:
- Website presence and content quality
- LinkedIn: follower count, engagement, posting frequency
- X/Twitter: presence, followers, engagement, sentiment
- Other social platforms (Instagram, Facebook, TikTok if found)
- Overall digital footprint assessment

## 3. Competitive Landscape Analysis
- Direct competitors identified
- Competitive positioning
- Competitor social strategies
- Market differentiation

## 4. Industry Trends & Opportunities
- Current industry trends
- Emerging topics and discussions
- Thought leaders in this space
- Common pain points

## 5. Key Gaps & Opportunities Identified
- Content gaps
- Untapped platforms
- Strategic opportunities
- Recommended focus areas

---

**FORMATTING REQUIREMENTS:**
- Use markdown formatting
- Include specific data points and metrics where available
- Cite sources when making claims
- Be specific and actionable
- Highlight key insights with bullet points
- Use headers and subheaders for clear structure

Generate the complete report now."""

        # Call Claude for synthesis
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": synthesis_prompt
            }]
        )

        # Extract report text
        report_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                report_text += block.text

        return {
            "report": report_text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0
        }

    except Exception as e:
        return {"error": str(e)}
