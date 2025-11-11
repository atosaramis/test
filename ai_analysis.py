"""
AI Analysis Module for LinkedIn Company Strategy

Analyzes companies' LinkedIn presence as a whole to extract:
- Voice & Tone Profile
- Content Strategy & Pillars
- Engagement Patterns
- Content Generation capabilities
"""

import os
import json
import requests
from typing import Dict, List, Optional
from pathlib import Path


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


def get_prompt_template(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        prompt_name: Name of the prompt file (without .txt extension)

    Returns:
        Prompt template as string
    """
    prompt_file = Path(__file__).parent / "prompts" / f"{prompt_name}.txt"

    try:
        with open(prompt_file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise Exception(f"Prompt template not found: {prompt_file}")


def call_openrouter(
    prompt: str,
    model: str = "anthropic/claude-haiku-4.5",
    max_tokens: int = 3000
) -> Dict:
    """
    Call OpenRouter API with specified Claude model.

    Args:
        prompt: The prompt to send to the model
        model: Model to use (default: claude-3.5-haiku)
        max_tokens: Maximum tokens in response

    Returns:
        Dict with either {"content": str} or {"error": str}
    """
    api_key = get_credential("OPENROUTER_API_KEY")

    if not api_key:
        return {"error": "OPENROUTER_API_KEY not configured"}

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3  # Lower temperature for consistent analysis
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        # Get response text for error messages
        response_text = response.text

        response.raise_for_status()

        data = response.json()

        if data.get("choices") and len(data["choices"]) > 0:
            return {"content": data["choices"][0]["message"]["content"]}
        else:
            return {"error": f"No response from model. Response: {response_text[:500]}"}

    except requests.exceptions.HTTPError as e:
        # Capture HTTP error details
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", str(error_data))
        except:
            error_msg = response_text[:500]
        return {"error": f"OpenRouter HTTP {response.status_code}: {error_msg}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"OpenRouter API request failed: {str(e)}"}

    except Exception as e:
        return {"error": f"OpenRouter error: {str(e)}"}


def parse_json_response(response_dict: Dict) -> Dict:
    """
    Parse JSON from model response, handling markdown code blocks.

    Args:
        response_dict: Response dict from call_openrouter with "content" or "error"

    Returns:
        Parsed JSON dict, or error dict if parsing fails
    """
    # Check if there was an API error
    if response_dict.get("error"):
        return {"error": response_dict["error"]}

    response_text = response_dict.get("content")
    if not response_text:
        return {"error": "No content in API response"}

    # Remove markdown code blocks if present
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]

    if response_text.endswith("```"):
        response_text = response_text[:-3]

    response_text = response_text.strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON: {str(e)}. Response: {response_text[:500]}"}


def analyze_company_voice(
    posts_list: List[Dict],
    company_name: str,
    model: str = "anthropic/claude-haiku-4.5"
) -> Dict:
    """
    Analyze company's overall voice and tone from all posts.

    Args:
        posts_list: List of post dicts with 'text' key
        company_name: Company name
        model: Claude model to use

    Returns:
        Dict with voice profile analysis
    """
    if not posts_list:
        return {"error": "No posts to analyze"}

    # Aggregate all post text
    all_posts_text = "\n\n---POST BREAK---\n\n".join([
        f"Post {i+1}:\n{post.get('text', '')}"
        for i, post in enumerate(posts_list)
        if post.get('text')
    ])

    prompt_template = get_prompt_template("company_voice_profile")
    prompt = prompt_template.replace("{company_name}", company_name)
    prompt = prompt.replace("{num_posts}", str(len(posts_list)))
    prompt = prompt.replace("{all_posts_text}", all_posts_text[:15000])  # Limit to ~15K chars

    print(f"Analyzing voice profile for {company_name}...")

    response = call_openrouter(prompt, model, max_tokens=2000)
    result = parse_json_response(response)

    # Check if parsing returned an error
    if result.get("error"):
        return {
            "error": f"Failed to analyze voice profile: {result['error']}",
            "overall_tone": "unknown",
            "consistency_score": 0
        }

    return result


def analyze_content_strategy(
    posts_list: List[Dict],
    company_name: str,
    model: str = "anthropic/claude-haiku-4.5"
) -> Dict:
    """
    Analyze company's content strategy and distribution.

    Args:
        posts_list: List of post dicts
        company_name: Company name
        model: Claude model to use

    Returns:
        Dict with content strategy analysis
    """
    if not posts_list:
        return {"error": "No posts to analyze"}

    # Aggregate all post text
    all_posts_text = "\n\n---POST BREAK---\n\n".join([
        f"Post {i+1}:\n{post.get('text', '')}"
        for i, post in enumerate(posts_list)
        if post.get('text')
    ])

    prompt_template = get_prompt_template("company_content_strategy")
    prompt = prompt_template.replace("{company_name}", company_name)
    prompt = prompt.replace("{num_posts}", str(len(posts_list)))
    prompt = prompt.replace("{all_posts_text}", all_posts_text[:15000])

    print(f"Analyzing content strategy for {company_name}...")

    response = call_openrouter(prompt, model, max_tokens=2000)
    result = parse_json_response(response)

    # Check if parsing returned an error
    if result.get("error"):
        return {
            "error": f"Failed to analyze content strategy: {result['error']}",
            "content_pillar_distribution": {},
            "primary_focus": "unknown"
        }

    return result


def analyze_engagement_patterns(
    posts_list: List[Dict],
    company_name: str,
    model: str = "anthropic/claude-haiku-4.5"
) -> Dict:
    """
    Analyze engagement patterns and what content performs best.

    Args:
        posts_list: List of post dicts with engagement metrics
        company_name: Company name
        model: Claude model to use

    Returns:
        Dict with engagement analysis
    """
    if not posts_list:
        return {"error": "No posts to analyze"}

    # Format posts with engagement data
    posts_with_metrics = "\n\n---POST BREAK---\n\n".join([
        f"Post {i+1}:\n"
        f"Text: {post.get('text', '')}\n"
        f"Likes: {post.get('num_likes', 0)}\n"
        f"Comments: {post.get('num_comments', 0)}\n"
        f"Reposts: {post.get('num_reposts', 0)}\n"
        f"Posted: {post.get('posted', 'unknown')}"
        for i, post in enumerate(posts_list)
        if post.get('text')
    ])

    prompt_template = get_prompt_template("company_engagement_analysis")
    prompt = prompt_template.replace("{company_name}", company_name)
    prompt = prompt.replace("{num_posts}", str(len(posts_list)))
    prompt = prompt.replace("{posts_with_metrics}", posts_with_metrics[:15000])

    print(f"Analyzing engagement patterns for {company_name}...")

    response = call_openrouter(prompt, model, max_tokens=2500)
    result = parse_json_response(response)

    # Check if parsing returned an error
    if result.get("error"):
        return {
            "error": f"Failed to analyze engagement: {result['error']}",
            "avg_engagement": {},
            "top_performing_content_types": []
        }

    return result


def analyze_company_complete(
    posts_list: List[Dict],
    company_name: str,
    company_url: str,
    model: str = "anthropic/claude-haiku-4.5"
) -> Dict:
    """
    Run complete company-level analysis.

    Args:
        posts_list: List of post dicts
        company_name: Company name
        company_url: LinkedIn URL
        model: Claude model to use

    Returns:
        Dict with all analysis results
    """
    print(f"\n{'='*60}")
    print(f"Analyzing {company_name} ({len(posts_list)} posts)")
    print(f"{'='*60}\n")

    # Run all analyses
    voice_profile = analyze_company_voice(posts_list, company_name, model)
    content_strategy = analyze_content_strategy(posts_list, company_name, model)
    engagement_metrics = analyze_engagement_patterns(posts_list, company_name, model)

    # Calculate date range
    dates = [p.get('posted', '') for p in posts_list if p.get('posted')]
    date_range = f"{dates[-1]} to {dates[0]}" if dates else "Unknown"

    # Extract top posts (top 5 by engagement)
    posts_with_engagement = [
        {
            'text': p.get('text', '')[:200],
            'url': p.get('url', ''),
            'engagement': p.get('num_likes', 0) + p.get('num_comments', 0) + p.get('num_reposts', 0)
        }
        for p in posts_list
        if p.get('text')
    ]
    top_posts = sorted(posts_with_engagement, key=lambda x: x['engagement'], reverse=True)[:5]

    analysis = {
        "company_url": company_url,
        "company_name": company_name,
        "posts_analyzed": len(posts_list),
        "date_range": date_range,
        "voice_profile": voice_profile,
        "content_pillars": content_strategy,
        "engagement_metrics": engagement_metrics,
        "top_posts": top_posts,
        "analysis_model": model
    }

    print(f"\n✅ Analysis complete for {company_name}\n")

    return analysis


def generate_content(
    voice_profile: Dict,
    content_strategy: Dict,
    input_type: str,
    user_input: str,
    model: str = "anthropic/claude-haiku-4.5",
    variation_number: int = 1
) -> Dict:
    """
    Generate LinkedIn post in company's voice.

    Args:
        voice_profile: Company voice profile from analysis
        content_strategy: Company content strategy from analysis
        input_type: "article", "topic", "rewrite"
        user_input: User's input (URL, topic, or content to rewrite)
        model: Claude model to use
        variation_number: Which variation to generate (1, 2, or 3)

    Returns:
        Dict with generated post
    """
    prompt_template = get_prompt_template("content_generation")

    # Format voice profile and content strategy as strings
    voice_str = json.dumps(voice_profile, indent=2)
    strategy_str = json.dumps(content_strategy, indent=2)

    # Add variation instructions to the prompt
    variation_instructions = {
        1: "Focus on a data-driven, analytical approach with specific metrics and frameworks.",
        2: "Focus on storytelling and emotional resonance with relatable examples.",
        3: "Focus on thought leadership with bold insights and industry predictions."
    }

    prompt = prompt_template.replace("{voice_profile}", voice_str)
    prompt = prompt.replace("{content_strategy}", strategy_str)
    prompt = prompt.replace("{input_type}", input_type)
    prompt = prompt.replace("{user_input}", user_input)

    # Add variation instruction
    prompt += f"\n\nVARIATION STYLE: {variation_instructions.get(variation_number, variation_instructions[1])}"

    print(f"Generating content variation {variation_number} ({input_type})...")

    response = call_openrouter(prompt, model, max_tokens=2000)
    result = parse_json_response(response)

    # Check if parsing returned an error
    if result.get("error"):
        return {
            "error": f"Failed to generate content: {result['error']}",
            "post_text": "Generation failed. Please try again."
        }

    return result
