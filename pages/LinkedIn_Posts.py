"""
LinkedIn Company Strategy Analysis

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from seo_functions import (
    fetch_linkedin_posts,
    save_linkedin_posts_to_db,
    save_company_analysis,
    get_company_analysis,
    get_all_company_analyses,
    save_generated_posts,
    get_ranked_keywords_for_domain,
    query_llm_about_company,
    update_company_ranked_keywords,
    update_company_ai_perception
)
from ai_analysis import analyze_company_complete, generate_content
import pandas as pd

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first")
    st.stop()

# Logout in sidebar
with st.sidebar:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    st.divider()

    st.caption("**Smart Defaults:**")
    st.caption("• 500 organic keywords")
    st.caption("• 3 AI perception questions")
    st.caption("• Claude Haiku 4.5 for analysis")
    st.caption("• Auto-save all data")

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

            with st.spinner("Onboarding client..."):
                # Extract company name
                company_name = linkedin_url.split('/')[-2] if '/' in linkedin_url else "Unknown Client"

                status = st.empty()

                # Step 1: Fetch LinkedIn posts
                status.text("📥 Fetching LinkedIn posts...")

                response = fetch_linkedin_posts(linkedin_url)

                if not response.get("error"):
                    # Save raw posts to database
                    save_linkedin_posts_to_db(linkedin_url, response.get("raw_response", {}))

                    data = response.get("data", {})
                    posts = data.get("data", [])

                    # Step 2: Analyze voice & strategy
                    status.text(f"🤖 Analyzing {len(posts)} posts...")
                    analysis_result = analyze_company_complete(
                        posts_list=posts,
                        company_name=company_name,
                        company_url=linkedin_url,
                        model=analysis_model
                    )
                    save_company_analysis(analysis_result)

                    # Step 3: Fetch ranked keywords
                    status.text(f"🔍 Fetching {keyword_limit_default} ranked keywords...")
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

                    # Step 4: Query AI perception
                    status.text(f"🔮 Querying ChatGPT...")
                    ai_perception_result = query_llm_about_company(
                        company_name=company_name,
                        domain=domain,
                        llm_provider="chatgpt",
                        custom_prompt=None  # Use defaults
                    )

                    if not ai_perception_result.get('error'):
                        update_company_ai_perception(
                            company_url=linkedin_url,
                            ai_perception_data=ai_perception_result
                        )

                    status.empty()

                    # Success message
                    st.success(f"✅ Client **{company_name}** successfully onboarded!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Posts Analyzed", len(posts))
                    with col2:
                        kw_count = ranked_keywords_result.get('count', 0) if not ranked_keywords_result.get('error') else 0
                        st.metric("Keywords Found", kw_count)
                    with col3:
                        ai_count = len(ai_perception_result.get('responses', [])) if not ai_perception_result.get('error') else 0
                        st.metric("AI Queries", ai_count)

                    st.info("👉 Go to **'My Clients'** tab to view the full analysis")

                else:
                    st.error(f"❌ Error fetching posts: {response.get('error')}")

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

            with st.expander(f"🏢 {company_name} - Last updated: {updated_at}", expanded=False):
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
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                with btn_col1:
                    if st.button("🔄 Refresh Data", key=f"refresh_{client.get('id')}", use_container_width=True):
                        st.info("Refresh feature coming soon!")
                with btn_col2:
                    if st.button("🤖 Ask AI", key=f"ask_ai_{client.get('id')}", use_container_width=True):
                        st.info("Custom AI queries coming soon!")
                with btn_col3:
                    if st.button("🔍 Update Keywords", key=f"update_kw_{client.get('id')}", use_container_width=True):
                        st.info("Advanced keyword update coming soon!")

                st.divider()

                # Display full 6-tab analysis (reuse existing code structure)
                client_tabs = st.tabs(["🎤 Voice", "📋 Strategy", "📈 Engagement", "🔝 Top Posts", "🔍 Keywords", "🔮 AI"])

                with client_tabs[0]:
                    voice = client.get('voice_profile', {})
                    if voice and not voice.get('error'):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Tone:** {voice.get('overall_tone', 'N/A')}")
                            st.write(f"**Style:** {voice.get('writing_style', 'N/A')}")
                            st.write(f"**Formality:** {voice.get('formality_level', 'N/A')}")
                            st.metric("Consistency", f"{voice.get('consistency_score', 0)}/10")
                        with col2:
                            st.write("**Personality:**")
                            for trait in voice.get('personality_traits', [])[:5]:
                                st.write(f"• {trait}")
                        if voice.get('unique_voice_characteristics'):
                            st.success(f"**Unique:** {voice['unique_voice_characteristics']}")
                    else:
                        st.info("No voice profile data")

                with client_tabs[1]:
                    strategy = client.get('content_pillars', {})
                    if strategy and not strategy.get('error'):
                        st.write(f"**Primary Focus:** {strategy.get('primary_focus', 'N/A')}")
                        if strategy.get('content_pillar_distribution'):
                            st.write("**Content Distribution:**")
                            for pillar, pct in sorted(strategy['content_pillar_distribution'].items(), key=lambda x: x[1], reverse=True)[:5]:
                                st.progress(pct / 100, text=f"{pillar}: {pct}%")
                    else:
                        st.info("No content strategy data")

                with client_tabs[2]:
                    engagement_data = client.get('engagement_metrics', {})
                    if engagement_data and not engagement_data.get('error'):
                        avg_eng = engagement_data.get('avg_engagement', {})
                        if avg_eng:
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Avg Likes", f"{avg_eng.get('likes', 0):,}")
                            c2.metric("Avg Comments", f"{avg_eng.get('comments', 0):,}")
                            c3.metric("Avg Reposts", f"{avg_eng.get('reposts', 0):,}")
                            c4.metric("Avg Total", f"{avg_eng.get('total', 0):,}")
                    else:
                        st.info("No engagement data")

                with client_tabs[3]:
                    top_posts = client.get('top_posts', [])
                    if top_posts:
                        for i, post in enumerate(top_posts, 1):
                            st.write(f"**#{i}** - {post.get('engagement', 0):,} engagement")
                            st.caption(post.get('text', '')[:200] + "...")
                            st.markdown("---")
                    else:
                        st.info("No top posts data")

                with client_tabs[4]:
                    ranked_kw = client.get('ranked_keywords', {})
                    if ranked_kw and not ranked_kw.get('error'):
                        keywords = ranked_kw.get('keywords', [])[:20]
                        if keywords:
                            df = pd.DataFrame(keywords)
                            df = df[['keyword', 'position', 'search_volume']]
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No keywords data")

                with client_tabs[5]:
                    ai_data = client.get('ai_perception', {})
                    if ai_data and not ai_data.get('error'):
                        responses = ai_data.get('responses', [])
                        for i, resp in enumerate(responses, 1):
                            with st.expander(f"Q{i}: {resp.get('prompt', '')[:80]}..."):
                                st.write(f"**A:** {resp.get('response', '')}")
                    else:
                        st.info("No AI perception data")

                # Download button
                st.download_button(
                    "📥 Download Client Data (JSON)",
                    data=json.dumps(client, indent=2),
                    file_name=f"client_{company_name.replace(' ', '_')}.json",
                    mime="application/json",
                    key=f"download_{client.get('id')}"
                )

# ============================================================================
# TAB 3: COMPETITOR COMPARISON (OLD TAB 2)
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
# TAB 4: CONTENT CREATION (OLD TAB 3)
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
