"""
Modern Dashboard Streamlit App with Query Parameter Navigation
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="SEO & Marketing Tools",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ============================================================================
# AUTHENTICATION GATE - NOTHING RENDERS UNTIL USER IS AUTHENTICATED
# ============================================================================

def check_password():
    """Returns True if user is authenticated. Renders login page if not."""

    def password_entered():
        """Validates credentials from Streamlit secrets."""
        try:
            # Get credentials from Streamlit secrets
            correct_username = st.secrets["APP_USERNAME"]
            correct_password = st.secrets["APP_PASSWORD"]

            if (st.session_state["username"] == correct_username and
                st.session_state["password"] == correct_password):
                st.session_state.authenticated = True
                # Clear password from session state for security
                del st.session_state["password"]
                del st.session_state["username"]
                # Clear query params to always start at dashboard after login
                st.query_params.clear()
            else:
                st.session_state.authenticated = False

        except KeyError:
            st.error("⚠️ Authentication credentials not configured in secrets.toml")
            st.stop()

    # If not authenticated, show ONLY the login form
    if not st.session_state.authenticated:
        # Login page CSS
        st.markdown("""
        <style>
            /* Hide Streamlit branding */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            /* Login page styling */
            .login-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 3rem;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
        </style>
        """, unsafe_allow_html=True)

        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("# 🚀 SEO & Marketing Tools")
            st.markdown("### Please login to continue")
            st.markdown("<br>", unsafe_allow_html=True)

            st.text_input("Username", key="username", placeholder="Enter username")
            st.text_input("Password", type="password", key="password", placeholder="Enter password")
            st.button("Login", on_click=password_entered, type="primary", use_container_width=True)

            # Show error only after a failed login attempt
            if "authenticated" in st.session_state and not st.session_state.authenticated:
                if "username" not in st.session_state:  # Error was triggered by failed login
                    st.error("😕 Username or password incorrect")

        # STOP execution - do not render anything else
        st.stop()

    return True

# Authentication gate - stops here if not authenticated
check_password()

# ============================================================================
# AUTHENTICATED USER AREA - Only renders if authentication passes
# ============================================================================

# Custom CSS for modern card design (only loads for authenticated users)
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Dashboard container */
    .dashboard-container {
        padding: 2rem 0;
    }

    /* Row 1 - LinkedIn (blue) */
    div[data-testid="column"]:nth-child(1) .stButton > button {
        background: linear-gradient(135deg, #0077B5 0%, #00A0DC 100%);
        color: white;
    }

    /* Row 1 - Keywords (purple) */
    div[data-testid="column"]:nth-child(2) .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    /* Row 2 - App 3 (green) */
    div[data-testid="column"]:nth-child(3) .stButton > button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }

    /* Row 2 - App 4 (orange) */
    div[data-testid="column"]:nth-child(4) .stButton > button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }


    /* Header styling */
    .dashboard-header {
        text-align: center;
        margin-bottom: 3rem;
    }

    .dashboard-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .dashboard-subtitle {
        font-size: 1.3rem;
        color: #666;
        font-weight: 400;
    }

    /* Back button styling */
    .back-button {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def navigate_to_app(app_name):
    """Callback to navigate to app"""
    st.query_params["app"] = app_name

def render_dashboard():
    """Render the modern card-based dashboard."""

    # Header
    st.markdown("""
    <div class="dashboard-header">
        <h1 class="dashboard-title">🚀 SEO & Marketing Tools</h1>
        <p class="dashboard-subtitle">Select a tool to get started with your analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # Logout button (top right)
    col1, col2, col3 = st.columns([4, 1, 1])
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            # Clear Grok chat history on logout
            if "grok_messages" in st.session_state:
                del st.session_state.grok_messages
            # Clear Sales chat history on logout
            if "sales_messages" in st.session_state:
                del st.session_state.sales_messages
            # Clear transcripts on logout
            if "transcripts" in st.session_state:
                del st.session_state.transcripts
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # App cards - Row 1
    col1, col2 = st.columns(2, gap="large")

    with col1:
        linkedin_card = """📊

**LinkedIn Analysis**

Analyze company LinkedIn presence and generate content in their voice"""

        st.button(linkedin_card, key="linkedin_btn", use_container_width=True, on_click=navigate_to_app, args=("linkedin",))

    with col2:
        keywords_card = """🔍

**Keyword Research**

Advanced SEO keyword research with search volume and competitor analysis"""

        st.button(keywords_card, key="keywords_btn", use_container_width=True, on_click=navigate_to_app, args=("keywords",))

    st.markdown("<br>", unsafe_allow_html=True)

    # App cards - Row 2
    col3, col4 = st.columns(2, gap="large")

    with col3:
        app3_card = """🤖

**Samba Knowledge Chat**

Chat with Samba Scientific's website using AI"""

        st.button(app3_card, key="app3_btn", use_container_width=True, on_click=navigate_to_app, args=("grok_chat",))

    with col4:
        app4_card = """🎙️

**Meeting Transcription**

Transcribe meetings, extract insights, and generate summaries"""

        st.button(app4_card, key="app4_btn", use_container_width=True, on_click=navigate_to_app, args=("transcription",))

    st.markdown("<br>", unsafe_allow_html=True)

    # App cards - Row 3
    col5, col6 = st.columns(2, gap="large")

    with col5:
        app5_card = """🎯

**Sales Menu Chat**

Chat with Samba Scientific's sales menu and services using AI"""

        st.button(app5_card, key="app5_btn", use_container_width=True, on_click=navigate_to_app, args=("sales_chat",))

    with col6:
        app6_card = """🔧

**Tech Stack Analyzer**

Discover what technologies power any website"""

        st.button(app6_card, key="app6_btn", use_container_width=True, on_click=navigate_to_app, args=("tech_stack",))

    st.markdown("<br>", unsafe_allow_html=True)

    # App cards - Row 4
    col7, col8 = st.columns(2, gap="large")

    with col7:
        app7_card = """📢

**Google Ads Intelligence**

Discover competitor ad creatives and campaigns running on Google Ads"""

        st.button(app7_card, key="app7_btn", use_container_width=True, on_click=navigate_to_app, args=("google_ads",))

    # Suggest Workflow Button
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <a href="https://forms.cloud.microsoft/r/eJnE5Lji2h" target="_blank" style="text-decoration: none;">
            <button style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 0.75rem 2rem;
                font-size: 1rem;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
                font-weight: 600;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(0,0,0,0.2)';"
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)';">
                💡 Suggest a Workflow
            </button>
        </a>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

