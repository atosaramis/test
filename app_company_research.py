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
from seo_functions import (
    fetch_linkedin_posts,
    get_credential,
    save_company_analysis,
    save_linkedin_posts_to_db,
    get_company_analysis,
    get_company_competitors
)
from ai_analysis import analyze_company_complete

def render_company_research_app():
    """Main function to render the Company Research app."""

    st.title("🔍 Company Intelligence Research")
    st.caption("Multi-source AI research combining Grok, Claude, and LinkedIn data")

    # Initialize session state for storing research results
    if "research_results" not in st.session_state:
        st.session_state.research_results = None

    # Create tabs
    tab1, tab2 = st.tabs(["📝 Input & Research", "📊 Final Report"])

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
                # STEP 0: CREATE INITIAL DATABASE RECORD
                # ==============================================================
                with st.spinner("💾 Initializing database record..."):
                    save_success = save_company_analysis({
                        'linkedin_company_url': linkedin_url,
                        'website_url': company_url,
                        'company_name': company_name,
                        'research_type': 'primary',
                        'competitor_of': None
                    })
                    if save_success:
                        st.success("✅ Database record created")
                    else:
                        st.error("❌ Failed to create database record - check server logs")
                        st.stop()

                # ==============================================================
                # STEP 1: GROK RESEARCH
                # ==============================================================
                with st.spinner("🤖 Grok: Running agentic web + X search..."):
                    grok_result = run_grok_research(
                        company_url=company_url,
                        company_name=company_name,
                        competitors=competitors
                    )

                if grok_result.get("error"):
                    st.warning(f"⚠️ Grok search error: {grok_result['error']}")
                else:
                    # Save to DB immediately
                    save_company_analysis({
                        'linkedin_company_url': linkedin_url,
                        'grok_research': grok_result
                    })
                    st.success(f"✅ Grok research complete and saved ({grok_result.get('total_tokens', 0)} tokens)")

                # ==============================================================
                # STEP 2: CLAUDE RESEARCH
                # ==============================================================
                with st.spinner("🔍 Claude: Running web fetch + search..."):
                    claude_result = run_claude_research(
                        company_url=company_url,
                        company_name=company_name,
                        competitors=competitors
                    )

                if claude_result.get("error"):
                    st.warning(f"⚠️ Claude search error: {claude_result['error']}")
                else:
                    # Save to DB immediately
                    save_company_analysis({
                        'linkedin_company_url': linkedin_url,
                        'claude_research': claude_result
                    })
                    st.success(f"✅ Claude research complete and saved ({claude_result.get('total_tokens', 0)} tokens)")

                # ==============================================================
                # STEP 3: LINKEDIN DATA
                # ==============================================================
                with st.spinner("📊 Fetching LinkedIn posts via RapidAPI..."):
                    linkedin_result = fetch_linkedin_posts(linkedin_url)

                if linkedin_result.get("error"):
                    st.warning(f"⚠️ LinkedIn error: {linkedin_result['error']}")
                else:
                    posts_data = linkedin_result.get("data", {}).get("data", [])
                    st.success(f"✅ LinkedIn data fetched ({len(posts_data)} posts)")

                    # Save raw LinkedIn posts to DB
                    save_linkedin_posts_to_db(linkedin_url, linkedin_result.get("raw_response", {}))

                    # Run AI analysis on LinkedIn posts
                    if posts_data:
                        with st.spinner("🤖 Analyzing LinkedIn posts with AI..."):
                            linkedin_analysis = analyze_company_complete(
                                posts_data,
                                company_name,
                                linkedin_url,
                                "anthropic/claude-haiku-4.5"
                            )

                            # Save LinkedIn analysis to DB immediately
                            save_company_analysis({
                                'linkedin_company_url': linkedin_url,
                                'voice_profile': linkedin_analysis.get('voice_profile', {}),
                                'content_pillars': linkedin_analysis.get('content_pillars', {}),
                                'engagement_metrics': linkedin_analysis.get('engagement_metrics', {}),
                                'top_posts': linkedin_analysis.get('top_posts', []),
                                'posts_analyzed': linkedin_analysis.get('posts_analyzed', 0),
                                'date_range': linkedin_analysis.get('date_range', ''),
                                'analysis_model': linkedin_analysis.get('analysis_model', '')
                            })
                            st.success("✅ LinkedIn analysis complete and saved")

                # ==============================================================
                # STEP 3B: COMPETITOR LINKEDIN SCRAPING
                # ==============================================================
                if competitors:
                    st.markdown(f"### 🔍 Analyzing {len(competitors)} Competitor(s)")
                    st.info(f"💡 Scraping and analyzing LinkedIn data for {len(competitors)} competitors...")

                    for idx, competitor_url in enumerate(competitors, 1):
                        with st.spinner(f"📊 Competitor {idx}/{len(competitors)}: Fetching LinkedIn posts..."):
                            competitor_result = fetch_linkedin_posts(competitor_url)

                        if competitor_result.get("error"):
                            st.warning(f"⚠️ Competitor {idx} LinkedIn error: {competitor_result['error']}")
                            continue

                        # Extract competitor name from URL
                        competitor_name = competitor_url.rstrip('/').split('/')[-1].replace('-', ' ').title()

                        competitor_posts = competitor_result.get("data", {}).get("data", [])
                        if not competitor_posts:
                            st.warning(f"⚠️ No posts found for competitor {idx}")
                            continue

                        st.success(f"✅ Competitor {idx} ({competitor_name}): {len(competitor_posts)} posts fetched")

                        # Save raw competitor posts to DB
                        save_linkedin_posts_to_db(competitor_url, competitor_result.get("raw_response", {}))

                        # Run AI analysis on competitor posts
                        with st.spinner(f"🤖 Competitor {idx}: Analyzing with AI..."):
                            competitor_analysis = analyze_company_complete(
                                competitor_posts,
                                competitor_name,
                                competitor_url,
                                "anthropic/claude-haiku-4.5"
                            )

                        # Save competitor analysis to DB
                        competitor_data = {
                            'linkedin_company_url': competitor_url,
                            'company_name': competitor_name,
                            'research_type': 'competitor',
                            'competitor_of': linkedin_url,  # Reference to main company's linkedin_company_url
                            'website_url': None,
                            'voice_profile': competitor_analysis.get('voice_profile', {}),
                            'content_pillars': competitor_analysis.get('content_pillars', {}),
                            'engagement_metrics': competitor_analysis.get('engagement_metrics', {}),
                            'top_posts': competitor_analysis.get('top_posts', []),
                            'posts_analyzed': competitor_analysis.get('posts_analyzed', 0),
                            'date_range': competitor_analysis.get('date_range', ''),
                            'analysis_model': competitor_analysis.get('analysis_model', '')
                        }

                        save_company_analysis(competitor_data)
                        st.success(f"✅ Competitor {idx} ({competitor_name}) saved to database")

                # ==============================================================
                # STEP 4: SYNTHESIS (from DB)
                # ==============================================================
                with st.spinner("🧠 Claude: Synthesizing all sources from database into final report..."):
                    final_report = synthesize_company_report(
                        company_name=company_name,
                        company_url=company_url,
                        linkedin_url=linkedin_url
                    )

                if final_report.get("error"):
                    st.error(f"❌ Synthesis failed: {final_report['error']}")
                else:
                    st.session_state.research_results = final_report
                    st.success("✅ Company Intelligence Report complete!")
                    st.balloons()

                    st.info("👉 View final report in **'Final Report'** tab")

    # ========================================================================
    # TAB 2: FINAL REPORT
    # ========================================================================
    with tab2:
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
            # Filter out None/empty values
            valid_competitors = [comp for comp in competitors if comp and str(comp).strip()]
            if valid_competitors:
                competitor_text = f"\n\nKey competitors to research:\n" + "\n".join(f"- {comp}" for comp in valid_competitors)

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
            # Filter out None/empty values
            valid_competitors = [comp for comp in competitors if comp and str(comp).strip()]
            if valid_competitors:
                competitor_text = f"\n\nKey competitors to analyze:\n" + "\n".join(f"- {comp}" for comp in valid_competitors)

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
            if hasattr(block, 'text') and block.text is not None:
                response_text += block.text

        # Extract citations
        citations = []
        for block in response.content:
            if hasattr(block, 'citations') and block.citations:
                for citation in block.citations:
                    if hasattr(citation, 'url') and citation.url:
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
    linkedin_url: str
) -> dict:
    """
    Use Claude to synthesize all research sources from DB into final report.

    Queries database for main company and competitors, builds structured context.

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

        # ==============================================================
        # QUERY DATABASE FOR STRUCTURED DATA
        # ==============================================================

        # Get main company data
        print(f"[SYNTHESIS] Querying for main company with linkedin_url: {linkedin_url}")
        main_company = get_company_analysis(linkedin_company_url=linkedin_url)
        print(f"[SYNTHESIS] Query result: {main_company.keys() if main_company else 'None/Empty'}")
        if not main_company:
            print(f"[SYNTHESIS] ERROR: Main company data not found!")
            return {"error": "Main company data not found in database. Please run research first."}

        # Get competitors
        competitors = get_company_competitors(linkedin_url)

        # ==============================================================
        # BUILD STRUCTURED CONTEXT
        # ==============================================================

        # Grok Research Summary
        grok_summary = "Not available"
        if main_company.get('grok_research'):
            grok_data = main_company['grok_research']
            grok_summary = grok_data.get('response', 'No response')[:2000]  # First 2000 chars
            if len(grok_data.get('response', '')) > 2000:
                grok_summary += "... (truncated)"

        # Claude Research Summary
        claude_summary = "Not available"
        if main_company.get('claude_research'):
            claude_data = main_company['claude_research']
            claude_summary = claude_data.get('response', 'No response')[:2000]  # First 2000 chars
            if len(claude_data.get('response', '')) > 2000:
                claude_summary += "... (truncated)"

        # LinkedIn Analysis
        voice_profile = main_company.get('voice_profile', {})
        content_pillars = main_company.get('content_pillars', {})
        engagement = main_company.get('engagement_metrics', {})

        linkedin_summary = f"""
