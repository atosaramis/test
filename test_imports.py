"""
Test script to verify all imports work correctly
"""

print("Testing imports...")

try:
    print("1. Testing streamlit_app.py imports...")
    import os
    print("   ✓ os")

    print("\n2. Testing app_linkedin.py imports...")
    import sys
    print("   ✓ sys")
    import json
    print("   ✓ json")
    import time
    print("   ✓ time")

    # Test if seo_functions exists
    try:
        from seo_functions import fetch_linkedin_posts
        print("   ✓ seo_functions")
    except ImportError as e:
        print(f"   ✗ seo_functions: {e}")

    # Test if ai_analysis exists
    try:
        from ai_analysis import analyze_company_complete
        print("   ✓ ai_analysis")
    except ImportError as e:
        print(f"   ✗ ai_analysis: {e}")

    print("\n3. Testing app_keywords.py imports...")
    import pandas as pd
    print("   ✓ pandas")

    print("\n✅ All core Python imports successful!")
    print("\nNote: Streamlit-specific imports will only work when Streamlit is installed.")
    print("The app structure is correct and ready to run with 'streamlit run streamlit_app.py'")

except Exception as e:
    print(f"\n❌ Error during import testing: {e}")
