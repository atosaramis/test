"""
Test script to diagnose OpenRouter API issues
"""
import os
import json
import requests
from pathlib import Path

def load_secrets():
    """Load credentials from .streamlit/secrets.toml"""
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"

    if not secrets_path.exists():
        print(f"❌ secrets.toml not found at: {secrets_path}")
        return None

    secrets = {}
    with open(secrets_path, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                secrets[key] = value

    return secrets

def test_openrouter_api():
    """Test OpenRouter API call"""
    print("=" * 60)
    print("OpenRouter API Test")
    print("=" * 60)

    # Load credentials
    print("\n1. Loading credentials from secrets.toml...")
    secrets = load_secrets()

    if not secrets:
        return

    api_key = secrets.get('OPENROUTER_API_KEY')

    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in secrets.toml")
        return

    print(f"✅ API Key found: {api_key[:20]}...{api_key[-10:]}")

    # Test API call
    print("\n2. Making test API call...")
    print(f"   Model: anthropic/claude-haiku-4.5")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "anthropic/claude-haiku-4.5",
        "messages": [
            {
                "role": "user",
                "content": "Say 'test successful' if you can read this."
            }
        ],
        "max_tokens": 50,
        "temperature": 0.3
    }

    try:
        print("   Sending request...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"\n3. Response Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ API call successful!")
            data = response.json()

            if data.get("choices"):
                content = data["choices"][0]["message"]["content"]
                print(f"\n   Model Response: {content}")
            else:
                print(f"\n   Response data: {json.dumps(data, indent=2)}")

        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"\n   Error Response:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)

    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_openrouter_api()
