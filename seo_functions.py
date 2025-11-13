"""
SEO Tools Functions

Simple Python functions that run directly on Streamlit Cloud.
No cloud infrastructure needed - just API calls.
"""

import requests
import os
import json
from typing import Dict, List
from supabase import create_client, Client


def get_credential(key: str, default=None):
    """
    Get credential from Streamlit secrets or environment variables.
    Tries st.secrets first, falls back to os.environ.

    Args:
        key: The credential key name
        default: Default value if not found

    Returns:
        The credential value or default
    """
    try:
        import streamlit as st
        return st.secrets.get(key, os.environ.get(key, default))
    except (ImportError, FileNotFoundError):
        # Streamlit not available or secrets file not found, use environment
        return os.environ.get(key, default)


def get_keyword_data(keyword: str) -> Dict:
    """
    Fetch keyword research data from DataForSEO API.

    Args:
        keyword: The keyword to research

    Returns:
        Dictionary with keyword metrics
    """
    dataforseo_login = get_credential("DATAFORSEO_LOGIN")
    dataforseo_password = get_credential("DATAFORSEO_PASSWORD")

    if not dataforseo_login or not dataforseo_password:
        return {"error": "DataForSEO credentials not configured"}

    api_url = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"

    payload = [{
        "keywords": [keyword],
        "language_code": "en",
        "location_code": 2840  # United States
    }]

    try:
        response = requests.post(
            api_url,
            json=payload,
            auth=(dataforseo_login, dataforseo_password),
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        if data.get("tasks") and data["tasks"][0].get("result") and len(data["tasks"][0]["result"]) > 0:
            result = data["tasks"][0]["result"][0]

            # Return full result plus raw response
            return {
                "result": result,
                "raw_response": data,
                "error": None
            }
        else:
            return {"error": f"No data found for '{keyword}'"}

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}


def fetch_linkedin_posts(linkedin_url: str) -> Dict:
    """
    Fetch LinkedIn company posts from RapidAPI.

    Args:
        linkedin_url: LinkedIn company URL

    Returns:
        Dictionary with posts data
    """
    rapidapi_key = get_credential("RAPIDAPI_KEY")

    if not rapidapi_key:
        return {"error": "RapidAPI key not configured"}

    api_url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-company-posts"

    params = {
        "linkedin_url": linkedin_url,
        "start": "0",
        "sort_by": "recent"
    }

    try:
        response = requests.get(
            api_url,
            params=params,
            headers={
                "x-rapidapi-key": rapidapi_key,
                "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com"
            },
            timeout=120  # 2 minute timeout for slow API responses
        )

        response.raise_for_status()
        data = response.json()

        if data.get("data") and len(data["data"]) > 0:
            # Return raw response
            return {
                "data": data,
                "raw_response": data,
                "error": None
            }
        else:
            return {"error": f"No posts found for {linkedin_url}"}

    except requests.exceptions.Timeout:
        return {"error": f"API timeout after 120 seconds. The LinkedIn API is very slow - try again later or try a different company."}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}


def get_keyword_suggestions(seed_keyword: str, limit: int = 100) -> Dict:
    """
    Get related keyword suggestions from DataForSEO.

    Args:
        seed_keyword: Seed keyword to get suggestions for
        limit: Maximum number of suggestions (default: 100)

    Returns:
        Dictionary with keyword suggestions and metrics
    """
    dataforseo_login = get_credential("DATAFORSEO_LOGIN")
    dataforseo_password = get_credential("DATAFORSEO_PASSWORD")

    if not dataforseo_login or not dataforseo_password:
        return {"error": "DataForSEO credentials not configured"}

    api_url = "https://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live"

    payload = [{
        "keywords": [seed_keyword],
        "language_code": "en",
        "location_code": 2840,  # United States
        "limit": limit
    }]

    try:
        response = requests.post(
            api_url,
            json=payload,
            auth=(dataforseo_login, dataforseo_password),
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        if data.get("tasks") and data["tasks"][0].get("result") and len(data["tasks"][0]["result"]) > 0:
            results = data["tasks"][0]["result"]

            return {
                "keywords": results,
                "count": len(results),
                "raw_response": data,
                "error": None
            }
        else:
            return {"error": f"No suggestions found for '{seed_keyword}'"}

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}


