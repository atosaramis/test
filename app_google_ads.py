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
import time


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def scrape_ad_content(transparency_url: str) -> Optional[Dict[str, Any]]:
    """
    Scrape Google Ads Transparency page using Firecrawl to extract ad content.

    Args:
        transparency_url: URL to Google Ads Transparency page

    Returns:
        dict: Extracted ad content (headline, description, images) or None if error
    """
    api_key = get_credential("FIRECRAWL_API_KEY")

    if not api_key:
        return None

    try:
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "url": transparency_url,
                "formats": ["markdown", "html"],
                "onlyMainContent": True
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "markdown": data.get("data", {}).get("markdown", ""),
                "html": data.get("data", {}).get("html", ""),
                "metadata": data.get("data", {}).get("metadata", {})
            }
        else:
            return None

    except Exception as e:
        return None


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
        firecrawl_key = get_credential("FIRECRAWL_API_KEY")

        if login and password:
            st.success(f"✅ DataForSEO: {login[:5]}...")
        else:
            st.error("❌ DataForSEO credentials missing")

        if firecrawl_key:
            st.success(f"✅ Firecrawl: {firecrawl_key[:8]}...")
        else:
            st.warning("⚠️ Firecrawl API key missing (ad content scraping disabled)")

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

                    # Check if Firecrawl is available for scraping
                    firecrawl_key = get_credential("FIRECRAWL_API_KEY")
                    can_scrape = bool(firecrawl_key)
                    scrape_limit = 15  # Auto-scrape up to 15 ads without preview images

                    # Prepare data for display and export
                    ads_list = []
                    scraped_count = 0
                    total_to_scrape = 0

                    # Count how many ads need scraping
                    if can_scrape:
                        for item in ads_data["items"]:
                            preview_image_obj = item.get("preview_image", {})
                            preview_image_url = preview_image_obj.get("url") if preview_image_obj else None
                            if not preview_image_url:
                                total_to_scrape += 1

                    # Show scraping status if needed
                    if can_scrape and total_to_scrape > 0:
                        ads_to_scrape = min(total_to_scrape, scrape_limit)
                        st.info(f"🔍 Scraping {ads_to_scrape} ads without preview images...")
                        scrape_progress = st.progress(0)
                        scrape_status = st.empty()

                    for idx, item in enumerate(ads_data["items"]):
                        advertiser_id = item.get("advertiser_id", "")
                        creative_id = item.get("creative_id", "")
                        title = item.get("title", "No title")
                        url = item.get("url", "")
                        verified = item.get("verified", False)
                        ad_format = item.get("format", "text")
                        first_shown = item.get("first_shown", "N/A")
                        last_shown = item.get("last_shown", "N/A")

                        # Extract preview image URL
                        preview_image_obj = item.get("preview_image", {})
                        preview_image_url = preview_image_obj.get("url") if preview_image_obj else None

                        # Auto-scrape if no preview image and Firecrawl is available
                        scraped_content = None
                        if not preview_image_url and can_scrape and scraped_count < scrape_limit and url:
                            scrape_status.text(f"Scraping ad {scraped_count + 1}...")
                            scraped_content = scrape_ad_content(url)
                            scraped_count += 1
                            if total_to_scrape > 0:
                                scrape_progress.progress(min(scraped_count / min(total_to_scrape, scrape_limit), 1.0))
                            time.sleep(0.5)  # Rate limiting

                        ads_list.append({
                            "Advertiser": title,
                            "Format": ad_format,
                            "First Shown": first_shown,
                            "Last Shown": last_shown,
                            "Verified": "✓" if verified else "",
                            "Advertiser ID": advertiser_id,
                            "Creative ID": creative_id,
                            "Transparency URL": url,
                            "Preview Image URL": preview_image_url or "",
                            "Has Preview": "Yes" if preview_image_url else "No",
                            "Scraped Content": "Yes" if scraped_content else "No"
                        })

                        # Display individual ad card
                        with st.container():
                            # Header with advertiser name and verification badge
                            col_header1, col_header2 = st.columns([4, 1])
                            with col_header1:
                                st.markdown(f"### {title}")
                                st.caption(f"Format: {ad_format} | Active: {first_shown[:10]} to {last_shown[:10]}")
                            with col_header2:
                                if verified:
                                    st.markdown("✅ **Verified**")

                            # Show ad content in priority order: preview image > scraped content > info message
                            if preview_image_url:
                                st.markdown("**🖼️ Ad Preview:**")
                                st.image(preview_image_url, use_column_width=True)
                            elif scraped_content:
                                st.markdown("**📄 Ad Content:**")
                                content_markdown = scraped_content.get("markdown", "")
                                if content_markdown:
                                    # Display in a nice box
                                    st.markdown(f"""
                                    <div style="padding: 1rem; background-color: #f0f2f6; border-radius: 8px; border-left: 4px solid #4CAF50;">
                                    {content_markdown}
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.caption("Content extraction in progress...")
                            else:
                                if can_scrape:
                                    st.caption("⏩ Skipped (exceeds scrape limit)")
                                else:
                                    st.warning("⚠️ Add FIRECRAWL_API_KEY to secrets.toml to extract ad content")

                            # Link to full details
                            if url:
                                st.markdown(f"[🔗 View full details on Google Ads Transparency]({url})")

                            st.markdown("---")

                    # Clear scraping status
                    if can_scrape and total_to_scrape > 0:
                        scrape_status.empty()
                        scrape_progress.empty()

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
