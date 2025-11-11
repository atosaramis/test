"""
Complete Keywords Research Tool Module for Digital Marketers
"""

import streamlit as st
import sys
import os
import json
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_functions import (
    get_keyword_data, get_keyword_suggestions, get_keywords_for_site,
    calculate_opportunity_score, detect_seasonality,
    calculate_growth_rate, generate_recommendation, save_keywords_to_db
)

def render_keywords_app():
    """Main function to render the Keyword Research app."""

    st.title("📊 Complete Keywords Research")

    # HOW IT WORKS SECTION
    with st.expander("ℹ️ How Keyword Research Works", expanded=False):
        st.markdown("""
        ### Powered by DataForSEO Keywords Data API

        This tool uses real-time data from **DataForSEO**, which aggregates keyword metrics from Google Ads and Google Search Console
        to provide accurate, up-to-date keyword intelligence for SEO and PPC campaigns.

        #### What You Can Research:

        **1. Single Keyword Analysis**
        - Get detailed metrics for a specific keyword
        - See search volume, cost-per-click, and competition data

        **2. Related Keywords (100 suggestions)**
        - Discover up to 100 related keyword ideas
        - Find variations and long-tail opportunities

        **3. Competitor Keyword Analysis**
        - Enter a competitor's URL to see what keywords they rank for
        - Discover gaps in your keyword strategy

        ---

        ### Understanding the Metrics

        **Search Volume** 📊
        - Average monthly searches for the keyword on Google
        - Higher volume = more potential traffic (but usually more competition)

        **CPC (Cost-Per-Click)** 💰
        - Average cost advertisers pay per click in Google Ads
        - Higher CPC often indicates commercial intent and value
        - Note: CPC data is only available for United States location

        **Competition** ⚔️
        - Represents how many advertisers compete for this keyword in Google Ads
        - Scale: 0 to 1 (0 = low competition, 1 = high competition)
        - Categorized as: **LOW**, **MEDIUM**, or **HIGH**

        **Opportunity Score** 🎯
        - Our proprietary calculation combining search volume and competition
        - Scale: 0 to 10 (higher = better opportunity)
        - 🟢 7-10: High opportunity | 🟡 4-7: Moderate | 🔴 0-4: Low

        **Growth Rate** 📈
        - Percentage change in search volume over the last 12 months
        - Positive % = growing interest | Negative % = declining interest

        **Seasonality Detection** 🗓️
        - Identifies keywords with seasonal search patterns
        - Shows peak months when search volume spikes
        - Example: "halloween costumes" peaks in October

        **12-Month Trend** 📉
        - Historical search volume for each of the past 12 months
        - Visualize search patterns and growth trends
        - Useful for planning content calendars and ad spend

        ---

        ### How to Use This Tool

        1. **Enter a keyword or competitor URL** above
        2. **Review the results** - All keywords are sorted by opportunity score by default
        3. **Apply filters** to narrow down keywords by volume, competition, or trend
        4. **Select keywords** using checkboxes to compare trends side-by-side
        5. **Download data** as CSV or JSON for further analysis

        **Pro Tip:** Start with broad keywords to discover related terms, then filter by opportunity score
        to find the best keywords for your SEO strategy.
        """)

    # Initialize session state
    if "keywords_data" not in st.session_state:
        st.session_state.keywords_data = []
    if "selected_keywords" not in st.session_state:
        st.session_state.selected_keywords = set()

    # SECTION 1: INPUT
    st.subheader("1. Get Keywords")

    input_method = st.radio("", ["Search for keyword", "Analyze competitor URL"], horizontal=True, label_visibility="collapsed")

    col1, col2 = st.columns([4, 1])

    if input_method == "Search for keyword":
        with col1:
            keyword_input = st.text_input("Enter keyword", placeholder="e.g., biotech marketing", label_visibility="collapsed")
        with col2:
            get_suggestions = st.checkbox("Get 100 related keywords", value=False)
    else:
        with col1:
            url_input = st.text_input("Competitor URL", placeholder="e.g., competitor.com", label_visibility="collapsed")
        with col2:
            get_suggestions = False  # Not applicable for URL input

    search_button = st.button("🔍 Research Keywords", type="primary", use_container_width=True)

    # PROCESS INPUT
    if search_button:
        if input_method == "Search for keyword" and not keyword_input:
            st.warning("Enter a keyword")
        elif input_method == "Analyze competitor URL" and not url_input:
            st.warning("Enter a competitor URL")
        else:
            with st.spinner("Fetching keyword data..."):
                all_keywords = []

                if input_method == "Search for keyword":
                    if get_suggestions:
                        # Get suggestions
                        response = get_keyword_suggestions(keyword_input, limit=100)
                        if response.get("error"):
                            st.error(response['error'])
                        else:
                            all_keywords = response.get("keywords", [])
                            st.success(f"Found {len(all_keywords)} related keywords")
                    else:
                        # Get single keyword data
                        response = get_keyword_data(keyword_input)
                        if response.get("error"):
                            st.error(response['error'])
                        else:
                            all_keywords = [response.get("result", {})]

                else:  # Competitor URL
                    response = get_keywords_for_site(url_input, limit=100)
                    if response.get("error"):
                        st.error(response['error'])
                    else:
                        all_keywords = response.get("keywords", [])
                        st.success(f"Found {len(all_keywords)} keywords from {url_input}")

                # Process and enrich keyword data
                if all_keywords:
                    enriched_keywords = []
                    for kw in all_keywords:
                        kw_copy = kw.copy()
                        kw_copy["opportunity_score"] = calculate_opportunity_score(kw)
                        kw_copy["growth_rate"] = calculate_growth_rate(kw)
                        seasonality = detect_seasonality(kw)
                        kw_copy["is_seasonal"] = seasonality["is_seasonal"]
                        kw_copy["peak_months"] = ", ".join(seasonality["peak_months"][:3])
                        kw_copy["recommendation"] = generate_recommendation(kw)
                        enriched_keywords.append(kw_copy)

                    st.session_state.keywords_data = enriched_keywords
                    st.session_state.selected_keywords = set()

                    # Save to database
                    if save_keywords_to_db(enriched_keywords):
                        st.success(f"✅ Saved {len(enriched_keywords)} keywords to database")
                    else:
                        st.warning("⚠️ Failed to save to database, but data is still available in session")

    # SECTION 2: RESULTS
    if st.session_state.keywords_data:
        st.divider()

        st.subheader(f"2. Results ({len(st.session_state.keywords_data)} keywords)")

        # Download buttons
        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            # Download all as JSON
            all_json = json.dumps(st.session_state.keywords_data, indent=2)
            st.download_button(
                "📥 Download JSON",
                data=all_json,
                file_name="keywords_data.json",
                mime="application/json"
            )

        with col2:
            # Download all as CSV - only include columns that exist
            df = pd.DataFrame(st.session_state.keywords_data)

            # Select columns that exist in the dataframe
            desired_cols = ["keyword", "search_volume", "cpc", "competition_level", "opportunity_score", "growth_rate"]
            available_cols = [col for col in desired_cols if col in df.columns]

            if available_cols:
                csv = df[available_cols].to_csv(index=False)
            else:
                # If none of the desired columns exist, export all columns
                csv = df.to_csv(index=False)

            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name="keywords_data.csv",
                mime="text/csv"
            )

        with col3:
            # View all data button
            if st.button("📊 View All Data"):
                st.session_state.show_all_data = not st.session_state.get("show_all_data", False)

        # Show all data dashboard if requested
        if st.session_state.get("show_all_data", False):
            st.divider()
            st.subheader("📊 Complete Data Dashboard")

            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["Summary Table", "Full Details", "Raw JSON"])

            with tab1:
                # Summary table with all available columns
                df_display = pd.DataFrame(st.session_state.keywords_data)

                # Reorder columns to put most important first
                preferred_order = ["keyword", "search_volume", "cpc", "competition_level",
                                 "opportunity_score", "growth_rate", "is_seasonal", "peak_months"]
                cols = [c for c in preferred_order if c in df_display.columns]
                other_cols = [c for c in df_display.columns if c not in cols and c not in ["monthly_searches", "recommendation", "raw_response"]]
                final_cols = cols + other_cols

                st.dataframe(df_display[final_cols], use_container_width=True, height=600)

            with tab2:
                # Detailed view of each keyword
                st.markdown(f"**Showing all {len(st.session_state.keywords_data)} keywords:**")

                for idx, kw in enumerate(st.session_state.keywords_data[:100]):  # Limit to 100 for performance
                    with st.expander(f"{idx+1}. {kw.get('keyword', 'Unknown')} - {kw.get('search_volume', 0):,} searches/mo"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Main Metrics:**")
                            for key, value in kw.items():
                                if key not in ["monthly_searches", "raw_response", "recommendation"] and not isinstance(value, (dict, list)):
                                    st.write(f"- **{key}:** {value}")

                        with col2:
                            if kw.get("recommendation"):
                                st.markdown("**Recommendation:**")
                                st.info(kw["recommendation"])

                            if kw.get("monthly_searches"):
                                st.markdown("**12-Month Trend:**")
                                monthly_df = pd.DataFrame(kw["monthly_searches"])
                                if not monthly_df.empty and "search_volume" in monthly_df.columns:
                                    st.line_chart(monthly_df.set_index(monthly_df.index)["search_volume"])

                if len(st.session_state.keywords_data) > 100:
                    st.info(f"Showing first 100 of {len(st.session_state.keywords_data)} keywords. Download JSON for complete data.")

            with tab3:
                # Raw JSON view
                st.markdown("**Complete Raw Data:**")
                st.json(st.session_state.keywords_data[:20])  # Show first 20 for performance
                if len(st.session_state.keywords_data) > 20:
                    st.info(f"Showing first 20 of {len(st.session_state.keywords_data)} keywords. Download JSON for complete data.")

            st.divider()

        # SECTION 3: FILTERS
        st.markdown("**Filters:**")

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            min_volume = st.number_input("Min Volume", min_value=0, value=0, step=100)

        with filter_col2:
            competition_filter = st.selectbox("Competition", ["ALL", "LOW", "MEDIUM", "HIGH"])

        with filter_col3:
            trend_filter = st.selectbox("Trend", ["ALL", "Growing", "Declining", "Stable"])

        with filter_col4:
            sort_by = st.selectbox("Sort by", ["Opportunity Score", "Search Volume", "CPC", "Growth Rate"])

        # Apply filters
        filtered_keywords = st.session_state.keywords_data.copy()

        # Volume filter
        filtered_keywords = [kw for kw in filtered_keywords if kw.get("search_volume", 0) >= min_volume]

        # Competition filter
        if competition_filter != "ALL":
            filtered_keywords = [kw for kw in filtered_keywords if kw.get("competition_level") == competition_filter]

        # Trend filter
        if trend_filter == "Growing":
            filtered_keywords = [kw for kw in filtered_keywords if kw.get("growth_rate", 0) > 5]
        elif trend_filter == "Declining":
            filtered_keywords = [kw for kw in filtered_keywords if kw.get("growth_rate", 0) < -5]
        elif trend_filter == "Stable":
            filtered_keywords = [kw for kw in filtered_keywords if -5 <= kw.get("growth_rate", 0) <= 5]

        # Sort
        if sort_by == "Opportunity Score":
            filtered_keywords = sorted(filtered_keywords, key=lambda x: x.get("opportunity_score", 0), reverse=True)
        elif sort_by == "Search Volume":
            filtered_keywords = sorted(filtered_keywords, key=lambda x: x.get("search_volume", 0), reverse=True)
        elif sort_by == "CPC":
            filtered_keywords = sorted(filtered_keywords, key=lambda x: x.get("cpc", 0), reverse=True)
        elif sort_by == "Growth Rate":
            filtered_keywords = sorted(filtered_keywords, key=lambda x: x.get("growth_rate", 0), reverse=True)

        st.caption(f"Showing {len(filtered_keywords)} of {len(st.session_state.keywords_data)} keywords")

        # SECTION 4: KEYWORDS TABLE
        st.divider()

        for idx, kw in enumerate(filtered_keywords[:50]):  # Show top 50
            keyword = kw.get("keyword", "")
            volume = kw.get("search_volume", 0)
            cpc = kw.get("cpc", 0) or 0
            competition = kw.get("competition_level", "N/A")
            opp_score = kw.get("opportunity_score", 0)
            growth = kw.get("growth_rate", 0)
            seasonal = kw.get("peak_months", "")

            # Color coding based on opportunity score
            if opp_score >= 7.0:
                color = "🟢"
            elif opp_score >= 4.0:
                color = "🟡"
            else:
                color = "🔴"

            # Trend arrow
            if growth > 10:
                trend_icon = "📈"
            elif growth < -10:
                trend_icon = "📉"
            else:
                trend_icon = "➡️"

            # Checkbox for selection
            col_check, col_keyword, col_metrics = st.columns([0.3, 2, 3])

            with col_check:
                is_selected = st.checkbox("", value=keyword in st.session_state.selected_keywords, key=f"check_{idx}", label_visibility="collapsed")
                if is_selected:
                    st.session_state.selected_keywords.add(keyword)
                else:
                    st.session_state.selected_keywords.discard(keyword)

            with col_keyword:
                st.markdown(f"{color} **{keyword}**")
                if seasonal:
                    st.caption(f"Peaks: {seasonal}")

            with col_metrics:
                metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

                with metric_col1:
                    st.metric("Volume", f"{volume:,}", label_visibility="visible")

                with metric_col2:
                    st.metric("CPC", f"${cpc:.2f}", label_visibility="visible")

                with metric_col3:
                    st.caption("Competition")
                    st.write(competition)

                with metric_col4:
                    st.metric(f"{trend_icon}", f"{growth:+.1f}%", label_visibility="collapsed")

                with metric_col5:
                    st.metric("Score", f"{opp_score}/10", label_visibility="visible")

        if len(filtered_keywords) > 50:
            st.info(f"Showing top 50. Download CSV for full list of {len(filtered_keywords)} keywords.")

        # SECTION 5: COMPARISON CHART
        if len(st.session_state.selected_keywords) > 0:
            st.divider()

            st.subheader(f"3. Trend Comparison ({len(st.session_state.selected_keywords)} selected)")

            # Get selected keywords data
            selected_kw_data = [kw for kw in st.session_state.keywords_data if kw.get("keyword") in st.session_state.selected_keywords]

            # Create Plotly chart
            fig = go.Figure()

            for kw in selected_kw_data[:10]:  # Max 10 lines
                monthly = kw.get("monthly_searches", [])
                if monthly:
                    months = [f"{m.get('month')}/{m.get('year')}" for m in reversed(monthly)]
                    volumes = [m.get("search_volume", 0) for m in reversed(monthly)]

                    fig.add_trace(go.Scatter(
                        x=months,
                        y=volumes,
                        mode='lines+markers',
                        name=kw.get("keyword", ""),
                        line=dict(width=2)
                    ))

            fig.update_layout(
                title="12-Month Search Volume Trends",
                xaxis_title="Month",
                yaxis_title="Search Volume",
                hovermode='x unified',
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)

            # Auto-recommendation
            if selected_kw_data:
                best_kw = max(selected_kw_data, key=lambda x: x.get("opportunity_score", 0))
                st.success(f"**Recommendation:** '{best_kw.get('keyword')}' has the highest opportunity score ({best_kw.get('opportunity_score')}/10)")

            # SECTION 6: DETAILED INSIGHTS
            st.divider()

            st.subheader("4. Detailed Insights")

            for kw in selected_kw_data:
                with st.expander(f"{kw.get('keyword', '')} - Full Analysis"):
                    st.markdown(kw.get("recommendation", ""))

                    insight_col1, insight_col2 = st.columns(2)

                    with insight_col1:
                        st.markdown("**Metrics:**")
                        st.write(f"- Volume: {kw.get('search_volume', 0):,}/month")
                        st.write(f"- CPC: ${kw.get('cpc', 0):.2f}")
                        st.write(f"- Competition: {kw.get('competition_level', 'N/A')}")
                        st.write(f"- Growth: {kw.get('growth_rate', 0):+.1f}%")

                    with insight_col2:
                        st.markdown("**Seasonality:**")
                        if kw.get("is_seasonal"):
                            st.write(f"✅ Seasonal keyword")
                            if kw.get("peak_months"):
                                st.write(f"Peak months: {kw.get('peak_months')}")
                        else:
                            st.write("➡️ Stable year-round")

                    # Monthly data
                    monthly = kw.get("monthly_searches", [])
                    if monthly:
                        st.markdown("**Monthly Search Volume:**")
                        monthly_df = pd.DataFrame(monthly)
                        monthly_df = monthly_df.sort_values(by=["year", "month"], ascending=False)
                        monthly_df["month_year"] = monthly_df.apply(lambda x: f"{x['month']}/{x['year']}", axis=1)
                        st.dataframe(monthly_df[["month_year", "search_volume"]], use_container_width=True, hide_index=True)

    else:
        st.info("👆 Enter a keyword or competitor URL above to start researching")