def get_keywords_for_site(url: str, limit: int = 100) -> Dict:
    """
    Get keywords for a competitor website from DataForSEO.

    Args:
        url: Competitor website URL
        limit: Maximum number of keywords (default: 100)

    Returns:
        Dictionary with keywords from the site
    """
    dataforseo_login = get_credential("DATAFORSEO_LOGIN")
    dataforseo_password = get_credential("DATAFORSEO_PASSWORD")

    if not dataforseo_login or not dataforseo_password:
        return {"error": "DataForSEO credentials not configured"}

    api_url = "https://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live"

    payload = [{
        "target": url,
        "language_code": "en",
        "location_code": 2840,  # United States
        "limit": limit
    }]

    try:
        response = requests.post(
            api_url,
            json=payload,
            auth=(dataforseo_login, dataforseo_password),
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        if data.get("tasks") and data["tasks"][0].get("result") and len(data["tasks"][0]["result"]) > 0:
            results = data["tasks"][0]["result"]

            return {
                "keywords": results,
                "count": len(results),
                "url": url,
                "raw_response": data,
                "error": None
            }
        else:
            return {"error": f"No keywords found for '{url}'"}

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}


def get_ranked_keywords_for_domain(
    domain: str,
    limit: int = 500,
    include_paid: bool = False,
    max_position: int = None
) -> Dict:
    """
    Get ranked keywords for a domain from DataForSEO Labs API.
    Shows what keywords the domain ranks for in Google search results.

    Args:
        domain: Domain to analyze (e.g., "example.com")
        limit: Maximum number of keywords (default: 500, max: 1000)
        include_paid: Include paid keywords in addition to organic (default: False)
        max_position: Optional filter for maximum ranking position (e.g., 20 for top 20)

    Returns:
        Dictionary with ranked keywords and metrics
    """
    dataforseo_login = get_credential("DATAFORSEO_LOGIN")
    dataforseo_password = get_credential("DATAFORSEO_PASSWORD")

    if not dataforseo_login or not dataforseo_password:
        return {"error": "DataForSEO credentials not configured"}

    api_url = "https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live"

    # Build payload
    payload = [{
        "target": domain,
        "location_code": 2840,  # United States
        "language_code": "en",
        "limit": min(limit, 1000),  # Cap at 1000
        "load_rank_absolute": True,
        "order_by": ["ranked_serp_element.serp_item.rank_absolute,asc"]  # Sort by position
    }]

    # Add item_types filter
    if include_paid:
        payload[0]["item_types"] = ["organic", "paid"]
    else:
        payload[0]["item_types"] = ["organic"]

    # Add position filter if specified
    if max_position:
        payload[0]["filters"] = [
            ["ranked_serp_element.serp_item.rank_absolute", "<=", max_position]
        ]

    try:
        response = requests.post(
            api_url,
            json=payload,
            auth=(dataforseo_login, dataforseo_password),
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for larger datasets
        )

        response.raise_for_status()
        data = response.json()

        if data.get("tasks") and data["tasks"][0].get("result") and len(data["tasks"][0]["result"]) > 0:
            result = data["tasks"][0]["result"][0]
            items = result.get("items", [])

            # Parse and structure the keywords
            keywords = []
            for item in items:
                keyword_data = item.get("keyword_data", {})
                keyword_info = keyword_data.get("keyword_info", {})
                serp_item = item.get("ranked_serp_element", {}).get("serp_item", {})

                keyword = {
                    "keyword": keyword_data.get("keyword", ""),
                    "position": serp_item.get("rank_absolute", 0),
                    "search_volume": keyword_info.get("search_volume", 0),
                    "cpc": keyword_info.get("cpc", 0.0),
                    "competition": keyword_info.get("competition", 0.0),
                    "competition_level": keyword_info.get("competition_level", "UNKNOWN"),
                    "type": serp_item.get("type", "organic"),  # organic or paid
                    "url": serp_item.get("url", ""),
                    "etv": serp_item.get("etv", 0.0),  # Estimated Traffic Volume
                    "traffic_cost": serp_item.get("traffic_cost", 0.0)  # Est. cost of traffic
                }
                keywords.append(keyword)

            # Calculate summary metrics
            total_keywords = len(keywords)
            avg_position = sum(k["position"] for k in keywords) / total_keywords if total_keywords > 0 else 0
            top_3_count = sum(1 for k in keywords if k["position"] <= 3)
            total_search_volume = sum(k["search_volume"] for k in keywords)
            total_traffic_cost = sum(k["traffic_cost"] for k in keywords)

            return {
                "domain": domain,
                "keywords": keywords,
                "count": total_keywords,
                "summary": {
                    "total_keywords": total_keywords,
                    "avg_position": round(avg_position, 1),
                    "top_3_count": top_3_count,
                    "total_search_volume": total_search_volume,
                    "estimated_monthly_traffic_value": round(total_traffic_cost, 2)
                },
                "raw_response": data,
                "error": None
            }
        else:
            return {"error": f"No ranked keywords found for '{domain}'"}

    except requests.exceptions.Timeout:
        return {"error": f"API timeout. Try reducing the limit or try again later."}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}


