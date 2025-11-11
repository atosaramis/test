# Quick Setup Guide

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (30 seconds)

```bash
cd blank-app-main
pip install -r requirements.txt
```

### Step 2: Configure Secrets (2 minutes)

**Create your secrets file:**

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

**Edit `.streamlit/secrets.toml` and add your credentials:**

```toml
APP_USERNAME = "admin"
APP_PASSWORD = "your_password_here"

DATAFORSEO_LOGIN = "your_login"
DATAFORSEO_PASSWORD = "your_password"
RAPIDAPI_KEY = "your_key"
OPENROUTER_API_KEY = "your_key"

SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_ANON_KEY = "your_key"
```

### Step 3: Run the App (10 seconds)

```bash
streamlit run streamlit_app.py
```

That's it! The app will open at `http://localhost:8501`

---

## 🔒 Security Features

### Complete Login Lockdown

The app enforces strict authentication:

- ✅ **NO access** to any page before login
- ✅ **NO buttons** or features visible until authenticated
- ✅ Login form is the **ONLY** thing rendered before authentication
- ✅ `st.stop()` prevents any code execution after login page
- ✅ All credentials stored in `.streamlit/secrets.toml` (gitignored)

### How it works:

1. App starts → Checks if user is authenticated
2. **Not authenticated** → Shows login page, calls `st.stop()`, nothing else renders
3. **Authenticated** → Proceeds to render dashboard and apps

### Authentication Flow:

```
User visits app
    ↓
Is authenticated?
    ↓ NO
Login page renders
st.stop() called  ← EXECUTION STOPS HERE
    ↓ Login success
Session state updated
Page reloads
    ↓ YES
Dashboard & apps render
```

---

## 🔑 Getting API Credentials

### DataForSEO (Keyword Research)

1. Go to https://dataforseo.com/
2. Sign up for an account
3. Navigate to API dashboard
4. Copy your login and password
5. Add to secrets.toml:
   ```toml
   DATAFORSEO_LOGIN = "your_login"
   DATAFORSEO_PASSWORD = "your_password"
   ```

### RapidAPI (LinkedIn Scraping)

1. Go to https://rapidapi.com/
2. Sign up for an account
3. Subscribe to a LinkedIn scraping API
4. Copy your API key from dashboard
5. Add to secrets.toml:
   ```toml
   RAPIDAPI_KEY = "your_key"
   ```

### OpenRouter (AI Analysis)

1. Go to https://openrouter.ai/
2. Sign up and add credits
3. Generate an API key
4. Add to secrets.toml:
   ```toml
   OPENROUTER_API_KEY = "your_key"
   ```

### Supabase (Database)

1. Go to https://supabase.com/
2. Create a new project
3. Go to Settings → API
4. Copy your project URL and anon key
5. Add to secrets.toml:
   ```toml
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_ANON_KEY = "your_anon_key"
   ```

---

## 🚨 Troubleshooting

### "Authentication credentials not configured"

**Problem**: The app can't find your secrets.toml file.

**Solution**:
1. Make sure `.streamlit/secrets.toml` exists
2. Check the file has the correct format (TOML)
3. Verify `APP_USERNAME` and `APP_PASSWORD` are set

### "Invalid credentials" on login

**Problem**: Username/password doesn't match secrets.toml.

**Solution**:
1. Double-check spelling in secrets.toml
2. No extra spaces in the values
3. Strings should be in quotes: `APP_USERNAME = "admin"`

### API errors when using features

**Problem**: API credentials not working.

**Solution**:
1. Verify all API keys are correctly copied
2. Check API service is active and has credits
3. Test API credentials directly on the provider's website

### Missing dependencies

**Problem**: Import errors when running the app.

**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

---

## 📁 File Locations

```
blank-app-main/
├── .streamlit/
│   ├── secrets.toml          ← YOUR CREDENTIALS (create this)
│   └── secrets.toml.example  ← Template (don't edit)
├── streamlit_app.py          ← Main app with authentication
├── app_linkedin.py           ← LinkedIn Analysis module
└── app_keywords.py           ← Keyword Research module
```

---

## ✅ Checklist

Before running the app, make sure:

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.streamlit/secrets.toml` file created
- [ ] `APP_USERNAME` and `APP_PASSWORD` set in secrets.toml
- [ ] All API credentials added to secrets.toml
- [ ] secrets.toml is **NOT** committed to git (it's in .gitignore)

---

## 🎯 Next Steps

After setup:

1. Run `streamlit run streamlit_app.py`
2. Login with your credentials
3. Click a card to open an app
4. Start analyzing LinkedIn or researching keywords!

Need help? Check the main DASHBOARD_README.md for detailed documentation.
