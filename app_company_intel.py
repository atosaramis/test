"""
Company Intelligence Module

Analyze companies' LinkedIn presence:
- Voice & Tone Profile
- Content Strategy & Pillars
- Engagement Patterns
- Export full analysis
"""

import streamlit as st
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_functions import (
    fetch_linkedin_posts,
    save_linkedin_posts_to_db,
    save_company_analysis,
    get_company_analysis,
    get_all_company_analyses,
    delete_company_analysis
)
from ai_analysis import analyze_company_complete

def render_company_intel_app():
    """Main function to render the Company Intelligence app."""

    st.title("🔍 Company Intelligence")
    st.caption("Analyze any company's LinkedIn presence to understand their voice, strategy, and engagement patterns")

    # Tabs
    tab1, tab2 = st.tabs(["➕ Analyze New Company", "📊 View Companies"])

    # Analysis settings (fixed)
    analysis_model = "anthropic/claude-haiku-4.5"

    # ============================================================================
    # TAB 1: ANALYZE NEW COMPANY
    # ============================================================================
    with tab1:
        st.markdown("### Analyze a Company")
        st.info("💡 Enter a LinkedIn company URL to analyze their content strategy, voice profile, and engagement patterns")

        linkedin_url = st.text_input(
            "LinkedIn Company URL",
            placeholder="https://www.linkedin.com/company/anthropic-ai/",
            help="Enter the full LinkedIn company URL"
        )

        with st.expander("ℹ️ What happens when you analyze?"):
            st.markdown("""
            **Analysis Process:**
            1. 📥 Fetch 50 recent LinkedIn posts
            2. 🎯 Analyze voice & tone profile
            3. 📊 Identify content strategy & pillars
            4. 📈 Analyze engagement patterns
            5. 💾 Save to database for future reference

            **What you get:**
            - Complete voice profile (tone, style, personality)
            - Content pillar distribution
            - Top performing content types
            - Engagement metrics and recommendations
            """)

        if st.button("🚀 Analyze Company", type="primary", use_container_width=True):
            if not linkedin_url:
                st.error("❌ Please enter a LinkedIn URL")
            else:
                # Extract company name from URL
                company_name = linkedin_url.rstrip('/').split('/')[-1].replace('-', ' ').title()

                # Progress tracking
                progress_container = st.empty()
                results = {
                    "posts": {"status": "pending", "message": ""},
                    "voice": {"status": "pending", "message": ""},
                    "strategy": {"status": "pending", "message": ""},
                    "engagement": {"status": "pending", "message": ""}
                }

                # Step 1: Fetch LinkedIn Posts
                progress_container.info("📥 Fetching LinkedIn posts...")
                posts_result = fetch_linkedin_posts(linkedin_url)

                if posts_result.get("error"):
                    results["posts"]["status"] = "failed"
                    results["posts"]["message"] = posts_result["error"]
                    progress_container.error(f"❌ Error fetching posts: {posts_result['error']}")
                    st.error("⛔ Analysis stopped - cannot proceed without LinkedIn posts")

                    st.markdown("**Next steps:**")
                    st.markdown("• Check your RAPIDAPI_KEY in secrets.toml")
                    st.markdown("• Verify the LinkedIn URL is correct")
                    st.markdown("• Check your RapidAPI subscription status")
                    st.stop()
                else:
                    results["posts"]["status"] = "success"
                    results["posts"]["message"] = "Posts fetched successfully"

                    # Save to database
                    save_linkedin_posts_to_db(linkedin_url, posts_result.get("raw_response", {}))

                    # Extract posts array
                    posts_data = posts_result.get("data", {}).get("data", [])
                    num_posts = len(posts_data)

                    progress_container.success(f"✅ Fetched {num_posts} posts")

                    # Step 2: Run AI Analysis
                    progress_container.info(f"🤖 Analyzing {num_posts} posts with AI...")

                    analysis_result = analyze_company_complete(
                        posts_data,
                        company_name,
                        linkedin_url,
                        analysis_model
                    )

                    # Check each analysis component
                    voice_profile = analysis_result.get("voice_profile", {})
                    content_pillars = analysis_result.get("content_pillars", {})
                    engagement_metrics = analysis_result.get("engagement_metrics", {})

                    if voice_profile.get("error"):
                        results["voice"]["status"] = "failed"
                        results["voice"]["message"] = voice_profile["error"]
                    else:
                        results["voice"]["status"] = "success"

                    if content_pillars.get("error"):
                        results["strategy"]["status"] = "failed"
                        results["strategy"]["message"] = content_pillars["error"]
                    else:
                        results["strategy"]["status"] = "success"

                    if engagement_metrics.get("error"):
                        results["engagement"]["status"] = "failed"
                        results["engagement"]["message"] = engagement_metrics["error"]
                    else:
                        results["engagement"]["status"] = "success"

                    # Save to database
                    save_success = save_company_analysis(analysis_result)

                    # Show summary
                    progress_container.empty()

                    success_count = sum(1 for r in results.values() if r["status"] == "success")
                    total_count = len(results)

                    if success_count == total_count:
                        st.success(f"✅ Analysis complete! ({success_count}/{total_count} steps succeeded)")
                        st.balloons()
                    elif success_count > 0:
                        st.warning(f"⚠️ Partial success ({success_count}/{total_count} steps succeeded)")
                    else:
                        st.error(f"❌ Analysis failed ({success_count}/{total_count} steps succeeded)")

                    # Show details
                    with st.expander("📋 Analysis Details", expanded=success_count < total_count):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**✅ Successful:**")
                            for key, result in results.items():
                                if result["status"] == "success":
                                    st.markdown(f"• {key.title()}")

                        with col2:
                            st.markdown("**❌ Failed:**")
                            failed_any = False
                            for key, result in results.items():
                                if result["status"] == "failed":
                                    failed_any = True
                                    st.markdown(f"• {key.title()}")
                                    if result["message"]:
                                        st.caption(f"  {result['message']}")
                            if not failed_any:
                                st.markdown("• None")

                    if success_count > 0:
                        st.info("💡 Go to the 'View Companies' tab to see your analysis")

    # ============================================================================
    # TAB 2: VIEW COMPANIES
    # ============================================================================
    with tab2:
        st.markdown("### Your Analyzed Companies")

        # Fetch all companies
        companies = get_all_company_analyses(limit=50)

        if not companies:
            st.info("📭 No companies analyzed yet. Go to the 'Analyze New Company' tab to get started!")
        else:
            st.caption(f"Showing {len(companies)} compan{'y' if len(companies) == 1 else 'ies'}")

            for company in companies:
                company_url = company.get("company_url", "")
                company_name = company.get("company_name", "Unknown")
                posts_analyzed = company.get("posts_analyzed", 0)
                date_range = company.get("date_range", "Unknown")
                updated_at = company.get("updated_at", "Unknown")

                voice_profile = company.get("voice_profile", {})
                content_pillars = company.get("content_pillars", {})
                engagement_metrics = company.get("engagement_metrics", {})
                top_posts = company.get("top_posts", [])

                # Calculate health status
                data_checks = {
                    "Posts": posts_analyzed > 0,
                    "Voice": voice_profile and not voice_profile.get("error"),
                    "Strategy": content_pillars and not content_pillars.get("error"),
                    "Engagement": engagement_metrics and not engagement_metrics.get("error")
                }

                complete_count = sum(data_checks.values())
                completion_pct = (complete_count / 4) * 100

                if completion_pct == 100:
                    health_emoji = "🟢"
                    health_status = "Healthy"
                elif completion_pct >= 50:
                    health_emoji = "🟡"
                    health_status = "Partial"
                else:
                    health_emoji = "🔴"
                    health_status = "Issues"

                # Company card
                with st.expander(f"{health_emoji} **{company_name}** - {completion_pct:.0f}% complete", expanded=False):
                    st.caption(f"Last updated: {updated_at}")

                    # Health status
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Health Status:** {health_emoji} {health_status} ({complete_count}/4 analyses)")
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{company_url}"):
                            delete_company_analysis(company_url)
                            st.success("✅ Company deleted")
                            st.rerun()

                    # Show what's working vs failed
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**✅ Working:**")
                        for check_name, is_working in data_checks.items():
                            if is_working:
                                st.markdown(f"• {check_name}")

                    with col2:
                        st.markdown("**❌ Failed/Missing:**")
                        failed_any = False
                        for check_name, is_working in data_checks.items():
                            if not is_working:
                                failed_any = True
                                st.markdown(f"• {check_name}")
                        if not failed_any:
                            st.markdown("• None")

                    st.divider()

                    # Nested tabs for analysis details
                    detail_tabs = st.tabs(["📊 Overview", "🎯 Voice & Strategy", "📈 Engagement", "📥 Export"])

                    # Overview Tab
                    with detail_tabs[0]:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Posts Analyzed", posts_analyzed)
                        with col2:
                            avg_eng = engagement_metrics.get("avg_engagement", {}).get("total", 0) if engagement_metrics else 0
                            st.metric("Avg Engagement", f"{avg_eng:.0f}")
                        with col3:
                            voice_score = voice_profile.get("consistency_score", 0) if voice_profile else 0
                            st.metric("Voice Consistency", f"{voice_score}/10")

                        st.caption(f"Date Range: {date_range}")
                        st.caption(f"Analysis Model: {company.get('analysis_model', 'Unknown')}")

                    # Voice & Strategy Tab
                    with detail_tabs[1]:
                        if voice_profile and not voice_profile.get("error"):
                            st.markdown("#### 🎯 Voice Profile")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Overall Tone:** {voice_profile.get('overall_tone', 'Unknown')}")
                                st.markdown(f"**Writing Style:** {voice_profile.get('writing_style', 'Unknown')}")
                                st.markdown(f"**Formality:** {voice_profile.get('formality_level', 'Unknown')}")
                            with col2:
                                st.markdown(f"**Consistency Score:** {voice_profile.get('consistency_score', 0)}/10")
                                traits = voice_profile.get('personality_traits', [])
                                if traits:
                                    st.markdown(f"**Personality:** {', '.join(traits)}")

                            st.markdown(f"**Target Audience:** {voice_profile.get('target_audience', 'Unknown')}")
                            st.markdown(f"**Voice Characteristics:** {voice_profile.get('unique_voice_characteristics', 'Unknown')}")
                        else:
                            st.warning("⚠️ Voice profile not available")

                        st.divider()

                        if content_pillars and not content_pillars.get("error"):
                            st.markdown("####📊 Content Strategy")

                            pillar_dist = content_pillars.get("content_pillar_distribution", {})
                            if pillar_dist:
                                st.markdown("**Content Pillar Distribution:**")
                                for pillar, percentage in sorted(pillar_dist.items(), key=lambda x: x[1], reverse=True):
                                    st.markdown(f"• {pillar.replace('_', ' ').title()}: {percentage}%")

                            st.markdown(f"**Primary Focus:** {content_pillars.get('primary_focus', 'Unknown')}")

                            themes = content_pillars.get('content_themes', [])
                            if themes:
                                st.markdown(f"**Content Themes:** {', '.join(themes)}")
                        else:
                            st.warning("⚠️ Content strategy not available")

                    # Engagement Tab
                    with detail_tabs[2]:
                        if engagement_metrics and not engagement_metrics.get("error"):
                            st.markdown("#### 📈 Engagement Metrics")

                            avg_eng = engagement_metrics.get("avg_engagement", {})
                            if avg_eng:
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Avg Likes", f"{avg_eng.get('likes', 0):.0f}")
                                with col2:
                                    st.metric("Avg Comments", f"{avg_eng.get('comments', 0):.0f}")
                                with col3:
                                    st.metric("Avg Reposts", f"{avg_eng.get('reposts', 0):.0f}")
                                with col4:
                                    st.metric("Avg Total", f"{avg_eng.get('total', 0):.0f}")

                            st.divider()

                            top_content = engagement_metrics.get("top_performing_content_types", [])
                            if top_content:
                                st.markdown("**Top Performing Content Types:**")
                                for item in top_content[:3]:
                                    st.markdown(f"• **{item.get('type', 'Unknown')}** ({item.get('avg_engagement', 0):.0f} avg)")
                                    st.caption(f"  {item.get('why_it_works', '')}")

                            st.divider()

                            if top_posts:
                                st.markdown("**Top 5 Posts:**")
                                for i, post in enumerate(top_posts, 1):
                                    with st.expander(f"#{i} - {post.get('engagement', 0)} engagement"):
                                        st.markdown(post.get('text', 'No text'))
                                        if post.get('url'):
                                            st.markdown(f"[View Post]({post['url']})")
                        else:
                            st.warning("⚠️ Engagement data not available")

                    # Export Tab
                    with detail_tabs[3]:
                        st.markdown("#### 📥 Export Analysis Data")

                        export_data = {
                            "company_url": company_url,
                            "company_name": company_name,
                            "posts_analyzed": posts_analyzed,
                            "date_range": date_range,
                            "voice_profile": voice_profile,
                            "content_pillars": content_pillars,
                            "engagement_metrics": engagement_metrics,
                            "top_posts": top_posts,
                            "updated_at": updated_at
                        }

                        st.download_button(
                            label="📄 Download Full Analysis (JSON)",
                            data=json.dumps(export_data, indent=2),
                            file_name=f"{company_name.replace(' ', '_')}_analysis.json",
                            mime="application/json",
                            use_container_width=True
                        )