def query_llm_about_company(
    company_name: str,
    domain: str = None,
    llm_provider: str = "chatgpt",
    custom_prompt: str = None
) -> Dict:
    """
    Query LLM (ChatGPT, Claude, Gemini, or Perplexity) about a company
    using DataForSEO AI Optimization API.

    Args:
        company_name: Name of the company
        domain: Optional company website domain
        llm_provider: "chatgpt", "claude", "gemini", or "perplexity" (default: chatgpt)
        custom_prompt: Optional custom question (if None, uses default prompts)

    Returns:
        Dictionary with LLM responses
    """
    dataforseo_login = get_credential("DATAFORSEO_LOGIN")
    dataforseo_password = get_credential("DATAFORSEO_PASSWORD")

    if not dataforseo_login or not dataforseo_password:
        return {"error": "DataForSEO credentials not configured"}

    # Map provider to endpoint
    endpoints = {
        "chatgpt": "https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live",
        "claude": "https://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/live",
        "gemini": "https://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/live",
        "perplexity": "https://api.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/live"
    }

    # Map provider to model
    models = {
        "chatgpt": "gpt-4o-mini",  # Cost-effective
        "claude": "claude-sonnet-4-0",
        "gemini": "gemini-2.0-flash-exp",
        "perplexity": "sonar-pro"
    }

    if llm_provider not in endpoints:
        return {"error": f"Invalid LLM provider: {llm_provider}. Choose: chatgpt, claude, gemini, or perplexity"}

    api_url = endpoints[llm_provider]
    model_name = models[llm_provider]

    # Define default prompts
    domain_text = f" (website: {domain})" if domain else ""
    default_prompts = [
        f"What do you know about {company_name}{domain_text}?",
        f"What is {company_name}'s main value proposition and target market?",
        f"What industry is {company_name} in and who are their main competitors?"
    ]

    # Use custom prompt or defaults
    prompts_to_run = [custom_prompt] if custom_prompt else default_prompts

    responses = []

    for prompt in prompts_to_run:
        payload = [{
            "user_prompt": prompt,
            "model_name": model_name,
            "max_output_tokens": 500,
            "temperature": 0.7
        }]

        try:
            response = requests.post(
                api_url,
                json=payload,
                auth=(dataforseo_login, dataforseo_password),
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            if data.get("tasks") and data["tasks"][0].get("result") and len(data["tasks"][0]["result"]) > 0:
                result = data["tasks"][0]["result"][0]
                message_data = result.get("new_message_data", {})

                responses.append({
                    "prompt": prompt,
                    "response": message_data.get("message", ""),
                    "tokens_used": result.get("output_tokens", 0),
                    "model": result.get("model_name", model_name)
                })
            else:
                responses.append({
                    "prompt": prompt,
                    "response": "",
                    "error": "No response from LLM",
                    "tokens_used": 0
                })

        except requests.exceptions.RequestException as e:
            responses.append({
                "prompt": prompt,
                "response": "",
                "error": f"API request failed: {str(e)}",
                "tokens_used": 0
            })
        except Exception as e:
            responses.append({
                "prompt": prompt,
                "response": "",
                "error": f"Error: {str(e)}",
                "tokens_used": 0
            })

    return {
        "provider": llm_provider,
        "company_name": company_name,
        "domain": domain,
        "responses": responses,
        "total_tokens": sum(r.get("tokens_used", 0) for r in responses),
        "error": None if any(r.get("response") for r in responses) else "All queries failed"
    }


# Helper functions for keyword analysis

def calculate_opportunity_score(keyword_data: Dict) -> float:
    """
    Calculate opportunity score for a keyword.
    Higher score = better opportunity

    Score = (search_volume * growth_factor) / (competition_index * 10)
    """
    volume = keyword_data.get("search_volume", 0) or 0
    competition = keyword_data.get("competition")

    # Handle None or invalid competition values
    if competition is None or competition == 0:
        competition = 0.5  # Default medium competition

    # Ensure numeric types
    try:
        volume = float(volume)
        competition = float(competition)
    except (TypeError, ValueError):
        return 0.0

    # Calculate growth from monthly searches
    monthly = keyword_data.get("monthly_searches", [])
    if len(monthly) >= 2:
        recent = monthly[0].get("search_volume", 0) or 0
        old = monthly[-1].get("search_volume", 1) or 1
        try:
            growth_factor = float(recent) / float(old) if old > 0 else 1.0
        except (TypeError, ValueError, ZeroDivisionError):
            growth_factor = 1.0
    else:
        growth_factor = 1.0

    try:
        score = (volume * growth_factor) / (competition * 100)
        return round(min(score, 10.0), 1)  # Cap at 10.0
    except (TypeError, ZeroDivisionError):
        return 0.0


def detect_seasonality(keyword_data: Dict) -> Dict:
    """
    Detect seasonal patterns in keyword data.

    Returns:
        Dict with peak_months, low_months, is_seasonal
    """
    monthly = keyword_data.get("monthly_searches", [])

    if not monthly or len(monthly) < 12:
        return {"is_seasonal": False, "peak_months": [], "low_months": []}

    # Find average - filter out None values
    volumes = [m.get("search_volume", 0) or 0 for m in monthly]
    volumes = [v for v in volumes if isinstance(v, (int, float))]

    if not volumes:
        return {"is_seasonal": False, "peak_months": [], "low_months": []}

    avg = sum(volumes) / len(volumes)

    if avg == 0:
        return {"is_seasonal": False, "peak_months": [], "low_months": []}

    # Find peaks (>25% above average)
    peak_months = []
    low_months = []

    for m in monthly:
        vol = m.get("search_volume", 0) or 0
        month = m.get("month")

        if not isinstance(vol, (int, float)) or not month:
            continue

        try:
            if vol > avg * 1.25:
                month_name = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][month - 1]
                peak_months.append(month_name)
            elif vol < avg * 0.75:
                month_name = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][month - 1]
                low_months.append(month_name)
        except (IndexError, TypeError):
            continue

    is_seasonal = len(peak_months) > 0 or len(low_months) > 0

    return {
        "is_seasonal": is_seasonal,
        "peak_months": peak_months,
        "low_months": low_months
    }


