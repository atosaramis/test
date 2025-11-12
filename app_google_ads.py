"""
Google Ads Intelligence - Discover paid keywords and ad strategies
Analyzes Google Ads campaigns for any domain using DataForSEO Labs API
"""

import streamlit as st
import os
import requests
import pandas as pd
from typing import Dict, Any, Optional, List
import base64


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def get_google_ads_data(domain: str, location_code: int = 2840, limit: int = 100) -> Optional[Dict[str, Any]]:
    """
    Get Google Ads data for a domain using DataForSEO Labs API.

    Args:
        domain: Domain name (e.g., "example.com")
        location_code: Location code (default: 2840 for United States)
        limit: Number of results to return (default: 100)

    Returns:
        dict: API response with paid keywords data or None if error
    """
    login = get_credential("DATAFORSEO_LOGIN")
    password = get_credential("DATAFORSEO_PASSWORD")

    if not login or not password:
        st.error("❌ DataForSEO credentials not configured")
        st.info("💡 Add DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD to secrets.toml")
        return None

    # Prepare authentication
    credentials = f"{login}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # API endpoint
    url = "https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live"

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

    payload = [
        {
            "target": domain,
            "location_code": location_code,
            "language_code": "en",
            "filters": [
                ["ranked_serp_element.serp_item.is_paid", "=", True]
            ],
            "limit": limit,
            "order_by": ["ranked_serp_element.serp_item.rank_absolute,asc"]
        }
    ]

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()

        # Check if request was successful
        if data.get("status_code") == 20000:
            return data
        else:
            st.error(f"❌ API Error: {data.get('status_message', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request failed: {str(e)}")
        return None


