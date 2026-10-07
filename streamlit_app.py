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
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("🏭 Secure Production & Downtime Dashboard")
    st.caption(f"Logged in as: **{st.session_state.username.upper()}** | Role: **{st.session_state.user_role.capitalize()}**")
with header_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Log Out", type="secondary", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.divider()

# Pull live logs from permanent database
db_df = load_permanent_data()

if "local_line_tracking" not in st.session_state:
    st.session_state.local_line_tracking = {}

if st.session_state.local_line_tracking:
    local_df = pd.DataFrame(st.session_state.local_line_tracking.values())
    combined_df = pd.concat([local_df, db_df], ignore_index=True).drop_duplicates(subset=["Line"], keep="first")
else:
    combined_df = db_df.drop_duplicates(subset=["Line"], keep="first")

# 4. Interactive Analytics Panel
if not combined_df.empty:
    st.subheader("📊 Live Production Performance Metrics")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    try:
        temp_df = combined_df.copy()
        temp_df["Timestamp_dt"] = pd.to_datetime(temp_df["Timestamp"], errors="coerce")
        latest_row = temp_df.sort_values(by="Timestamp_dt", ascending=False).iloc[0]
        last_updated_hours = latest_row["Elapsed Hours"]
    except Exception:
        last_updated_hours = combined_df.iloc[0]["Elapsed Hours"]
        
    total_actual = combined_df["Actual Bundles"].sum()
    total_expected = combined_df["Expected Bundles"].sum()
    total_downtime = combined_df["Downtime Mins"].sum()
    plant_efficiency = (total_actual / total_expected * 100) if total_expected > 0 else 0
    
    with kpi_col1:
        st.metric("Total Operational Time", f"{last_updated_hours:.2f} Hrs")
    with kpi_col2:
        st.metric("Actual Units Produced", f"{int(total_actual):,}")
    with kpi_col3:
        st.metric("Total Lost Production Time", f"{int(total_downtime):,} Mins", delta=f"{int(total_downtime)} mins delay", delta_color="inverse")
    with kpi_col4:
        st.metric("Overall Plant Efficiency", f"{plant_efficiency:.1f}%")
        
    st.markdown("<br>", unsafe_allow_html=True)
    graph_col1, graph_col2 = st.columns(2)
    
    with graph_col1:
        st.markdown("#### ⏳ Accumulated Downtime Minutes by Line")
        downtime_summary = combined_df.groupby("Line", as_index=False)["Downtime Mins"].sum()
        fig_bar = px.bar(
            downtime_summary, x="Line", y="Downtime Mins", text_auto=True, color="Line",
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={"Downtime Mins": "Downtime (Minutes)", "Line": "Production Line"}
        )
        fig_bar.update_layout(showlegend=False, height=350, margin=dict(t=20, b=10, l=10, r=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with graph_col2:
        st.markdown("#### 📈 Actual vs. Expected Output by Shift")
        shift_summary = combined_df.groupby("Shift", as_index=False)[["Actual Bundles", "Expected Bundles"]].sum()
        fig_group = go.Figure()
        fig_group.add_trace(go.Bar(name='Actual Units', x=shift_summary['Shift'], y=shift_summary['Actual Bundles'], marker_color='#3b82f6'))
        fig_group.add_trace(go.Bar(name='Expected Target', x=shift_summary['Shift'], y=shift_summary['Expected Bundles'], marker_color='#cbd5e1'))
        fig_group.update_layout(barmode='group', height=350, margin=dict(t=20, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_group, use_container_width=True)
        
    st.divider()

# 5. Input Portal Layout (7:30 to 7:30 Shift Window Alignment)
st.subheader("📥 Log New Shift Performance Data")
col_input1, col_input2 = st.columns(2, gap="large")

with col_input1:
    machine_family = st.selectbox("Select Machine Family", options=["Absolut Machines (CP01-CP04)", "Garant Machines (CP05-CP14)"])
    
    if "Absolut" in machine_family:
        line_name = st.selectbox("Select Production Line", options=["CP01", "CP02", "CP03", "CP04"])
    else:
        line_name = st.selectbox("Select Production Line", options=[f"CP{i:02d}" for i in range(5, 15)])
        
    shift_name = st.selectbox("Select 12-Hour Shift Cycle", options=["Shift A (07:30 - 19:30)", "Shift B (19:30 - 07:30)"])
    actual_bundles = st.number_input("Actual Production Output (Units)", min_value=0, value=10, step=1)

with col_input2:
    st.markdown("**⏰ 12-Hour Shift Operational Window (07:30 to 07:30)**")
    
    st.markdown("##### ⏱️ Start Time")
    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        start_hour = st.number_input("Hour", min_value=1, max_value=12, value=7, step=1)
    with s_col2:
        start_min = st.number_input("Minute", min_value=0, max_value=59, value=30, step=1)
    with s_col3:
        start_ampm = st.selectbox("AM/PM", options=["AM", "PM"])
        
    st.markdown("##### ⏱️ End Time (Max 12 Hours Duration)")
    e_col1, e_col2, e_col3 = st.columns(3)
    with e_col1:
        end_hour = st.number_input("To Hour", min_value=1, max_value=12, value=7, step=1)
    with e_col2:
        end_min = st.number_input("To Minute", min_value=0, max_value=59, value=30, step=1)
    with e_col3:
        end_ampm = st.selectbox("To AM/PM", options=["PM", "AM"])
        
    st.markdown("<br>", unsafe_allow_html=True)
    submit_clicked = st.button("🚀 Submit & Calculate Data", type="primary", use_container_width=True)

if submit_clicked:
    def to_24hr_mins(hr, mn, ap):
        h24 = hr % 12
        if ap == "PM":
            h24 += 12
        return (h24 * 60) + mn

    start_total_mins = to_24hr_mins(start_hour, start_min, start_ampm)
    end_total_mins = to_24hr_mins(end_hour, end_min, end_ampm)
    
    elapsed_minutes = end_total_mins - start_total_mins
    if elapsed_minutes < 0:
        elapsed_minutes += 24 * 60

    elapsed_hours_decimal = elapsed_minutes / 60.0
    
    if "Absolut" in machine_family:
        expected_bundles = elapsed_minutes * 1.0
        downtime_minutes = elapsed_minutes - actual_bundles
    else:
        expected_bundles = elapsed_minutes / 4.0
        downtime_minutes = elapsed_minutes - (actual_bundles * 4.0)
    
    if elapsed_minutes == 0 or elapsed_minutes > 720:
        st.error("❌ Error: 12-hour shift interval cannot exceed 720 minutes or be zero.")
    elif actual_bundles > expected_bundles:
        st.error(f"❌ Error: Actual production ({actual_bundles}) exceeds maximum expected capacity ({expected_bundles:.1f}) for this timeframe.")
    else:
        current_time_str = get_local_timestamp()
        
        new_entry = {
            "Timestamp": current_time_str,
            "Line": line_name,
            "Shift": shift_name,
            "Logged By": st.session_state.username,
            "Elapsed Hours": round(elapsed_hours_decimal, 2),
            "Elapsed Mins": int(elapsed_minutes),
            "Actual Bundles": int(actual_bundles),
            "Expected Bundles": round(expected_bundles, 2),
            "Downtime Mins": int(max(0, downtime_minutes))
        }
        
        send_data_to_google(new_entry)
        st.session_state.local_line_tracking[line_name] = new_entry
        st.success(f"Production metrics for Line {line_name} updated successfully!")
        st.rerun()

st.divider()

# 6. Continuous Data Ledger with 12-Hour Shift Separation Tabs
st.subheader("📊 Live Connected Production Database Ledger")

tab_all, tab_shift_a, tab_shift_b = st.tabs(["📋 Complete Master Ledger", "☀️ Shift A Logs (07:30 - 19:30)", "🌙 Shift B Logs (19:30 - 07:30)"])

with tab_all:
    st.dataframe(combined_df, use_container_width=True, hide_index=True)

with tab_shift_a:
    if not combined_df.empty and "Shift" in combined_df.columns:
        df_a = combined_df[combined_df["Shift"].str.contains("Shift A", na=False)]
        st.dataframe(df_a, use_container_width=True, hide_index=True)
    else:
        st.info("No Shift A entries logged yet.")

with tab_shift_b:
    if not combined