**Voice Profile:**
- Tone: {voice_profile.get('overall_tone', 'Unknown')}
- Style: {voice_profile.get('writing_style', 'Unknown')}
- Formality: {voice_profile.get('formality_level', 'Unknown')}
- Consistency Score: {voice_profile.get('consistency_score', 0)}/10

**Content Strategy:**
- Primary Focus: {content_pillars.get('primary_focus', 'Unknown')}
- Content Themes: {', '.join(content_pillars.get('content_themes', []))}
- Pillar Distribution: {json.dumps(content_pillars.get('content_pillar_distribution', {}))}

**Engagement:**
- Avg Engagement: {engagement.get('avg_engagement', {}).get('total', 0)}
- Posts Analyzed: {main_company.get('posts_analyzed', 0)}
"""

        # Competitor Comparison
        competitor_summary = "No competitors analyzed."
        if competitors:
            competitor_summary = f"\n**{len(competitors)} Competitors Analyzed:**\n"
            for comp in competitors:
                comp_name = comp.get('company_name', 'Unknown')
                comp_voice = comp.get('voice_profile', {})
                comp_eng = comp.get('engagement_metrics', {})
                competitor_summary += f"""
- **{comp_name}**
  - Voice: {comp_voice.get('overall_tone', 'Unknown')}
  - Avg Engagement: {comp_eng.get('avg_engagement', {}).get('total', 0)}
  - Posts: {comp.get('posts_analyzed', 0)}
"""

        # Build synthesis prompt
        synthesis_prompt = f"""You are a strategic business analyst creating a comprehensive Company Intelligence Report.

**Company:** {company_name}
**Website:** {company_url}
**LinkedIn:** {linkedin_url}

You have structured research data from multiple AI sources and LinkedIn analysis. Synthesize this into a comprehensive intelligence report.

---

**GROK RESEARCH (Web + X Search):**
{grok_summary}

**CLAUDE RESEARCH (Web Fetch + Search):**
{claude_summary}

**LINKEDIN ANALYSIS:**
{linkedin_summary}

**COMPETITOR ANALYSIS:**
{competitor_summary}

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
            max_tokens=16000,
            messages=[{
                "role": "user",
                "content": synthesis_prompt
            }]
        )

        # Extract report text
        report_text = ""
        for block in response.content:
            if hasattr(block, 'text') and block.text is not None:
                report_text += block.text

        return {
            "report": report_text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0
        }

    except Exception as e:
        return {"error": str(e)}