def calculate_growth_rate(keyword_data: Dict) -> float:
    """
    Calculate growth rate from monthly searches.
    Returns percentage change (e.g., 15.5 for +15.5%)
    """
    monthly = keyword_data.get("monthly_searches", [])

    if not monthly or len(monthly) < 2:
        return 0.0

    recent = monthly[0].get("search_volume", 0) or 0
    old = monthly[-1].get("search_volume", 0) or 0

    try:
        recent = float(recent)
        old = float(old)
    except (TypeError, ValueError):
        return 0.0

    if old == 0:
        return 0.0

    try:
        growth = ((recent - old) / old) * 100
        return round(growth, 1)
    except (TypeError, ZeroDivisionError):
        return 0.0


def generate_recommendation(keyword_data: Dict) -> str:
    """
    Generate actionable recommendation for a keyword.
    """
    score = calculate_opportunity_score(keyword_data)
    growth = calculate_growth_rate(keyword_data)
    seasonality = detect_seasonality(keyword_data)
    competition = keyword_data.get("competition_level", "UNKNOWN")

    if score >= 7.0:
        rec = "✅ Excellent opportunity! "
    elif score >= 4.0:
        rec = "⚠️ Good opportunity with caveats. "
    else:
        rec = "❌ Difficult keyword. "

    if growth > 10:
        rec += f"Growing fast (+{growth}%). "
    elif growth < -10:
        rec += f"Declining ({growth}%). "

    if seasonality["is_seasonal"] and seasonality["peak_months"]:
        peaks = ", ".join(seasonality["peak_months"][:3])
        rec += f"Peaks in {peaks}. "

    if competition == "HIGH":
        rec += "High competition - consider long-tail variations."
    elif competition == "LOW":
        rec += "Low competition - great for quick wins!"

    return rec


# Database functions

