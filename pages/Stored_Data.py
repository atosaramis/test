"""
Stored Data Viewer
"""

import streamlit as st
import pandas as pd
import json

from seo_functions import get_all_keywords_from_db, get_all_linkedin_posts_from_db, get_all_company_analyses

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Please login first")
    st.stop()

# Logout in sidebar
with st.sidebar:
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

st.title("📊 Stored Data")

st.markdown("View and manage data stored in the database.")

# Tabs for different data types
tab1, tab2, tab3 = st.tabs(["Keywords Data", "LinkedIn Posts", "🏢 Company Strategy Analysis"])

with tab1:
    st.subheader("📈 Stored Keywords")

    # Load keywords from DB
    if st.button("Load Keywords from Database"):
        with st.spinner("Loading keywords..."):
            keywords = get_all_keywords_from_db(1000)

        if keywords:
            st.success(f"Loaded {len(keywords)} keywords from database")

            # Convert to DataFrame for display
            df = pd.DataFrame(keywords)

            # Display summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Keywords", len(keywords))
            with col2:
                avg_score = df['opportunity_score'].mean() if 'opportunity_score' in df.columns else 0
                st.metric("Avg Opportunity Score", f"{avg_score:.1f}")
            with col3:
                total_volume = df['search_volume'].sum() if 'search_volume' in df.columns else 0
                st.metric("Total Search Volume", f"{total_volume:,}")

            # Filters
            st.subheader("Filters")
            col1, col2 = st.columns(2)
            with col1:
                min_score = st.slider("Min Opportunity Score", 0.0, 10.0, 0.0)
            with col2:
                competition_filter = st.selectbox("Competition Level", ["ALL", "LOW", "MEDIUM", "HIGH"])

            # Apply filters
            filtered_df = df.copy()
            if min_score > 0:
                filtered_df = filtered_df[filtered_df['opportunity_score'] >= min_score]
            if competition_filter != "ALL":
                filtered_df = filtered_df[filtered_df['competition_level'] == competition_filter]

            st.subheader(f"Filtered Results ({len(filtered_df)} keywords)")

            # Display table
            st.dataframe(filtered_df, use_container_width=True)

            # Download button
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                "📥 Download Filtered CSV",
                data=csv,
                file_name="stored_keywords.csv",
                mime="text/csv"
            )
        else:
            st.info("No keywords found in database. Start by researching some keywords!")

with tab2:
    st.subheader("📱 Stored LinkedIn Posts")

    # Load posts from DB
    if st.button("Load LinkedIn Posts from Database"):
        with st.spinner("Loading posts..."):
            posts = get_all_linkedin_posts_from_db(100)

        if posts:
            st.success(f"Loaded {len(posts)} URL entries from database")

            for post_entry in posts:
                url = post_entry['url']
                post_data = post_entry['post_data']
                created_at = post_entry['created_at']

                with st.expander(f"🔗 {url} - {created_at}"):
                    # Summary
                    # Handle different data structures
                    if isinstance(post_data, dict):
                        data = post_data.get('data', {})
                        if isinstance(data, dict):
                            posts_list = data.get('data', [])
                        else:
                            posts_list = []
                    else:
                        st.error(f"Invalid data format: expected dict, got {type(post_data).__name__}")
                        posts_list = []

                    if posts_list:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Posts", len(posts_list))
                        with col2:
                            total_likes = sum(p.get('num_likes', 0) for p in posts_list if isinstance(p, dict))
                            st.metric("Total Likes", f"{total_likes:,}")
                        with col3:
                            total_comments = sum(p.get('num_comments', 0) for p in posts_list if isinstance(p, dict))
                            st.metric("Total Comments", f"{total_comments:,}")

                        # Download button for this entry
                        st.download_button(
                            f"📥 Download JSON for {url.split('/')[-2] if '/' in url else 'data'}",
                            data=json.dumps(post_data, indent=2),
                            file_name=f"linkedin_posts_{url.split('/')[-2] if '/' in url else 'data'}_{created_at[:10]}.json",
                            mime="application/json",
                            key=f"download_{url}_{created_at}"
                        )

                        # Show first few posts
                        st.markdown("**Recent Posts:**")
                        for i, post in enumerate(posts_list[:3]):
                            if isinstance(post, dict):
                                st.write(f"**Post {i+1}:** {post.get('text', '')[:100]}...")
                                st.caption(f"Likes: {post.get('num_likes', 0)} | Comments: {post.get('num_comments', 0)}")
                                st.markdown("---")
                    else:
                        st.info("No posts found in this entry")
        else:
            st.info("No LinkedIn posts found in database. Start by fetching some company posts!")

