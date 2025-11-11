# Modern Dashboard Streamlit App

A modern, card-based dashboard for SEO and marketing tools with query parameter navigation.

## 🎨 Features

- **Modern Card Dashboard**: Beautiful gradient cards with hover effects
- **Query Parameter Navigation**: Clean URL-based routing (`?app=linkedin` or `?app=keywords`)
- **Single-Page Experience**: No sidebar clutter, everything on one page
- **Two Powerful Tools**:
  - 📊 **LinkedIn Analysis**: Analyze company LinkedIn presence, voice profiles, and generate AI-powered posts
  - 🔍 **Keyword Research**: Discover keywords, analyze competitors, track trends with advanced SEO metrics

## 📁 File Structure

```
blank-app-main/
├── streamlit_app.py          # Main dashboard with authentication & routing
├── app_linkedin.py            # LinkedIn Analysis module
├── app_keywords.py            # Keyword Research module
├── seo_functions.py           # API & database functions
├── ai_analysis.py             # AI analysis functions
├── requirements.txt           # Python dependencies
├── pages/                     # Old multi-page structure (can be deleted)
└── prompts/                   # AI prompts for content generation
```

## 🚀 Setup & Installation

### 1. Install Dependencies

```bash
# Navigate to the app directory
cd blank-app-main

# Install required packages
pip install -r requirements.txt
```

### 2. Configure Secrets (REQUIRED)

The app uses Streamlit secrets for secure credential management. **You must set up secrets before the app will run.**

#### Step 1: Create secrets file

```bash
# Copy the template
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

#### Step 2: Edit `.streamlit/secrets.toml` with your credentials

```toml
# REQUIRED: App Authentication
APP_USERNAME = "your_username"
APP_PASSWORD = "your_secure_password"

# REQUIRED: API Credentials
DATAFORSEO_LOGIN = "your_dataforseo_login"
DATAFORSEO_PASSWORD = "your_dataforseo_password"
RAPIDAPI_KEY = "your_rapidapi_key"
OPENROUTER_API_KEY = "your_openrouter_key"

# REQUIRED: Database
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
```

#### Important Security Notes:

- ✅ `.streamlit/secrets.toml` is in `.gitignore` (won't be committed)
- ✅ Never commit secrets.toml to version control
- ✅ Never share your secrets.toml file
- ✅ Each team member needs their own secrets.toml file

#### Where to get API credentials:

- **DataForSEO**: https://dataforseo.com/ (for keyword research)
- **RapidAPI**: https://rapidapi.com/ (for LinkedIn scraping)
- **OpenRouter**: https://openrouter.ai/ (for AI analysis)
- **Supabase**: https://supabase.com/ (for database)

### 3. Run the App

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

**Important**: The app will show an error if secrets.toml is not configured. Make sure to complete Step 2 above.

## 🎯 How to Use

### Login
- Use your configured username/password to access the dashboard
- Default is `admin/admin` if not configured

### Dashboard Navigation
1. **Main Dashboard**: After login, you'll see two modern cards
   - Click "Open LinkedIn Analysis" to access LinkedIn tools
   - Click "Open Keyword Research" to access SEO tools

2. **Using Apps**:
   - Click "← Back to Dashboard" to return to the main dashboard
   - Logout button is in the sidebar when viewing an app
   - URLs use query parameters: `?app=linkedin` or `?app=keywords`

### LinkedIn Analysis
- **Onboard New Client**: Add a client's LinkedIn URL and website domain
- **My Clients**: View all analyzed clients with voice profiles and metrics
- **Competitor Comparison**: Compare multiple companies side-by-side
- **Content Creation**: Generate LinkedIn posts in client's voice

### Keyword Research
- **Search Keywords**: Enter a keyword or get 100 related suggestions
- **Analyze Competitors**: Enter a URL to see their ranking keywords
- **Advanced Filters**: Filter by volume, competition, trends
- **Trend Visualization**: Compare multiple keywords over 12 months

## 🎨 Customization

### Changing Dashboard Colors

Edit the CSS gradients in `streamlit_app.py`:

```python
# LinkedIn card gradient (blue theme)
.app-card.linkedin {
    background: linear-gradient(135deg, #0077B5 0%, #00A0DC 100%);
}

# Keywords card gradient (purple theme)
.app-card.keywords {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### Adding More Apps

1. Create a new module: `app_yourname.py`
2. Add a `render_yourname_app()` function
3. Add a new card in the dashboard section of `streamlit_app.py`
4. Add a routing case in the `render_app()` function

Example:

```python
# In streamlit_app.py dashboard section
with col3:
    st.markdown("""
    <div class="app-card yourapp">
        <div>
            <span class="card-icon">🎯</span>
            <h2 class="card-title">Your App Name</h2>
            <p class="card-description">Your app description here.</p>
        </div>
        <div class="card-arrow">→ Click to start</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Your App", key="yourapp_btn", use_container_width=True, type="primary"):
        st.query_params["app"] = "yourapp"
        st.rerun()
```

## 🔧 Troubleshooting

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that Python version is 3.8+

### Database Connection Issues
- Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set correctly
- Check that your Supabase project is active

### API Rate Limits
- DataForSEO and RapidAPI have rate limits
- Consider implementing caching for frequently accessed data

## 📝 Migration Notes

### From Old Multi-Page Structure

The old app used Streamlit's built-in multi-page navigation with files in `pages/`:
- `pages/LinkedIn_Posts.py`
- `pages/Keywords.py`
- `pages/Stored_Data.py`

The new app uses:
- Query parameter navigation (`?app=linkedin`)
- Single main file (`streamlit_app.py`)
- Modular app files (`app_linkedin.py`, `app_keywords.py`)

**Benefits:**
- Cleaner URLs
- Faster navigation (no page reloads)
- Better user experience
- More control over layout
- Easier to customize

## 🎯 Next Steps

1. **Add More Apps**: Create additional tools following the module pattern
2. **Enhance Dashboard**: Add metrics, recent activity, or quick actions
3. **Improve Styling**: Customize colors, fonts, and animations
4. **Add Features**: User management, data export, scheduled reports
5. **Optimize Performance**: Implement caching, lazy loading

## 📄 License

Apache License 2.0

---

**Questions or Issues?** Open an issue or contact your development team.