def get_supabase_client() -> Client:
    """Get Supabase client."""
    url = get_credential("SUPABASE_URL")
    key = get_credential("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")

    return create_client(url, key)


def save_keywords_to_db(keywords_data: List[Dict]) -> bool:
    """
    Save keywords data to Supabase.

    Args:
        keywords_data: List of keyword dictionaries

    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()

        # Prepare data for bulk insert
        data_to_insert = []
        for kw in keywords_data:
            data_to_insert.append({
                'keyword': kw.get('keyword'),
                'search_volume': kw.get('search_volume'),
                'cpc': kw.get('cpc'),
                'competition_level': kw.get('competition_level'),
                'opportunity_score': kw.get('opportunity_score'),
                'growth_rate': kw.get('growth_rate'),
                'is_seasonal': kw.get('is_seasonal'),
                'peak_months': kw.get('peak_months'),
                'recommendation': kw.get('recommendation'),
                'monthly_searches': json.dumps(kw.get('monthly_searches', []))
            })

        # Bulk insert
        response = supabase.table('keywords').insert(data_to_insert).execute()
        return True

    except Exception as e:
        print(f"Error saving keywords to Supabase: {e}")
        return False


def save_linkedin_posts_to_db(url: str, posts_data: Dict) -> bool:
    """
    Save LinkedIn posts data to Supabase.

    Args:
        url: LinkedIn URL
        posts_data: Posts data dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()

        data_to_insert = {
            'url': url,
            'post_data': json.dumps(posts_data)
        }

        response = supabase.table('linkedin_posts').insert(data_to_insert).execute()
        return True

    except Exception as e:
        print(f"Error saving LinkedIn posts to Supabase: {e}")
        return False


def get_all_keywords_from_db(limit: int = 1000) -> List[Dict]:
    """
    Retrieve keywords from Supabase.

    Args:
        limit: Maximum number of records to return

    Returns:
        List of keyword dictionaries
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table('keywords').select('*').order('created_at', desc=True).limit(limit).execute()

        keywords = []
        for item in response.data:
            kw = {
                'keyword': item.get('keyword'),
                'search_volume': item.get('search_volume'),
                'cpc': item.get('cpc'),
                'competition_level': item.get('competition_level'),
                'opportunity_score': item.get('opportunity_score'),
                'growth_rate': item.get('growth_rate'),
                'is_seasonal': item.get('is_seasonal'),
                'peak_months': item.get('peak_months'),
                'recommendation': item.get('recommendation'),
                'monthly_searches': json.loads(item.get('monthly_searches', '[]')),
                'created_at': item.get('created_at')
            }
            keywords.append(kw)

        return keywords

    except Exception as e:
        print(f"Error retrieving keywords from Supabase: {e}")
        return []


def get_all_linkedin_posts_from_db(limit: int = 100) -> List[Dict]:
    """
    Retrieve LinkedIn posts from Supabase.

    Args:
        limit: Maximum number of records to return

    Returns:
        List of post dictionaries
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table('linkedin_posts').select('*').order('created_at', desc=True).limit(limit).execute()

        posts = []
        for item in response.data:
            post = {
                'url': item.get('url'),
                'post_data': json.loads(item.get('post_data', '{}')),
                'created_at': item.get('created_at')
            }
            posts.append(post)

        return posts

    except Exception as e:
        print(f"Error retrieving LinkedIn posts from Supabase: {e}")
        return []


