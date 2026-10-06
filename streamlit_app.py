import streamlit as st
import pandas as pd
import io
import datetime
import requests
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Secure Production Log", page_icon="🏭", layout="wide")

# 1. Configuration & Security Setup
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1gV2JAoaXqc0v5ClRlGmuGihExakxwrLQOOmlCxNwpAs/edit?usp=sharing"

# PASTE YOUR COPIED GOOGLE APPS SCRIPT WEB APP URL HERE:
GOOGLE_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz2ePknPsjK6YLxVIh7mMolJ_H-wKazZSKLBK2Y5KNjAZnaGZWUSGtiXiTZf3yF8kYJ/exec"

USER_CREDENTIALS = {
    "operator1": {"password": "Pa55w.rd", "role": "operator"},
    "manager1": {"password": "Pa55w.rd", "role": "manager"}
}

# 2. Helper Functions to Sync data with Google Sheets
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
            st.toast("Saved directly to Google Sheets! 💾", icon="✅")
            return True
        else:
            st.error(f"Sync connection returned code: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Cloud connection failed: {e}")
        return False

# 3. Auth Engine Setup
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center;'>🏭 Plant Control Login Portal</h2>", unsafe_allow_html=True)
    with st.form("Login Form"):
        username_input = st.text_input("Username").strip().lower()
        password_input = st.text_input("Password", type="password")
        if st.form_submit_button("Log In", type="primary"):
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
    if st.button("Log Out", type="secondary", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.divider()

# Pull live logs from permanent database
db_df = load_permanent_data()

# Combine cloud records with local session entries dynamically
if "local_backup" in st.session_state and st.session_state.local_backup:
    session_df = pd.DataFrame(st.session_state.local_backup)
    combined_df = pd.concat([session_df, db_df], ignore_index=True).drop_duplicates(subset=["Timestamp", "Line", "Shift", "Logged By"], keep="first")
else:
    combined_df = db_df

# 4. Interactive Analytics Panel (Visual Metric Charts)
if not combined_df.empty:
    st.subheader("📊 Live Production Performance Metrics")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    total_hours = combined_df["Elapsed Hours"].sum()
    total_actual = combined_df["Actual Bundles"].sum()
    total_expected = combined_df["Expected Bundles"].sum()
    total_downtime = combined_df["Downtime Mins"].sum()
    
    plant_efficiency = (total_actual / total_expected * 100) if total_expected > 0 else 0
    
    with kpi_col1:
        st.metric("Total Operational Time", f"{total_hours:.1f} Hrs")
    with kpi_col2:
        st.metric("Actual Bundles Produced", f"{int(total_actual):,}")
    with kpi_col3:
        st.metric("Total Lost Production Time", f"{int(total_downtime):,} Mins", delta=f"{int(total_downtime)} mins delay", delta_color="inverse")
    with kpi_col4:
        st.metric("Overall Plant Efficiency", f"{plant_efficiency:.1f}%")
        
    graph_col1, graph_col2 = st.columns(2)
    
    with graph_col1:
        st.markdown("#### ⏳ Accumulated Downtime Minutes by Production Line")
        downtime_summary = combined_df.groupby("Line", as_index=False)["Downtime Mins"].sum()
        
        fig_bar = px.bar(
            downtime_summary, 
            x="Line", 
            y="Downtime Mins", 
            text_auto=True,
            color="Line",
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={"Downtime Mins": "Downtime (Minutes)", "Line": "Production Line"}
        )
        fig_bar.update_layout(showlegend=False, height=350, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with graph_col2:
        st.markdown("#### 📈 Actual vs. Expected Production Bundles by Shift")
        shift_summary = combined_df.groupby("Shift", as_index=False)[["Actual Bundles", "Expected Bundles"]].sum()
        
        fig_group = go.Figure()
        fig_group.add_trace(go.Bar(name='Actual Bundles', x=shift_summary['Shift'], y=shift_summary['Actual Bundles'], marker_color='#2ca02c'))
        fig_group.add_trace(go.Bar(name='Expected Target', x=shift_summary['Shift'], y=shift_summary['Expected Bundles'], marker_color='#d62728'))
        
        fig_group.update_layout(barmode='group', height=350, margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=102, xanchor="right", x=1))
        st.plotly_chart(fig_group, use_container_width=True)
        
    st.divider()

# 5. Input Portal Layout
st.subheader("📥 Log New Shift Performance Data")
col_input1, col_input2 = st.columns(2)

with col_input1:
    line_name = st.selectbox("Select Production Line", options=["CP01", "CP02", "CP03", "CP04"])
    shift_name = st.selectbox("Select Shift", options=["A", "B", "C", "D"])

with col_input2:
    time_col1, time_col2 = st.columns(2)
    with time_col1:
        input_hours = st.number_input("Elapsed Hours", min_value=0, value=1, step=1)
    with time_col2:
        input_minutes = st.number_input("Elapsed Minutes", min_value=0, max_value=59, value=0, step=1)
        
    actual_bundles = st.number_input("Actual Bundles Produced", min_value=0, value=10, step=1)

if st.button("Submit & Calculate Data", type="primary"):
    elapsed_minutes = (input_hours * 60) + input_minutes
    elapsed_hours_decimal = elapsed_minutes / 60.0
    expected_bundles = elapsed_minutes * 1.0
    
    if actual_bundles > expected_bundles:
        st.error(f"❌ Error: Actual bundles ({actual_bundles}) exceed capacity for this timeframe.")
    elif elapsed_minutes == 0:
        st.error("❌ Error: Total elapsed runtime cannot be zero.")
    else:
        downtime_minutes = elapsed_minutes - actual_bundles
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_entry = {
            "Timestamp": current_time_str,
            "Line": line_name,
            "Shift": shift_name,
            "Logged By": st.session_state.username,
            "Elapsed Hours": round(elapsed_hours_decimal, 2),
            "Elapsed Mins": int(elapsed_minutes),
            "Actual Bundles": int(actual_bundles),
            "Expected Bundles": int(expected_bundles),
            "Downtime Mins": int(downtime_minutes)
        }
        
        sync_success = send_data_to_google(new_entry)
        
        if "local_backup" not in st.session_state:
            st.session_state.local_backup = []
        st.session_state.local_backup.append(new_entry)
        
        st.success("Production metrics calculated and submitted successfully!")
        st.rerun()

# 6. Continuous Data Ledger
st.subheader("📊 Live Connected Production Database Ledger")
st.dataframe(combined_df, use_container_width=True, hide_index=True)

# Manager Dashboard controls
if st.session_state.user_role == "manager":
    st.subheader("🔐 Management Administrative Control Panel")
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        combined_df.to_excel(writer, index=False, sheet_name='Plant Overview Summary')
    
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        st.download_button(
            label="📥 Download Consolidated Report (.xlsx)",
            data=buffer.getvalue(),
            file_name="permanent_production_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with act_col2:
        if st.button("⚠️ Clear Session Ledger Cache", type="secondary", use_container_width=True):
            st.session_state.local_backup = []
            st.rerun()
