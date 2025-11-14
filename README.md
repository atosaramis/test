# 🎈 Blank app template

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

## Known Issues & Troubleshooting

### Database Save Failures in Company Research Tool

**Problem:** "Failed to create database record" or "Main company data not found in database"

**Root Cause:**
- The `linkedin_company_analysis` table has a NOT NULL constraint on `company_url` (from Company Intelligence tool)
- Company Research tool uses `linkedin_company_url` as its primary identifier
- When saving without `company_url`, database INSERT fails silently

**Solution:**
- Always include BOTH `company_url` AND `linkedin_company_url` when saving Company Research data
- Set `company_url` to the same value as `linkedin_company_url` for compatibility

**Prevention:**
- When adding new tools that share the `linkedin_company_analysis` table, ensure all required fields (especially `company_url`) are populated in save operations