def save_company_analysis(analysis_dict: Dict) -> bool:
    """
    Save company-level LinkedIn analysis to Supabase.

    Args:
        analysis_dict: Complete analysis dict from analyze_company_complete()
                      For Company Research tool: linkedin_company_url, website_url, grok_research, claude_research
                      For Company Intelligence tool: company_url, company_name, voice_profile, etc.

    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()

        data = {}

        # Add fields based on what's provided in analysis_dict
        if 'company_url' in analysis_dict:
            data['company_url'] = analysis_dict.get('company_url')
        if 'company_name' in analysis_dict:
            data['company_name'] = analysis_dict.get('company_name')
        if 'voice_profile' in analysis_dict:
            data['voice_profile'] = json.dumps(analysis_dict.get('voice_profile', {}))
        if 'content_pillars' in analysis_dict:
            data['content_pillars'] = json.dumps(analysis_dict.get('content_pillars', {}))
        if 'engagement_metrics' in analysis_dict:
            data['engagement_metrics'] = json.dumps(analysis_dict.get('engagement_metrics', {}))
        if 'top_posts' in analysis_dict:
            data['top_posts'] = json.dumps(analysis_dict.get('top_posts', []))
        if 'posts_analyzed' in analysis_dict:
            data['posts_analyzed'] = analysis_dict.get('posts_analyzed')
        if 'date_range' in analysis_dict:
            data['date_range'] = analysis_dict.get('date_range')
        if 'analysis_model' in analysis_dict:
            data['analysis_model'] = analysis_dict.get('analysis_model')

        # Add new fields if present
        if 'ranked_keywords' in analysis_dict:
            data['ranked_keywords'] = json.dumps(analysis_dict.get('ranked_keywords'))
        if 'ranked_keywords_domain' in analysis_dict:
            data['ranked_keywords_domain'] = analysis_dict.get('ranked_keywords_domain')
        if 'ai_perception' in analysis_dict:
            data['ai_perception'] = json.dumps(analysis_dict.get('ai_perception'))

        # Add comprehensive research fields (Company Research tool)
        if 'linkedin_company_url' in analysis_dict:
            data['linkedin_company_url'] = analysis_dict.get('linkedin_company_url')
        if 'website_url' in analysis_dict:
            data['website_url'] = analysis_dict.get('website_url')
        if 'grok_research' in analysis_dict:
            data['grok_research'] = json.dumps(analysis_dict.get('grok_research'))
        if 'claude_research' in analysis_dict:
            data['claude_research'] = json.dumps(analysis_dict.get('claude_research'))
        if 'competitor_of' in analysis_dict:
            data['competitor_of'] = analysis_dict.get('competitor_of')
        if 'research_type' in analysis_dict:
            data['research_type'] = analysis_dict.get('research_type')

        # Determine unique key - use linkedin_company_url if provided, otherwise company_url
        if 'linkedin_company_url' in analysis_dict and analysis_dict.get('linkedin_company_url'):
            # Company Research tool - upsert by linkedin_company_url
            response = supabase.table('linkedin_company_analysis')\
                .upsert(data, on_conflict='linkedin_company_url')\
                .execute()
        elif 'company_url' in analysis_dict and analysis_dict.get('company_url'):
            # Company Intelligence tool - upsert by company_url
            response = supabase.table('linkedin_company_analysis')\
                .upsert(data, on_conflict='company_url')\
                .execute()
        else:
            # No unique key provided, do regular insert
            response = supabase.table('linkedin_company_analysis').insert(data).execute()

        return True

    except Exception as e:
        print(f"Error saving company analysis to Supabase: {e}")
        return False


def update_company_ranked_keywords(
    company_url: str,
    ranked_keywords_data: Dict,
    domain: str
) -> bool:
    """
    Update ranked keywords data for an existing company analysis.

    Args:
        company_url: LinkedIn company URL
        ranked_keywords_data: Keywords data from get_ranked_keywords_for_domain()
        domain: Website domain analyzed

    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()

        from datetime import datetime

        data = {
            'company_url': company_url,
            'ranked_keywords': json.dumps(ranked_keywords_data),
            'ranked_keywords_domain': domain,
            'ranked_keywords_fetched_at': datetime.utcnow().isoformat()
        }

        # Use upsert (will update if exists, insert if not)
        response = supabase.table('linkedin_company_analysis').upsert(data).execute()
        return True

    except Exception as e:
        print(f"Error updating ranked keywords in Supabase: {e}")
        return False