def render_app(app_name):
    """Render the selected app based on query parameter."""

    # Back to dashboard button
    if st.button("← Back to Dashboard", key="back_btn", use_container_width=False):
        st.query_params.clear()
        st.rerun()

    # Logout button in sidebar
    with st.sidebar:
        st.markdown("### Navigation")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            # Clear Grok chat history on logout
            if "grok_messages" in st.session_state:
                del st.session_state.grok_messages
            # Clear Sales chat history on logout
            if "sales_messages" in st.session_state:
                del st.session_state.sales_messages
            # Clear transcripts on logout
            if "transcripts" in st.session_state:
                del st.session_state.transcripts
            st.query_params.clear()
            st.rerun()

        st.divider()
        st.caption("Currently viewing:")
        if app_name == "linkedin":
            st.info("📊 LinkedIn Analysis")
        elif app_name == "keywords":
            st.info("🔍 Keyword Research")
        elif app_name == "grok_chat":
            st.info("🤖 Samba Knowledge Chat")
        elif app_name == "sales_chat":
            st.info("🎯 Sales Menu Chat")
        elif app_name == "transcription":
            st.info("🎙️ Meeting Transcription")
        elif app_name == "tech_stack":
            st.info("🔧 Tech Stack Analyzer")
        elif app_name == "google_ads":
            st.info("📢 Google Ads Intelligence")

    # Import and render the appropriate app
    if app_name == "linkedin":
        from app_linkedin import render_linkedin_app
        render_linkedin_app()

    elif app_name == "keywords":
        from app_keywords import render_keywords_app
        render_keywords_app()

    elif app_name == "grok_chat":
        from app_grok_chat import render_grok_chat_app
        render_grok_chat_app()

    elif app_name == "sales_chat":
        from app_sales_chat import render_sales_chat_app
        render_sales_chat_app()

    elif app_name == "transcription":
        from app_transcription import render_transcription_app
        render_transcription_app()

    elif app_name == "tech_stack":
        from app_tech_stack import render_tech_stack_app
        render_tech_stack_app()

    elif app_name == "google_ads":
        from app_google_ads import render_google_ads_app
        render_google_ads_app()

    else:
        st.error(f"Unknown app: {app_name}")
        st.info("Returning to dashboard...")
        st.query_params.clear()
        st.rerun()

# Main application flow
if not check_password():
    st.stop()

# Check if an app is selected via query params
try:
    selected_app = st.query_params.get("app")
except:
    selected_app = None

if selected_app:
    # Render the selected app
    render_app(selected_app)
else:
    # Render the dashboard
    render_dashboard()