def render_google_ads_app():
    """Render the Google Ads Intelligence interface."""

    st.markdown("## 📢 Google Ads Intelligence")
    st.caption("Discover what keywords competitors are bidding on in Google Ads")

    # Check credentials in sidebar
    with st.sidebar:
        st.markdown("### Configuration")
        login = get_credential("DATAFORSEO_LOGIN")
        password = get_credential("DATAFORSEO_PASSWORD")

        if login and password:
            st.success(f"✅ DataForSEO: {login[:5]}...")
        else:
            st.error("❌ DataForSEO credentials missing")

        st.markdown("### Settings")
        location_options = {
            "United States": 2840,
            "United Kingdom": 2826,
            "Canada": 2124,
            "Australia": 2036
        }
        location_name = st.selectbox("Location", list(location_options.keys()))
        location_code = location_options[location_name]

        limit = st.slider("Max Results", min_value=10, max_value=1000, value=100, step=10)

    # Main input
    st.markdown("### Enter Domain to Analyze")

    col1, col2 = st.columns([3, 1])

    with col1:
        domain_input = st.text_input(
            "Domain",
            placeholder="example.com",
            help="Enter domain without http:// or www",
            label_visibility="collapsed"
        )

    with col2:
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)

    # Example domains
    st.markdown("**Examples:** hubspot.com, salesforce.com, semrush.com")

    # Process analysis
    if analyze_button and domain_input:
        # Clean domain input
        domain = domain_input.strip().lower()
        domain = domain.replace("http://", "").replace("https://", "").replace("www.", "")
        domain = domain.split("/")[0]  # Remove any path

        with st.spinner(f"🔍 Analyzing Google Ads campaigns for {domain}..."):
            result = get_google_ads_data(domain, location_code, limit)

        # Debug section
        with st.expander("🐛 Debug Info - API Request"):
            st.write(f"**Original input:** `{domain_input}`")
            st.write(f"**Cleaned domain sent to API:** `{domain}`")
            st.write(f"**Location:** {location_name} ({location_code})")
            st.write(f"**Max Results:** {limit}")

        if result and result.get("tasks"):
            task = result["tasks"][0]

            # Show full task response in debug
            with st.expander("🐛 Debug Info - Full API Response"):
                st.json(result)

            if task.get("result") and len(task["result"]) > 0:
                ads_data = task["result"][0]

                # Display summary
                st.markdown("---")
                st.markdown(f"### 📊 Google Ads Results for **{ads_data.get('target', domain)}**")

                # Metrics
                total_count = ads_data.get("total_count", 0)
                items_count = ads_data.get("items_count", 0)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Paid Keywords", total_count)
                with col2:
                    st.metric("Showing", items_count)
                with col3:
                    st.metric("Location", location_name)
                with col4:
                    cost = task.get("cost", 0)
                    st.metric("API Cost", f"${cost:.4f}")

                # Display keywords
                if ads_data.get("items"):
                    st.markdown("### 🎯 Paid Keywords & Ad Data")

                    # Prepare data for table
                    keywords_list = []

                    for item in ads_data["items"]:
                        keyword_data = item.get("keyword_data", {})
                        keyword = keyword_data.get("keyword", "N/A")
                        keyword_info = keyword_data.get("keyword_info", {})

                        # Get SERP element data (for ad-specific info)
                        ranked_serp = item.get("ranked_serp_element", {})
                        serp_item = ranked_serp.get("serp_item", {})

                        # Extract metrics
                        search_volume = keyword_info.get("search_volume", 0)
                        cpc = keyword_info.get("cpc", 0.0)
                        competition = keyword_info.get("competition", 0.0)
                        competition_level = keyword_info.get("competition_level", "N/A")

                        # Ad position data
                        rank_absolute = serp_item.get("rank_absolute", 0)
                        rank_group = serp_item.get("rank_group", 0)

                        # Traffic estimates
                        etv = serp_item.get("etv", 0.0)
                        estimated_cost = serp_item.get("estimated_paid_traffic_cost", 0.0)

                        keywords_list.append({
                            "Keyword": keyword,
                            "Ad Position": rank_absolute,
                            "Group Position": rank_group,
                            "Search Volume": search_volume,
                            "CPC ($)": round(cpc, 2),
                            "Competition": round(competition, 2),
                            "Level": competition_level,
                            "Est. Traffic Value ($)": round(etv, 2),
                            "Est. Paid Cost ($)": round(estimated_cost, 2)
                        })

                    # Create DataFrame
                    df = pd.DataFrame(keywords_list)

                    # Display table with sorting
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Keyword": st.column_config.TextColumn("Keyword", width="large"),
                            "Ad Position": st.column_config.NumberColumn("Ad Position", format="%d"),
                            "Group Position": st.column_config.NumberColumn("Group Pos", format="%d"),
                            "Search Volume": st.column_config.NumberColumn("Search Vol", format="%d"),
                            "CPC ($)": st.column_config.NumberColumn("CPC ($)", format="$%.2f"),
                            "Competition": st.column_config.NumberColumn("Competition", format="%.2f"),
                            "Level": st.column_config.TextColumn("Level", width="small"),
                            "Est. Traffic Value ($)": st.column_config.NumberColumn("Traffic Value", format="$%.2f"),
                            "Est. Paid Cost ($)": st.column_config.NumberColumn("Paid Cost", format="$%.2f")
                        }
                    )

                    # Summary statistics
                    st.markdown("---")
                    st.markdown("### 📈 Campaign Statistics")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        total_search_vol = df["Search Volume"].sum()
                        st.metric("Total Search Volume", f"{total_search_vol:,}")
                    with col2:
                        avg_cpc = df["CPC ($)"].mean()
                        st.metric("Avg CPC", f"${avg_cpc:.2f}")
                    with col3:
                        total_etv = df["Est. Traffic Value ($)"].sum()
                        st.metric("Total Traffic Value", f"${total_etv:,.2f}")
                    with col4:
                        total_cost = df["Est. Paid Cost ($)"].sum()
                        st.metric("Total Paid Cost", f"${total_cost:,.2f}")

                    # Export functionality
                    st.markdown("---")
                    st.markdown("### 📥 Export Data")

                    csv = df.to_csv(index=False)

                    st.download_button(
                        label="📄 Download as CSV",
                        data=csv,
                        file_name=f"google_ads_{domain}_{location_name}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                    # Show raw data option
                    with st.expander("🔍 View Raw API Response"):
                        st.json(ads_data)

                else:
                    st.info(f"ℹ️ No paid keywords found for {domain} in {location_name}.")
                    st.markdown("This could mean:")
                    st.markdown("- The domain is not currently running Google Ads campaigns")
                    st.markdown("- Ads are running in different locations")
                    st.markdown("- The domain uses a different name for advertising")

            else:
                st.warning(f"⚠️ No Google Ads data found for {domain}.")

        elif result:
            st.error("❌ Failed to retrieve Google Ads data.")

    elif analyze_button and not domain_input:
        st.warning("⚠️ Please enter a domain to analyze.")