def update_company_ai_perception(
    company_url: str,
    ai_perception_data: Dict
) -> bool:
    """
    Update AI perception data for an existing company analysis.

    Args:
        company_url: LinkedIn company URL
        ai_perception_data: AI responses from query_llm_about_company()

    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()

        data = {
            'company_url': company_url,
            'ai_perception': json.dumps(ai_perception_data)
        }

        # Use upsert (will update if exists, insert if not)
        response = supabase.table('linkedin_company_analysis').upsert(data).execute()
        return True

    except Exception as e:
        print(f"Error updating AI perception in Supabase: {e}")
        return False


def get_company_analysis(company_url: str = None, linkedin_company_url: str = None) -> Dict:
    """
    Retrieve company analysis by URL from Supabase.

    Args:
        company_url: Company URL (for Company Intelligence tool)
        linkedin_company_url: LinkedIn company URL (for Company Research tool)

    Returns:
        Dict with company analysis, or empty dict if not found
    """
    try:
        supabase = get_supabase_client()

        # Query by linkedin_company_url if provided, otherwise by company_url
        if linkedin_company_url:
            response = supabase.table('linkedin_company_analysis')\
                .select('*')\
                .eq('linkedin_company_url', linkedin_company_url)\
                .execute()
        elif company_url:
            response = supabase.table('linkedin_company_analysis')\
                .select('*')\
                .eq('company_url', company_url)\
                .execute()
        else:
            return {}

        if not response.data or len(response.data) == 0:
            return {}

        item = response.data[0]

        result = {
            'id': item.get('id'),
            'company_url': item.get('company_url'),
            'linkedin_company_url': item.get('linkedin_company_url'),
            'website_url': item.get('website_url'),
            'company_name': item.get('company_name'),
            'voice_profile': json.loads(item.get('voice_profile', '{}')) if item.get('voice_profile') else {},
            'content_pillars': json.loads(item.get('content_pillars', '{}')) if item.get('content_pillars') else {},
            'engagement_metrics': json.loads(item.get('engagement_metrics', '{}')) if item.get('engagement_metrics') else {},
            'posting_strategy': json.loads(item.get('posting_strategy', '{}')) if item.get('posting_strategy') else {},
            'top_posts': json.loads(item.get('top_posts', '[]')) if item.get('top_posts') else [],
            'strategic_recommendations': json.loads(item.get('strategic_recommendations', '{}')) if item.get('strategic_recommendations') else {},
            'posts_analyzed': item.get('posts_analyzed'),
            'date_range': item.get('date_range'),
            'analysis_model': item.get('analysis_model'),
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at')
        }

        # Add new fields if present
        if item.get('ranked_keywords'):
            result['ranked_keywords'] = json.loads(item.get('ranked_keywords'))
        if item.get('ranked_keywords_domain'):
            result['ranked_keywords_domain'] = item.get('ranked_keywords_domain')
        if item.get('ranked_keywords_fetched_at'):
            result['ranked_keywords_fetched_at'] = item.get('ranked_keywords_fetched_at')
        if item.get('ai_perception'):
            result['ai_perception'] = json.loads(item.get('ai_perception'))

        # Add comprehensive research fields
        if item.get('grok_research'):
            result['grok_research'] = json.loads(item.get('grok_research'))
        if item.get('claude_research'):
            result['claude_research'] = json.loads(item.get('claude_research'))
        if item.get('competitor_of'):
            result['competitor_of'] = item.get('competitor_of')
        if item.get('research_type'):
            result['research_type'] = item.get('research_type')

        return result

    except Exception as e:
        print(f"Error retrieving company analysis from Supabase: {e}")
        return {}


def get_company_competitors(main_company_url: str) -> List[Dict]:
    """
    Retrieve all competitor analyses for a given company from Supabase.

    Args:
        main_company_url: LinkedIn URL of the main company

    Returns:
        List of competitor analysis dicts, or empty list if none found
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table('linkedin_company_analysis')\
            .select('*')\
            .eq('competitor_of', main_company_url)\
            .eq('research_type', 'competitor')\
            .execute()

        if not response.data:
            return []

        competitors = []
        for item in response.data:
            result = {
                'id': item.get('id'),
                'company_url': item.get('company_url'),
                'linkedin_company_url': item.get('linkedin_company_url'),
                'website_url': item.get('website_url'),
                'company_name': item.get('company_name'),
                'voice_profile': json.loads(item.get('voice_profile', '{}')) if item.get('voice_profile') else {},
                'content_pillars': json.loads(item.get('content_pillars', '{}')) if item.get('content_pillars') else {},
                'engagement_metrics': json.loads(item.get('engagement_metrics', '{}')) if item.get('engagement_metrics') else {},
                'top_posts': json.loads(item.get('top_posts', '[]')) if item.get('top_posts') else [],
                'posts_analyzed': item.get('posts_analyzed'),
                'date_range': item.get('date_range'),
                'analysis_model': item.get('analysis_model'),
                'competitor_of': item.get('competitor_of'),
                'research_type': item.get('research_type'),
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at')
            }
            competitors.append(result)

        return competitors

    except Exception as e:
        print(f"Error retrieving competitors from Supabase: {e}")
        return []


