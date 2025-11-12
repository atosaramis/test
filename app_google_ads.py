"""
Google Ads Intelligence - Discover competitor ad creatives
Analyzes Google Ads campaigns for any domain using DataForSEO SERP API
"""

import streamlit as st
import os
import requests
import pandas as pd
from typing import Dict, Any, Optional, List
import base64
import json


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def get_google_ads_data(domain: str, location_code: int = 2840, limit: int = 100) -> Optional[Dict[str, Any]]:
    """
    Get Google Ads creatives for a domain using DataForSEO SERP API.

    Args:
        domain: Domain name (e.g., "example.com")
        location_code: Location code (default: 2840 for United States)
        limit: Number of results to return (default: 100, max: 120)

    Returns:
        dict: API response with Google Ads creatives or None if error
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

    # API endpoint - SERP API Google Ads Search
    url = "https://api.dataforseo.com/v3/serp/google/ads_search/live/advanced"

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

    payload = [
        {
            "target": domain,
            "location_code": location_code,
            "language_code": "en",
            "depth": min(limit, 120),  # Max depth is 120
            "platform": "all",
            "format": "all"
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
    st.caption("Discover competitor ad creatives and campaigns running on Google Ads")

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

        if result and result.get("tasks"):
            task = result["tasks"][0]

            if task.get("result") and len(task["result"]) > 0:
                ads_data = task["result"][0]

                # Display summary
                st.markdown("---")
                st.markdown(f"## 📊 {ads_data.get('target', domain)}")

                # Metrics
                items = ads_data.get("items", [])
                items_count = len(items)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Ads Found", items_count)
                with col2:
                    st.metric("Location", location_name)
                with col3:
                    cost = task.get("cost", 0)
                    st.metric("API Cost", f"${cost:.4f}")

                st.markdown("")  # spacing

                # Display ads
                if ads_data.get("items"):
                    st.markdown("### 📢 Google Ads Creatives")

                    # TEMPORARY DEBUG - show first item structure
                    if len(ads_data["items"]) > 0:
                        st.info("🐛 DEBUG: First Ad Item Structure")
                        st.json(ads_data["items"][0])

                    # Prepare data for display and export
                    ads_list = []

                    for item in ads_data["items"]:
                        advertiser_id = item.get("advertiser_id", "")
                        creative_id = item.get("creative_id", "")
                        title = item.get("title", "No title")
                        url = item.get("url", "")
                        verified = item.get("verified", False)
                        ad_format = item.get("format", "text")
                        preview_image_obj = item.get("preview_image", None)
                        first_shown = item.get("first_shown", "N/A")
                        last_shown = item.get("last_shown", "N/A")

                        # Extract preview image URL if available
                        preview_image_url = None
                        if preview_image_obj and isinstance(preview_image_obj, dict):
                            preview_image_url = preview_image_obj.get("url")

                        ads_list.append({
                            "Title": title,
                            "Format": ad_format,
                            "URL": url,
                            "Verified": "✓" if verified else "",
                            "First Shown": first_shown,
                            "Last Shown": last_shown,
                            "Advertiser ID": advertiser_id,
                            "Creative ID": creative_id,
                            "Preview Image URL": preview_image_url or ""
                        })

                        # Display individual ad card
                        with st.container():
                            col_header1, col_header2 = st.columns([3, 1])
                            with col_header1:
                                st.markdown(f"### {title}")
                            with col_header2:
                                if verified:
                                    st.markdown("✅ **Verified**")

                            # Preview image (if available)
                            if preview_image_url:
                                st.image(preview_image_url, use_column_width=True)

                            # Ad details
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(f"**Format:** {ad_format}")
                                st.markdown(f"**First shown:** {first_shown}")
                            with col_b:
                                st.markdown(f"**Last shown:** {last_shown}")
                                if url:
                                    st.markdown(f"[View on Ads Transparency]({url})")

                            st.markdown("---")

                    # Export functionality
                    st.markdown("### 📥 Export Data")

                    col1, col2 = st.columns(2)

                    with col1:
                        df = pd.DataFrame(ads_list)
                        csv = df.to_csv(index=False)

                        st.download_button(
                            label="📄 Download CSV",
                            data=csv,
                            file_name=f"google_ads_{domain}_{location_name}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    with col2:
                        json_data = json.dumps(ads_data, indent=2)

                        st.download_button(
                            label="📦 Download JSON",
                            data=json_data,
                            file_name=f"google_ads_{domain}_{location_name}.json",
                            mime="application/json",
                            use_container_width=True
                        )

                else:
                    st.info(f"ℹ️ No Google Ads found for {domain} in {location_name}.")
                    st.markdown("This could mean:")
                    st.markdown("- The domain is not currently running Google Ads campaigns")
                    st.markdown("- Ads are running in different locations")
                    st.markdown("- The domain uses a different name for advertising")
                    st.markdown("- DataForSEO has not indexed ads for this domain yet")

            else:
                st.warning(f"⚠️ No Google Ads data found for {domain}.")

        elif result:
            st.error("❌ Failed to retrieve Google Ads data.")

    elif analyze_button and not domain_input:
        st.warning("⚠️ Please enter a domain to analyze.")
