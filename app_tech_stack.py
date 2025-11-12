"""
Tech Stack Analyzer - Analyze website technologies using DataForSEO
Identifies technologies, frameworks, CMS, analytics tools, and more
"""

import streamlit as st
import os
import requests
import pandas as pd
from typing import Dict, Any, Optional
import base64


def get_credential(key: str, default=None):
    """Get credential from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get(key, os.environ.get(key, default))
    except (FileNotFoundError, KeyError):
        return os.environ.get(key, default)


def analyze_tech_stack(domain: str) -> Optional[Dict[str, Any]]:
    """
    Analyze website technologies using DataForSEO Domain Analytics API.

    Args:
        domain: Domain name (e.g., "example.com")

    Returns:
        dict: API response with technology data or None if error
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
    url = "https://api.dataforseo.com/v3/domain_analytics/technologies/domain_technologies/live"

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

    payload = [
        {
            "target": domain
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


def render_tech_stack_app():
    """Render the Tech Stack Analyzer interface."""

    st.markdown("## 🔧 Tech Stack Analyzer")
    st.caption("Discover what technologies power any website")

    # Check credentials in sidebar
    with st.sidebar:
        st.markdown("### Configuration")
        login = get_credential("DATAFORSEO_LOGIN")
        password = get_credential("DATAFORSEO_PASSWORD")

        if login and password:
            st.success(f"✅ DataForSEO: {login[:5]}...")
        else:
            st.error("❌ DataForSEO credentials missing")

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
    st.markdown("**Examples:** dataforseo.com, hubspot.com, shopify.com")

    # Process analysis
    if analyze_button and domain_input:
        # Clean domain input
        domain = domain_input.strip().lower()
        domain = domain.replace("http://", "").replace("https://", "").replace("www.", "")
        domain = domain.split("/")[0]  # Remove any path

        with st.spinner(f"🔍 Analyzing technology stack for {domain}..."):
            result = analyze_tech_stack(domain)

        # Debug section
        with st.expander("🐛 Debug Info - API Request"):
            st.write(f"**Original input:** `{domain_input}`")
            st.write(f"**Cleaned domain sent to API:** `{domain}`")

        if result and result.get("tasks"):
            task = result["tasks"][0]

            # Show full task response in debug
            with st.expander("🐛 Debug Info - Full API Response"):
                st.json(result)

            if task.get("result") and len(task["result"]) > 0:
                tech_data = task["result"][0]

                # Display summary
                st.markdown("---")
                st.markdown(f"### 📊 Results for **{tech_data.get('domain', domain)}**")

                # Extract technologies from nested structure
                technologies = tech_data.get("technologies", {})

                # Count total technologies
                total_count = 0
                tech_list = []
                tech_by_category = {}

                for main_category, subcategories in technologies.items():
                    if isinstance(subcategories, dict):
                        for subcategory, tech_array in subcategories.items():
                            if isinstance(tech_array, list):
                                total_count += len(tech_array)

                                # Format category name
                                category_display = main_category.replace("_", " ").title()
                                subcategory_display = subcategory.replace("_", " ").title()

                                # Add to flat list for export
                                for tech_name in tech_array:
                                    tech_list.append({
                                        "Technology": tech_name,
                                        "Category": category_display,
                                        "Subcategory": subcategory_display
                                    })

                                # Group for display
                                if category_display not in tech_by_category:
                                    tech_by_category[category_display] = {}
                                if subcategory_display not in tech_by_category[category_display]:
                                    tech_by_category[category_display][subcategory_display] = []
                                tech_by_category[category_display][subcategory_display].extend(tech_array)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Technologies", total_count)
                with col2:
                    st.metric("Domain Rank", tech_data.get("domain_rank", "N/A"))
                with col3:
                    cost = task.get("cost", 0)
                    st.metric("API Cost", f"${cost:.4f}")

                # Display additional info
                if tech_data.get("title"):
                    st.markdown(f"**Title:** {tech_data['title']}")
                if tech_data.get("description"):
                    with st.expander("📄 Site Description"):
                        st.write(tech_data['description'])

                # Contact information
                col1, col2 = st.columns(2)
                with col1:
                    if tech_data.get("emails"):
                        st.markdown("**📧 Emails:**")
                        for email in tech_data["emails"]:
                            st.write(f"- {email}")
                with col2:
                    if tech_data.get("phone_numbers"):
                        st.markdown("**📞 Phone Numbers:**")
                        for phone in tech_data["phone_numbers"]:
                            st.write(f"- {phone}")

                # Social media
                if tech_data.get("social_graph_urls"):
                    with st.expander("🔗 Social Media Links"):
                        for url in tech_data["social_graph_urls"]:
                            st.markdown(f"- {url}")

                # Display technologies
                if tech_by_category:
                    st.markdown("### 🛠️ Technologies Detected")

                    # Display by category
                    for category, subcategories in sorted(tech_by_category.items()):
                        with st.expander(f"**{category}**", expanded=True):
                            for subcategory, technologies in sorted(subcategories.items()):
                                st.markdown(f"**{subcategory}:**")
                                for tech_name in technologies:
                                    st.markdown(f"- {tech_name}")

                    # Export functionality
                    st.markdown("---")
                    st.markdown("### 📥 Export Data")

                    df = pd.DataFrame(tech_list)
                    csv = df.to_csv(index=False)

                    st.download_button(
                        label="📄 Download as CSV",
                        data=csv,
                        file_name=f"tech_stack_{domain}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                    # Show raw data option
                    with st.expander("🔍 View Raw API Response"):
                        st.json(tech_data)

                else:
                    st.info("ℹ️ No technologies detected for this domain.")

            else:
                st.info("ℹ️ No technology data returned for this domain.")
                st.markdown("This could mean:")
                st.markdown("- The domain is very new or has minimal web presence")
                st.markdown("- The site uses custom or proprietary technologies")
                st.markdown("- The domain redirects to a different URL")

        elif result:
            st.error("❌ Failed to retrieve technology data.")

    elif analyze_button and not domain_input:
        st.warning("⚠️ Please enter a domain to analyze.")