def get_all_company_analyses(limit: int = 50) -> List[Dict]:
    """
    Retrieve all company analyses from Supabase for comparison.

    Args:
        limit: Maximum number of companies to return

    Returns:
        List of company analysis dictionaries
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table('linkedin_company_analysis')\
            .select('*')\
            .order('updated_at', desc=True)\
            .limit(limit)\
            .execute()

        companies = []
        for item in response.data:
            company = {
                'id': item.get('id'),
                'company_url': item.get('company_url'),
                'company_name': item.get('company_name'),
                'voice_profile': json.loads(item.get('voice_profile', '{}')),
                'content_pillars': json.loads(item.get('content_pillars', '{}')),
                'engagement_metrics': json.loads(item.get('engagement_metrics', '{}')),
                'posting_strategy': json.loads(item.get('posting_strategy', '{}')),
                'top_posts': json.loads(item.get('top_posts', '[]')),
                'strategic_recommendations': json.loads(item.get('strategic_recommendations', '{}')),
                'posts_analyzed': item.get('posts_analyzed'),
                'date_range': item.get('date_range'),
                'analysis_model': item.get('analysis_model'),
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at')
            }

            # Add new fields if present
            if item.get('ranked_keywords'):
                company['ranked_keywords'] = json.loads(item.get('ranked_keywords'))
            if item.get('ranked_keywords_domain'):
                company['ranked_keywords_domain'] = item.get('ranked_keywords_domain')
            if item.get('ranked_keywords_fetched_at'):
                company['ranked_keywords_fetched_at'] = item.get('ranked_keywords_fetched_at')
            if item.get('ai_perception'):
                company['ai_perception'] = json.loads(item.get('ai_perception'))

            companies.append(company)

        return companies

    except Exception as e:
        print(f"Error retrieving company analyses from Supabase: {e}")
        return []


def delete_company_analysis(company_url: str) -> bool:
    """
    Delete a company analysis from Supabase.

    Args:
        company_url: LinkedIn company URL to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()

        response = supabase.table('linkedin_company_analysis')\
            .delete()\
            .eq('company_url', company_url)\
            .execute()

        return True

    except Exception as e:
        print(f"Error deleting company analysis from Supabase: {e}")
        return False


def save_generated_posts(
    company_url: str,
    company_name: str,
    input_type: str,
    user_input: str,
    variations: List[Dict],
    model: str
) -> bool:
    """
    Save 3 generated post variations to Supabase.

    Args:
        company_url: LinkedIn company URL
        company_name: Company name
        input_type: "article", "topic", or "rewrite"
        user_input: Original user input
        variations: List of 3 variation dicts
        model: Model used for generation

    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()

        data = {
            'company_url': company_url,
            'company_name': company_name,
            'input_type': input_type,
            'user_input': user_input,
            'variation_1': json.dumps(variations[0]) if len(variations) > 0 else None,
            'variation_2': json.dumps(variations[1]) if len(variations) > 1 else None,
            'variation_3': json.dumps(variations[2]) if len(variations) > 2 else None,
            'generation_model': model
        }

        response = supabase.table('generated_posts').insert(data).execute()
        return True

    except Exception as e:
        print(f"Error saving generated posts to Supabase: {e}")
        return False


def get_generated_posts(company_url: str = None, limit: int = 50) -> List[Dict]:
    """
    Retrieve generated posts from Supabase.

    Args:
        company_url: Optional filter by company URL
        limit: Maximum number of records to return

    Returns:
        List of generated post dictionaries
    """
    try:
        supabase = get_supabase_client()

        query = supabase.table('generated_posts').select('*')

        if company_url:
            query = query.eq('company_url', company_url)

        response = query.order('created_at', desc=True).limit(limit).execute()

        posts = []
        for item in response.data:
            post = {
                'id': item.get('id'),
                'company_url': item.get('company_url'),
                'company_name': item.get('company_name'),
                'input_type': item.get('input_type'),
                'user_input': item.get('user_input'),
                'variation_1': json.loads(item.get('variation_1', '{}')),
                'variation_2': json.loads(item.get('variation_2', '{}')),
                'variation_3': json.loads(item.get('variation_3', '{}')),
                'generation_model': item.get('generation_model'),
                'created_at': item.get('created_at')
            }
            posts.append(post)

        return posts

    except Exception as e:
        print(f"Error retrieving generated posts from Supabase: {e}")
        return []