with tab3:
    st.subheader("🏢 Company Strategy Analysis")

    # Load company analyses from DB
    if st.button("Load Company Analyses from Database"):
        with st.spinner("Loading company analyses..."):
            companies = get_all_company_analyses(limit=50)

        if companies:
            st.success(f"Loaded {len(companies)} companies from database")

            # Summary stats
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Companies", len(companies))

            with col2:
                total_posts = sum(c.get('posts_analyzed', 0) for c in companies)
                st.metric("Total Posts Analyzed", f"{total_posts:,}")

            with col3:
                avg_posts = total_posts / len(companies) if companies else 0
                st.metric("Avg Posts per Company", f"{avg_posts:.0f}")

            st.divider()

            # Display each company's analysis
            for company in companies:
                company_name = company.get('company_name', 'Unknown')
                company_url = company.get('company_url', '')

                with st.expander(f"🏢 {company_name} ({company.get('posts_analyzed', 0)} posts analyzed)", expanded=False):

                    # Basic info
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Date Range:** {company.get('date_range', 'N/A')}")
                        st.write(f"**Model:** {company.get('analysis_model', 'N/A')}")
                    with col2:
                        st.write(f"**Created:** {company.get('created_at', 'N/A')[:10]}")
                        st.write(f"**Updated:** {company.get('updated_at', 'N/A')[:10]}")

                    if company_url:
                        st.link_button("View LinkedIn Profile", company_url, use_container_width=True)

                    st.divider()

                    # Analysis tabs
                    c_tab1, c_tab2, c_tab3, c_tab4, c_tab5 = st.tabs(["🎤 Voice Profile", "📋 Content Strategy", "📈 Engagement", "🔍 Ranked Keywords", "🔮 AI Perception"])

                    with c_tab1:
                        voice = company.get('voice_profile', {})

                        if voice:
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

                            if voice.get('target_audience'):
                                st.info(f"**Target Audience:** {voice['target_audience']}")

                            if voice.get('unique_voice_characteristics'):
                                st.success(f"**Unique:** {voice['unique_voice_characteristics']}")
                        else:
                            st.info("No voice profile data")

                    with c_tab2:
                        strategy = company.get('content_pillars', {})

                        if strategy:
                            st.write(f"**Primary Focus:** {strategy.get('primary_focus', 'N/A')}")

                            # Content pillar distribution
                            if strategy.get('content_pillar_distribution'):
                                st.write("**Content Distribution:**")
                                pillars = strategy['content_pillar_distribution']
                                for pillar, percentage in sorted(pillars.items(), key=lambda x: x[1], reverse=True):
                                    st.progress(percentage / 100, text=f"{pillar}: {percentage}%")

                            # Topic clusters
                            if strategy.get('topic_clusters'):
                                st.write("**Topic Clusters:**")
                                for cluster in strategy['topic_clusters'][:5]:
                                    st.write(f"• **{cluster.get('theme')}** ({cluster.get('percentage', 0)}%)")

                            # Strategic positioning
                            if strategy.get('strategic_positioning'):
                                st.info(f"**Positioning:** {strategy['strategic_positioning']}")
                        else:
                            st.info("No content strategy data")

                    with c_tab3:
                        engagement = company.get('engagement_metrics', {})

                        if engagement:
                            # Average engagement
                            if engagement.get('avg_engagement'):
                                avg = engagement['avg_engagement']
                                col1, col2, col3, col4 = st.columns(4)

                                with col1:
                                    st.metric("Avg Likes", f"{avg.get('likes', 0):,}")
                                with col2:
                                    st.metric("Avg Comments", f"{avg.get('comments', 0):,}")
                                with col3:
                                    st.metric("Avg Reposts", f"{avg.get('reposts', 0):,}")
                                with col4:
                                    st.metric("Avg Total", f"{avg.get('total', 0):,}")

                            # Top performing content
                            if engagement.get('top_performing_content_types'):
                                st.write("**What Works:**")
                                for content_type in engagement['top_performing_content_types'][:3]:
                                    st.success(f"**{content_type.get('type')}** - {content_type.get('avg_engagement', 0):,} avg")

                            # Recommendations
                            if engagement.get('strategic_recommendations'):
                                st.write("**Recommendations:**")
                                for rec in engagement['strategic_recommendations'][:3]:
                                    st.write(f"• {rec}")
                        else:
                            st.info("No engagement data")

                    with c_tab4:
                        ranked_keywords = company.get('ranked_keywords', {})
                        domain = company.get('ranked_keywords_domain')

                        if ranked_keywords and not ranked_keywords.get('error'):
                            keywords_list = ranked_keywords.get('keywords', [])
                            summary = ranked_keywords.get('summary', {})

                            # Summary metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Keywords", summary.get('total_keywords', 0))
                            with col2:
                                st.metric("Avg Position", summary.get('avg_position', 0))
                            with col3:
                                st.metric("Top 3", summary.get('top_3_count', 0))
                            with col4:
                                traffic = summary.get('estimated_monthly_traffic_value', 0)
                                st.metric("Traffic Value", f"${traffic:,.0f}/mo")

                            if domain:
                                st.caption(f"Domain: {domain}")

                            # Show first 20 keywords in table
                            if keywords_list:
                                st.write(f"**Top 20 Keywords:**")
                                df = pd.DataFrame(keywords_list[:20])
                                df = df[['keyword', 'position', 'search_volume', 'type']]
                                df.columns = ['Keyword', 'Position', 'Volume', 'Type']
                                df['Volume'] = df['Volume'].apply(lambda x: f"{x:,}")
                                st.dataframe(df, use_container_width=True)

                                # Download all keywords
                                csv = pd.DataFrame(keywords_list).to_csv(index=False)
                                st.download_button(
                                    "📥 Download All Keywords CSV",
                                    data=csv,
                                    file_name=f"keywords_{domain}.csv",
                                    mime="text/csv",
                                    key=f"download_kw_{company.get('id')}"
                                )
                        else:
                            st.info("No ranked keywords data available")

                    with c_tab5:
                        ai_perception = company.get('ai_perception', {})

                        if ai_perception and not ai_perception.get('error'):
                            provider = ai_perception.get('provider', 'Unknown').upper()
                            responses = ai_perception.get('responses', [])

                            st.write(f"**Provider:** {provider}")
                            st.write(f"**Responses:** {len(responses)}")

                            # Display each Q&A
                            for i, resp in enumerate(responses, 1):
                                prompt = resp.get('prompt', '')
                                response_text = resp.get('response', '')
                                error = resp.get('error')

                                with st.expander(f"Q{i}: {prompt[:80]}..."):
                                    st.write(f"**Question:** {prompt}")
                                    if error:
                                        st.error(f"Error: {error}")
                                    else:
                                        st.write(f"**Answer:** {response_text}")

                            # Download
                            ai_text = "\n\n".join([
                                f"Q: {r.get('prompt', '')}\n\nA: {r.get('response', '')}"
                                for r in responses
                            ])
                            st.download_button(
                                "📥 Download AI Responses",
                                data=ai_text,
                                file_name=f"ai_{company_name.replace(' ', '_')}.txt",
                                mime="text/plain",
                                key=f"download_ai_{company.get('id')}"
                            )
                        else:
                            st.info("No AI perception data available")

                    st.divider()

                    # Download individual company data
                    st.download_button(
                        label="📥 Download Company Analysis (JSON)",
                        data=json.dumps(company, indent=2),
                        file_name=f"company_analysis_{company_name.replace(' ', '_')}.json",
                        mime="application/json",
                        key=f"download_company_{company.get('id')}"
                    )

            st.divider()

            # Download all companies
            all_companies_df = pd.DataFrame([
                {
                    'Company': c.get('company_name'),
                    'Posts Analyzed': c.get('posts_analyzed'),
                    'Tone': c.get('voice_profile', {}).get('overall_tone'),
                    'Style': c.get('voice_profile', {}).get('writing_style'),
                    'Consistency': c.get('voice_profile', {}).get('consistency_score'),
                    'Primary Focus': c.get('content_pillars', {}).get('primary_focus'),
                    'Avg Likes': c.get('engagement_metrics', {}).get('avg_engagement', {}).get('likes'),
                    'Avg Comments': c.get('engagement_metrics', {}).get('avg_engagement', {}).get('comments'),
                    'Avg Engagement': c.get('engagement_metrics', {}).get('avg_engagement', {}).get('total'),
                    'Date Range': c.get('date_range'),
                    'Model': c.get('analysis_model'),
                }
                for c in companies
            ])

            csv = all_companies_df.to_csv(index=False)
            st.download_button(
                "📥 Download All Companies (CSV)",
                data=csv,
                file_name="company_analyses.csv",
                mime="text/csv"
            )

        else:
            st.info("No company analyses found. Go to 'LinkedIn Posts' page to analyze companies!")

st.info("💡 Data is automatically saved when you research keywords or analyze companies.")
