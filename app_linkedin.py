"""
LinkedIn Company Strategy Analysis Module

Analyze companies' LinkedIn presence as a whole:
- Voice & Tone Profile
- Content Strategy & Pillars
- Engagement Patterns
- Competitor Comparison
- Content Generation in Company Voice
"""

import streamlit as st
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_functions import (
    fetch_linkedin_posts,
    save_linkedin_posts_to_db,
    save_company_analysis,
    get_company_analysis,
    get_all_company_analyses,
    delete_company_analysis,
    save_generated_posts,
    get_ranked_keywords_for_domain,
    query_llm_about_company,
    update_company_ranked_keywords,
    update_company_ai_perception
)
from ai_analysis import analyze_company_complete, generate_content
import pandas as pd

def render_linkedin_app():
    """Main function to render the LinkedIn Analysis app."""

    st.title("📊 LinkedIn Client Intelligence")

    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Onboard New Client", "👥 My Clients", "🔍 Competitor Comparison", "✍️ Content Creation"])

    # Set smart defaults (always enabled)
    enable_analysis = True
    analysis_model = "anthropic/claude-haiku-4.5"
    enable_ai_perception = True
    keyword_limit_default = 500
    include_paid_default = False
    max_position_default = None

    # ============================================================================
    # TAB 1: ONBOARD NEW CLIENT
    # ============================================================================
    with tab1:
        st.markdown("### Onboard a New Client")
        st.caption("Add client LinkedIn profile and website to start comprehensive analysis")

        st.markdown("**Client LinkedIn URL**")
        client_linkedin_url = st.text_input(
            "LinkedIn URL",
            placeholder="https://www.linkedin.com/company/anthropic-ai/",
            help="The client's LinkedIn company page",
            label_visibility="collapsed"
        )

        st.markdown("**Client Website Domain**")
        client_domain = st.text_input(
            "Domain",
            placeholder="anthropic.com",
            help="Enter the domain without https:// (e.g., anthropic.com)",
            label_visibility="collapsed"
        )

        st.info("**What will be analyzed:**\n- 50 recent LinkedIn posts\n- Voice & content strategy\n- 500 organic keyword rankings\n- AI perception analysis (3 default questions)\n- All data saved to client profile")

        onboard_button = st.button("🚀 Onboard Client", type="primary", use_container_width=True)

        # Process
        if onboard_button:
            if not client_linkedin_url.strip():
                st.error("Please enter client LinkedIn URL")
            elif not client_domain.strip():
                st.error("Please enter client website domain")
            else:
                linkedin_url = client_linkedin_url.strip()
                domain = client_domain.strip()

                # Extract company name
                company_name = linkedin_url.split('/')[-2] if '/' in linkedin_url else "Unknown Client"

                st.markdown(f"### 🚀 Onboarding **{company_name}**")
                st.markdown("---")

                # Progress tracking
                progress_container = st.container()
                results = {
                    "posts": {"status": "pending", "data": None, "error": None},
                    "voice": {"status": "pending", "data": None, "error": None},
                    "strategy": {"status": "pending", "data": None, "error": None},
                    "engagement": {"status": "pending", "data": None, "error": None},
                    "keywords": {"status": "pending", "data": None, "error": None},
                    "ai_perception": {"status": "pending", "data": None, "error": None}
                }

                # Step 1: Fetch LinkedIn posts
                with progress_container:
                    status_posts = st.empty()
                    status_posts.info("📥 **Fetching LinkedIn posts...**")

                response = fetch_linkedin_posts(linkedin_url)

                if not response.get("error"):
                    data = response.get("data", {})
                    posts = data.get("data", [])
                    save_linkedin_posts_to_db(linkedin_url, response.get("raw_response", {}))
                    results["posts"]["status"] = "success"
                    results["posts"]["data"] = posts
                    status_posts.success(f"✅ **Fetched {len(posts)} LinkedIn posts**")

                    # Step 2: Analyze with AI (voice, strategy, engagement)
                    status_analysis = st.empty()
                    status_analysis.info(f"🤖 **Analyzing {len(posts)} posts with AI...**")

                    analysis_result = analyze_company_complete(
                        posts_list=posts,
                        company_name=company_name,
                        company_url=linkedin_url,
                        model=analysis_model
                    )

                    # Check individual analysis results
                    voice_profile = analysis_result.get("voice_profile", {})
                    content_pillars = analysis_result.get("content_pillars", {})
                    engagement_metrics = analysis_result.get("engagement_metrics", {})

                    if voice_profile.get("error"):
                        results["voice"]["status"] = "failed"
                        results["voice"]["error"] = voice_profile.get("error")
                    else:
                        results["voice"]["status"] = "success"
                        results["voice"]["data"] = voice_profile

                    if content_pillars.get("error"):
                        results["strategy"]["status"] = "failed"
                        results["strategy"]["error"] = content_pillars.get("error")
                    else:
                        results["strategy"]["status"] = "success"
                        results["strategy"]["data"] = content_pillars

                    if engagement_metrics.get("error"):
                        results["engagement"]["status"] = "failed"
                        results["engagement"]["error"] = engagement_metrics.get("error")
                    else:
                        results["engagement"]["status"] = "success"
                        results["engagement"]["data"] = engagement_metrics

                    # Save analysis
                    save_company_analysis(analysis_result)

                    # Update status for AI analysis
                    ai_success_count = sum(1 for r in [results["voice"], results["strategy"], results["engagement"]] if r["status"] == "success")
                    if ai_success_count == 3:
                        status_analysis.success(f"✅ **AI analysis complete** (Voice, Strategy, Engagement)")
                    elif ai_success_count > 0:
                        status_analysis.warning(f"⚠️ **AI analysis partial** ({ai_success_count}/3 succeeded)")
                    else:
                        status_analysis.error(f"❌ **AI analysis failed** (all 3 analyses failed)")

                    # Step 3: Fetch ranked keywords
                    status_keywords = st.empty()
                    status_keywords.info(f"🔍 **Fetching ranked keywords for {domain}...**")

                    ranked_keywords_result = get_ranked_keywords_for_domain(
                        domain=domain,
                        limit=keyword_limit_default,
                        include_paid=include_paid_default,
                        max_position=max_position_default
                    )

                    if not ranked_keywords_result.get('error'):
                        update_company_ranked_keywords(
                            company_url=linkedin_url,
                            ranked_keywords_data=ranked_keywords_result,
                            domain=domain
                        )
                        results["keywords"]["status"] = "success"
                        results["keywords"]["data"] = ranked_keywords_result
                        kw_count = ranked_keywords_result.get('count', 0)
                        status_keywords.success(f"✅ **Found {kw_count} ranked keywords**")
                    else:
                        results["keywords"]["status"] = "failed"
                        results["keywords"]["error"] = ranked_keywords_result.get('error')
                        status_keywords.error(f"❌ **Keyword fetch failed**: {ranked_keywords_result.get('error')}")

                    # Step 4: Query AI perception
                    status_ai = st.empty()
                    status_ai.info(f"🔮 **Querying AI about {company_name}...**")

                    ai_perception_result = query_llm_about_company(
                        company_name=company_name,
                        domain=domain,
                        llm_provider="chatgpt",
                        custom_prompt=None
                    )

                    if not ai_perception_result.get('error'):
                        update_company_ai_perception(
                            company_url=linkedin_url,
                            ai_perception_data=ai_perception_result
                        )
                        results["ai_perception"]["status"] = "success"
                        results["ai_perception"]["data"] = ai_perception_result
                        ai_count = len(ai_perception_result.get('responses', []))
                        status_ai.success(f"✅ **AI perception complete** ({ai_count} queries)")
                    else:
                        results["ai_perception"]["status"] = "failed"
                        results["ai_perception"]["error"] = ai_perception_result.get('error')
                        status_ai.error(f"❌ **AI perception failed**: {ai_perception_result.get('error')}")

                    # Summary
                    st.markdown("---")
                    st.markdown("### 📊 Onboarding Summary")

                    success_count = sum(1 for r in results.values() if r["status"] == "success")
                    total_count = len(results)

                    if success_count == total_count:
                        st.success(f"🎉 **All analyses complete!** ({success_count}/{total_count})")
                    elif success_count > 0:
                        st.warning(f"⚠️ **Partial success** ({success_count}/{total_count} analyses succeeded)")
                    else:
                        st.error(f"❌ **Onboarding failed** (0/{total_count} analyses succeeded)")

                    # Show failed analyses with errors
                    failed_analyses = [(name, data) for name, data in results.items() if data["status"] == "failed"]
                    if failed_analyses:
                        st.markdown("#### ❌ Failed Analyses:")
                        for name, data in failed_analyses:
                            with st.expander(f"🔴 {name.replace('_', ' ').title()} - Click for details"):
                                st.error(data["error"])
                                st.caption("**Next steps:**")
                                if "OpenRouter" in data["error"]:
                                    st.info("• Check OPENROUTER_API_KEY in secrets\n• Verify you have credits at openrouter.ai\n• Try a different model")
                                elif "DataForSEO" in data["error"]:
                                    st.info("• Check DATAFORSEO credentials in secrets\n• Verify domain is valid\n• Check DataForSEO credits")
                                elif "ChatGPT" in data["error"]:
                                    st.info("• Check API configuration\n• Verify provider is accessible")

                    st.info(f"👉 Go to **'My Clients'** tab to view full analysis for **{company_name}**")

                else:
                    status_posts.error(f"❌ **Error fetching posts**: {response.get('error')}")
                    st.error("⛔ Onboarding stopped - cannot proceed without LinkedIn posts")
                    st.caption("**Next steps:**")
                    st.info("• Check RAPIDAPI_KEY in secrets\n• Verify LinkedIn URL is correct\n• Check RapidAPI subscription status")

    # ============================================================================
    # TAB 2: MY CLIENTS
    # ============================================================================
    with tab2:
        st.markdown("### My Clients")
        st.caption("View and manage all onboarded clients")

        # Load all clients
        all_clients = get_all_company_analyses(limit=100)

        if not all_clients:
            st.info("📭 No clients yet. Go to 'Onboard New Client' to add your first client!")
        else:
            st.write(f"**{len(all_clients)} clients onboarded**")

            # Display each client
            for client in all_clients:
                company_name = client.get('company_name', 'Unknown')
                company_url = client.get('company_url', '')
                posts_analyzed = client.get('posts_analyzed', 0)
                updated_at = client.get('updated_at', '')[:10] if client.get('updated_at') else 'N/A'

                # Calculate health status
                voice_profile = client.get('voice_profile', {})
                content_pillars = client.get('content_pillars', {})
                engagement_metrics = client.get('engagement_metrics', {})
                ranked_keywords = client.get('ranked_keywords', {})
                ai_perception = client.get('ai_perception', {})

                data_checks = {
                    "Posts": posts_analyzed > 0,
                    "Voice": bool(voice_profile and not voice_profile.get('error')),
                    "Strategy": bool(content_pillars and not content_pillars.get('error')),
                    "Engagement": bool(engagement_metrics and not engagement_metrics.get('error')),
                    "Keywords": bool(ranked_keywords and not ranked_keywords.get('error')),
                    "AI Perception": bool(ai_perception and not ai_perception.get('error'))
                }

                complete_count = sum(1 for v in data_checks.values() if v)
                total_count = len(data_checks)
                completion_pct = int((complete_count / total_count) * 100)

                # Determine health status
                if completion_pct == 100:
                    health_emoji = "🟢"
                    health_status = "Healthy"
                    health_color = "#00C851"
                elif completion_pct >= 50:
                    health_emoji = "🟡"
                    health_status = "Partial"
                    health_color = "#FFB300"
                else:
                    health_emoji = "🔴"
                    health_status = "Issues"
                    health_color = "#FF4444"

                # Expander with health status
                with st.expander(f"{health_emoji} **{company_name}** - {completion_pct}% complete - Last updated: {updated_at}", expanded=False):
                    # Health summary at the top
                    st.markdown(f"### {health_emoji} Health Status: **{health_status}** ({complete_count}/{total_count} analyses)")

                    # Show what's working and what's not
                    col_status1, col_status2 = st.columns(2)
                    with col_status1:
                        st.markdown("**✅ Working:**")
                        working = [name for name, status in data_checks.items() if status]
                        if working:
                            for item in working:
                                st.markdown(f"• {item}")
                        else:
                            st.caption("Nothing working yet")

                    with col_status2:
                        st.markdown("**❌ Failed/Missing:**")
                        failed = [name for name, status in data_checks.items() if not status]
                        if failed:
                            for item in failed:
                                st.markdown(f"• {item}")
                        else:
                            st.caption("All analyses complete!")

                    st.divider()
                    # Quick metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Posts", posts_analyzed)
                    with col2:
                        ranked_kw = client.get('ranked_keywords', {})
                        kw_count = ranked_kw.get('count', 0) if not ranked_kw.get('error') else 0
                        st.metric("Keywords", kw_count)
                    with col3:
                        engagement = client.get('engagement_metrics', {}).get('avg_engagement', {})
                        avg_eng = engagement.get('total', 0)
                        st.metric("Avg Engagement", f"{avg_eng:,}")
                    with col4:
                        ai_data = client.get('ai_perception', {})
                        ai_count = len(ai_data.get('responses', [])) if not ai_data.get('error') else 0
                        st.metric("AI Queries", ai_count)

                    st.divider()

                    # Action buttons
                    if complete_count < total_count:
                        # Show retry button if there are failures
                        st.markdown("#### 🔄 Retry Failed Analyses")
                        st.caption("Re-run only the analyses that failed without re-fetching LinkedIn posts")

                        if st.button("🔄 Retry Failed Analyses", key=f"retry_{client.get('id')}", use_container_width=True, type="primary"):
                            retry_status = st.empty()
                            retry_status.info("Starting retry...")

                            # Get existing posts from database
                            posts = client.get('top_posts', [])  # We can use top posts or fetch from DB

                            # Retry Voice if failed
                            if not data_checks["Voice"]:
                                retry_status.info("🔄 Retrying voice analysis...")
                                from ai_analysis import analyze_company_voice
                                voice_result = analyze_company_voice(posts, company_name, analysis_model)
                                if not voice_result.get('error'):
                                    retry_status.success("✅ Voice analysis succeeded!")
                                else:
                                    retry_status.error(f"❌ Voice still failing: {voice_result.get('error')}")

                            # Retry Strategy if failed
                            if not data_checks["Strategy"]:
                                retry_status.info("🔄 Retrying strategy analysis...")
                                from ai_analysis import analyze_content_strategy
                                strategy_result = analyze_content_strategy(posts, company_name, analysis_model)
                                if not strategy_result.get('error'):
                                    retry_status.success("✅ Strategy analysis succeeded!")
                                else:
                                    retry_status.error(f"❌ Strategy still failing: {strategy_result.get('error')}")

                            # Retry Engagement if failed
                            if not data_checks["Engagement"]:
                                retry_status.info("🔄 Retrying engagement analysis...")
                                from ai_analysis import analyze_engagement_patterns
                                engagement_result = analyze_engagement_patterns(posts, company_name, analysis_model)
                                if not engagement_result.get('error'):
                                    retry_status.success("✅ Engagement analysis succeeded!")
                                else:
                                    retry_status.error(f"❌ Engagement still failing: {engagement_result.get('error')}")

                            # Retry Keywords if failed
                            if not data_checks["Keywords"]:
                                retry_status.info("🔄 Retrying keyword fetch...")
                                domain = client.get('domain', '')
                                if domain:
                                    kw_result = get_ranked_keywords_for_domain(domain, limit=keyword_limit_default)
                                    if not kw_result.get('error'):
                                        update_company_ranked_keywords(company_url, kw_result, domain)
                                        retry_status.success("✅ Keyword fetch succeeded!")
                                    else:
                                        retry_status.error(f"❌ Keywords still failing: {kw_result.get('error')}")

                            # Retry AI Perception if failed
                            if not data_checks["AI Perception"]:
                                retry_status.info("🔄 Retrying AI perception...")
                                ai_result = query_llm_about_company(company_name, client.get('domain', ''), "chatgpt")
                                if not ai_result.get('error'):
                                    update_company_ai_perception(company_url, ai_result)
                                    retry_status.success("✅ AI perception succeeded!")
                                else:
                                    retry_status.error(f"❌ AI perception still failing: {ai_result.get('error')}")

                            retry_status.success("🎉 Retry complete! Refreshing page...")
                            time.sleep(2)
                            st.rerun()

                        st.divider()

                    # Other action buttons
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("🗑️ Delete Client", key=f"delete_{client.get('id')}", use_container_width=True, type="secondary"):
                            if delete_company_analysis(company_url):
                                st.success(f"Deleted {company_name}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to delete client")
                    with btn_col2:
                        if st.button("📥 Download JSON", key=f"download_{client.get('id')}", use_container_width=True):
                            st.download_button(
                                label="Download",
                                data=str(client),
                                file_name=f"{company_name}_analysis.json",
                                mime="application/json"
                            )

                    st.divider()

                    # Display consolidated 5-tab analysis
                    client_tabs = st.tabs(["📊 Overview", "🎤 Voice & Strategy", "📈 Content Performance", "🔍 Keywords & AI", "🐛 Debug"])

                    # Tab 0: Overview
                    with client_tabs[0]:
                        st.markdown("### 📊 Quick Overview")

                        # Summary metrics row
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("Posts Analyzed", posts_analyzed)
                        with m2:
                            ranked_kw = client.get('ranked_keywords', {})
                            kw_count = ranked_kw.get('count', 0) if not ranked_kw.get('error') else 0
                            st.metric("Keywords", kw_count)
                        with m3:
                            engagement = client.get('engagement_metrics', {}).get('avg_engagement', {})
                            avg_eng = engagement.get('total', 0)
                            st.metric("Avg Engagement", f"{avg_eng:,}")
                        with m4:
                            ai_data = client.get('ai_perception', {})
                            ai_count = len(ai_data.get('responses', [])) if not ai_data.get('error') else 0
                            st.metric("AI Queries", ai_count)

                        st.divider()

                        # Quick voice summary
                        voice = client.get('voice_profile', {})
                        if voice and not voice.get('error'):
                            st.markdown("#### 🎤 Voice Summary")
                            vc1, vc2 = st.columns(2)
                            with vc1:
                                st.write(f"**Tone:** {voice.get('overall_tone', 'N/A')}")
                                st.write(f"**Style:** {voice.get('writing_style', 'N/A')}")
                            with vc2:
                                st.write(f"**Formality:** {voice.get('formality_level', 'N/A')}")
                                st.metric("Consistency", f"{voice.get('consistency_score', 0)}/10")

                        # Quick strategy summary
                        strategy = client.get('content_pillars', {})
                        if strategy and not strategy.get('error'):
                            st.markdown("#### 📋 Strategy Summary")
                            st.write(f"**Primary Focus:** {strategy.get('primary_focus', 'N/A')}")

                        # Date range
                        date_range = client.get('date_range', 'Unknown')
                        st.caption(f"📅 Analysis period: {date_range}")

                    # Tab 1: Voice & Strategy (Combined)
                    with client_tabs[1]:
                        st.markdown("### 🎤 Voice Profile")
                        voice = client.get('voice_profile', {})
                        if voice and not voice.get('error'):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Tone:** {voice.get('overall_tone', 'N/A')}")
                                st.write(f"**Style:** {voice.get('writing_style', 'N/A')}")
                                st.write(f"**Formality:** {voice.get('formality_level', 'N/A')}")
                                st.metric("Consistency", f"{voice.get('consistency_score', 0)}/10")
                            with col2:
                                st.write("**Personality Traits:**")
                                for trait in voice.get('personality_traits', [])[:5]:
                                    st.write(f"• {trait}")
                            if voice.get('unique_voice_characteristics'):
                                st.success(f"**Unique Characteristics:** {voice['unique_voice_characteristics']}")
                        elif voice.get('error'):
                            st.error(f"Voice analysis failed: {voice.get('error')}")
                            st.caption("💡 This usually means the OpenRouter API call failed. Check your API key and credits.")
                        else:
                            st.info("No voice profile data available")

                        st.divider()

                        st.markdown("### 📋 Content Strategy")
                        strategy = client.get('content_pillars', {})
                        if strategy and not strategy.get('error'):
                            st.write(f"**Primary Focus:** {strategy.get('primary_focus', 'N/A')}")
                            if strategy.get('content_pillar_distribution'):
                                st.write("**Content Pillar Distribution:**")
                                for pillar, pct in sorted(strategy['content_pillar_distribution'].items(), key=lambda x: x[1], reverse=True)[:5]:
                                    st.progress(pct / 100, text=f"{pillar}: {pct}%")
                        elif strategy.get('error'):
                            st.error(f"Content strategy analysis failed: {strategy.get('error')}")
                            st.caption("💡 This usually means the OpenRouter API call failed. Check your API key and credits.")
                        else:
                            st.info("No content strategy data available")

                    # Tab 2: Content Performance (Engagement + Top Posts)
                    with client_tabs[2]:
                        st.markdown("### 📈 Engagement Metrics")
                        engagement_data = client.get('engagement_metrics', {})
                        if engagement_data and not engagement_data.get('error'):
                            avg_eng = engagement_data.get('avg_engagement', {})
                            if avg_eng:
                                c1, c2, c3, c4 = st.columns(4)
                                c1.metric("Avg Likes", f"{avg_eng.get('likes', 0):,}")
                                c2.metric("Avg Comments", f"{avg_eng.get('comments', 0):,}")
                                c3.metric("Avg Reposts", f"{avg_eng.get('reposts', 0):,}")
                                c4.metric("Avg Total", f"{avg_eng.get('total', 0):,}")
                        elif engagement_data.get('error'):
                            st.error(f"Engagement analysis failed: {engagement_data.get('error')}")
                            st.caption("💡 This usually means the OpenRouter API call failed. Check your API key and credits.")
                        else:
                            st.info("No engagement data available")

                        st.divider()

                        st.markdown("### 🔝 Top Performing Posts")
                        top_posts = client.get('top_posts', [])
                        if top_posts:
                            for i, post in enumerate(top_posts, 1):
                                with st.expander(f"**#{i}** - {post.get('engagement', 0):,} total engagement"):
                                    st.write(post.get('text', ''))
                                    if post.get('url'):
                                        st.caption(f"[View on LinkedIn]({post.get('url')})")
                        else:
                            st.info("No top posts data")

                    # Tab 3: Keywords & AI (Combined)
                    with client_tabs[3]:
                        st.markdown("### 🔍 Ranked Keywords")
                        ranked_kw = client.get('ranked_keywords', {})
                        if ranked_kw and not ranked_kw.get('error'):
                            keywords = ranked_kw.get('keywords', [])[:20]
                            if keywords:
                                df = pd.DataFrame(keywords)
                                df = df[['keyword', 'position', 'search_volume']]
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("Keywords fetched but no data returned")
                        elif ranked_kw.get('error'):
                            st.error(f"Keyword fetch failed: {ranked_kw.get('error')}")
                            st.caption("💡 This usually means the DataForSEO API call failed. Check your API key and credits.")
                        else:
                            st.info("No keyword data available - may not have been fetched during onboarding")

                        st.divider()

                        st.markdown("### 🔮 AI Perception")
                        ai_data = client.get('ai_perception', {})
                        if ai_data and not ai_data.get('error'):
                            responses = ai_data.get('responses', [])
                            if responses:
                                for i, resp in enumerate(responses, 1):
                                    with st.expander(f"Q{i}: {resp.get('prompt', '')[:80]}..."):
                                        st.write(f"**Answer:** {resp.get('response', '')}")
                            else:
                                st.info("AI perception fetched but no responses returned")
                        elif ai_data.get('error'):
                            st.error(f"AI perception query failed: {ai_data.get('error')}")
                            st.caption("💡 This usually means the ChatGPT API call failed. Check your API configuration.")
                        else:
                            st.info("No AI perception data available - may not have been fetched during onboarding")

                    # Tab 4: Debug
                    with client_tabs[4]:
                        st.markdown("### 🐛 Raw Client Data")
                        st.caption("Debug view - shows all data from database. Use this to diagnose issues.")
                        st.json(client)

                    # Download button
                    st.download_button(
                        "📥 Download Client Data (JSON)",
                        data=json.dumps(client, indent=2),
                        file_name=f"client_{company_name.replace(' ', '_')}.json",
                        mime="application/json",
                        key=f"download_{client.get('id')}"
                    )

    # ============================================================================
    # TAB 3: COMPETITOR COMPARISON
    # ============================================================================
    with tab3:
        st.markdown("### Compare Companies Side-by-Side")
        st.caption("Select clients from your portfolio to compare")

        # Load all analyzed companies
        all_clients = get_all_company_analyses(limit=50)

        if not all_clients:
            st.info("No clients yet. Go to 'Onboard New Client' tab to add clients first.")
        else:
            # Company selector
            company_options = {f"{c.get('company_name', 'Unknown')} ({c.get('posts_analyzed', 0)} posts)": c for c in all_clients}

            selected_companies = st.multiselect(
                "Select Companies to Compare",
                options=list(company_options.keys()),
                default=list(company_options.keys())[:min(3, len(company_options))],
                help="Select 2-4 companies for comparison"
            )

            if not selected_companies:
                st.warning("Select at least one company to view analysis")
            else:
                companies_to_compare = [company_options[name] for name in selected_companies]

                st.divider()

                # Comparison metrics
                st.markdown("### 📊 Engagement Comparison")

                cols = st.columns(len(companies_to_compare))

                for idx, company in enumerate(companies_to_compare):
                    with cols[idx]:
                        st.markdown(f"**{company.get('company_name', 'Unknown')}**")

                        engagement = company.get('engagement_metrics', {})
                        avg_eng = engagement.get('avg_engagement', {})

                        st.metric("Avg Total Engagement", f"{avg_eng.get('total', 0):,}")
                        st.metric("Posts Analyzed", company.get('posts_analyzed', 0))

                st.divider()

                # Voice & Tone Comparison
                st.markdown("### 🎤 Voice & Tone Profiles")

                for company in companies_to_compare:
                    with st.expander(f"🏢 {company.get('company_name', 'Unknown')}", expanded=True):
                        voice = company.get('voice_profile', {})

                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Tone:** {voice.get('overall_tone', 'N/A')}")
                            st.write(f"**Style:** {voice.get('writing_style', 'N/A')}")
                            st.write(f"**Formality:** {voice.get('formality_level', 'N/A')}")

                        with col2:
                            st.write("**Personality:**")
                            for trait in voice.get('personality_traits', [])[:3]:
                                st.write(f"• {trait}")

                        if voice.get('unique_voice_characteristics'):
                            st.info(voice['unique_voice_characteristics'])

                st.divider()

                # Content Strategy Comparison
                st.markdown("### 📋 Content Strategy")

                for company in companies_to_compare:
                    with st.expander(f"🏢 {company.get('company_name', 'Unknown')}", expanded=True):
                        strategy = company.get('content_pillars', {})

                        st.write(f"**Primary Focus:** {strategy.get('primary_focus', 'N/A')}")

                        if strategy.get('content_pillar_distribution'):
                            pillars = strategy['content_pillar_distribution']
                            for pillar, percentage in sorted(pillars.items(), key=lambda x: x[1], reverse=True)[:3]:
                                st.progress(percentage / 100, text=f"{pillar}: {percentage}%")

                st.divider()

                # Download comparison data
                comparison_data = {
                    "compared_companies": [c.get('company_name') for c in companies_to_compare],
                    "companies": companies_to_compare
                }

                st.download_button(
                    label="📥 Download Comparison (JSON)",
                    data=json.dumps(comparison_data, indent=2),
                    file_name="company_comparison.json",
                    mime="application/json"
                )

    # ============================================================================
    # TAB 4: CONTENT CREATION
    # ============================================================================
    with tab4:
        st.markdown("### ✍️ Generate Content in Client Voice")
        st.caption("Create LinkedIn posts using any client's voice profile")

        # Load all analyzed companies for voice selection
        all_clients = get_all_company_analyses(limit=50)

        if not all_clients:
            st.info("No clients yet. Go to 'Onboard New Client' tab to add clients first.")
        else:
            # Select company voice
            company_options = {c.get('company_name', 'Unknown'): c for c in all_clients}

            selected_company_name = st.selectbox(
                "Select Company Voice",
                options=list(company_options.keys()),
                help="Content will be generated in this company's voice and style"
            )

            selected_company = company_options[selected_company_name]

            st.info(f"Using voice profile from: **{selected_company_name}** ({selected_company.get('posts_analyzed', 0)} posts analyzed)")

            st.divider()

            # Content generation options
            generation_type = st.radio(
                "Content Type",
                ["Create post from article URL", "Create post from topic", "Rewrite content in company voice"],
                horizontal=False
            )

            st.divider()

            # Input based on type
            if generation_type == "Create post from article URL":
                article_url = st.text_input(
                    "Article URL",
                    placeholder="https://example.com/article",
                    help="Paste URL to article you want to create a LinkedIn post about"
                )

                user_input = article_url
                input_type = "article"
                button_label = "Generate Post from Article"

            elif generation_type == "Create post from topic":
                topic = st.text_area(
                    "Topic or Brief",
                    placeholder="e.g., 'Announce new AI research breakthrough in reinforcement learning' or 'Share insights on enterprise AI adoption trends'",
                    height=100,
                    help="Describe what you want to post about"
                )

                user_input = topic
                input_type = "topic"
                button_label = "Generate Post from Topic"

            else:  # Rewrite
                content_to_rewrite = st.text_area(
                    "Content to Rewrite",
                    placeholder="Paste the content you want to rewrite in this company's voice...",
                    height=150,
                    help="Paste content to rewrite in company's voice"
                )

                user_input = content_to_rewrite
                input_type = "rewrite"
                button_label = "Rewrite in Company Voice"

            st.caption("Using Claude Sonnet 4.5 for high-quality content generation")

            # Generate button - creates 3 variations
            if st.button(button_label, type="primary", use_container_width=True):
                if not user_input.strip():
                    st.warning("Please provide input")
                else:
                    with st.spinner(f"Generating 3 variations in {selected_company_name}'s voice..."):
                        # Generate 3 variations
                        variations = []
                        for variation_num in range(1, 4):
                            result = generate_content(
                                voice_profile=selected_company.get('voice_profile', {}),
                                content_strategy=selected_company.get('content_pillars', {}),
                                input_type=input_type,
                                user_input=user_input,
                                model="anthropic/claude-sonnet-4.5",
                                variation_number=variation_num
                            )
                            if not result.get('error'):
                                variations.append(result)

                        if not variations:
                            st.error("All generations failed. Please try again.")
                        else:
                            st.success(f"Generated {len(variations)} variations!")

                            # Save to database
                            save_success = save_generated_posts(
                                company_url=selected_company.get('company_url', ''),
                                company_name=selected_company_name,
                                input_type=input_type,
                                user_input=user_input,
                                variations=variations,
                                model="anthropic/claude-sonnet-4.5"
                            )
                            if save_success:
                                st.caption("✓ Saved to database for future reference")

                            # Display all variations
                            for i, result in enumerate(variations, 1):
                                st.markdown(f"### 📝 Variation {i}")

                                post_text = result.get('post_text', '')
                                st.text_area(
                                    f"Variation {i}:",
                                    value=post_text,
                                    height=200,
                                    key=f"variation_{i}_text",
                                    label_visibility="collapsed"
                                )

                                # Show insights
                                with st.expander(f"💡 Insights for Variation {i}", expanded=False):
                                    if result.get('hook_explanation'):
                                        st.write(f"**Why This Hook Works:** {result['hook_explanation']}")

                                    if result.get('voice_match_notes'):
                                        st.info(f"**Voice Match:** {result['voice_match_notes']}")

                                    if result.get('alternative_hooks'):
                                        st.write("**Alternative Opening Lines:**")
                                        for j, hook in enumerate(result['alternative_hooks'], 1):
                                            st.write(f"{j}. {hook}")

                                    if result.get('suggested_cta'):
                                        st.write(f"**Suggested CTA:** {result['suggested_cta']}")

                                    if result.get('hashtag_suggestions'):
                                        st.write(f"**Hashtags:** {' '.join(result['hashtag_suggestions'])}")

                                # Download button for each variation
                                st.download_button(
                                    label=f"📥 Download Variation {i}",
                                    data=post_text,
                                    file_name=f"linkedin_post_{selected_company_name.replace(' ', '_')}_v{i}.txt",
                                    mime="text/plain",
                                    key=f"download_variation_{i}"
                                )

                                st.divider()
