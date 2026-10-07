import streamlit as st
import pandas as pd
import io
import datetime
import requests
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Secure Production Log", page_icon="🏭", layout="wide")

# ==================== MODERN UI STYLING ====================
st.markdown("""
<style>
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
    }
    div.stForm {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease-in-out;
    }
    hr {
        margin: 2rem 0;
        border-color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# 1. Configuration & Security Setup
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1gV2JAoaXqc0v5ClRlGmuGihExakxwrLQOOmlCxNwpAs/edit?usp=sharing"
GOOGLE_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz2ePknPsjK6YLxVIh7mMolJ_H-wKazZSKLBK2Y5KNjAZnaGZWUSGtiXiTZf3yF8kYJ/exec"
PLANT_UTC_OFFSET_HOURS = 0

USER_CREDENTIALS = {
    "wendy": {"password": "Pa55w.rd", "role": "operator"},
    "admin": {"password": "Pa55w.rd", "role": "manager"},
    "khin": {"password": "Pa55w.rd", "role": "operator"}
}

# 2. Helper Functions
def load_permanent_data():
    try:
        csv_url = GOOGLE_SHEET_URL.replace("/edit?usp=sharing", "/export?format=csv")
        df = pd.read_csv(csv_url)
        numeric_cols = ["Elapsed Hours", "Elapsed Mins", "Actual Bundles", "Expected Bundles", "Downtime Mins"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception:
        return pd.DataFrame(columns=["Timestamp", "Line", "Shift", "Logged By", "Elapsed Hours", "Elapsed Mins", "Actual Bundles", "Expected Bundles", "Downtime Mins"])

def send_data_to_google(new_row_dict):
    if "REPLACE_WITH_YOUR_APPS_SCRIPT_DEPLOYMENT_ID" in GOOGLE_WEB_APP_URL:
        st.warning("⚠️ Cloud Sync Note: To save directly to Google Sheets, make sure to add your Apps Script URL at the top of the code.")
        return False
    try:
        response = requests.post(GOOGLE_WEB_APP_URL, json=new_row_dict, timeout=10)
        if response.status_code == 200:
            st.toast("Line updated successfully in Google Sheets! 💾", icon="✅")
            return True
        else:
            st.error(f"Sync connection returned code: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Cloud connection failed: {e}")
        return False

def get_local_timestamp():
    utc_now = datetime.datetime.utcnow()
    local_now = utc_now + datetime.timedelta(hours=PLANT_UTC_OFFSET_HOURS)
    return local_now.strftime("%Y-%m-%d %H:%M:%S")

# 3. Auth Engine Setup
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        st.markdown("<h2 style='text-align: center;'>🏭 Plant Control Portal</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Enter credentials to access secure production operations.</p>", unsafe_allow_html=True)
        with st.form("Login Form"):
            username_input = st.text_input("Username").strip().lower()
            password_input = st.text_input("Password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Log In", type="primary", use_container_width=True):
                if username_input in USER_CREDENTIALS and USER_CREDENTIALS[username_input]["password"] == password_input:
                    st.session_state.authenticated = True
                    st.session_state.username = username_input
                    st.session_state.user_role = USER_CREDENTIALS[username_input]["role"]
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    st.stop()

# Header Panel
header_col
