import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Secure Production Log", page_icon="🏭", layout="wide")

# 1. Define authorized user accounts and roles
USER_CREDENTIALS = {
    "operator1": {"password": "Pa55w.rd", "role": "operator"},
    "manager1": {"password": "Pa55w.rd", "role": "manager"}
}

# 2. Initialize necessary session state keys
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "production_log" not in st.session_state:
    st.session_state.production_log = []

# 3. Authentication Interface (Login Screen)
if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center;'>🏭 Plant Control Login Portal</h2>", unsafe_allow_html=True)
    
    with st.form("Login Form", clear_on_submit=False):
        username_input = st.text_input("Username").strip().lower()
        password_input = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Log In", type="primary")
        
        if submit_login:
            if username_input in USER_CREDENTIALS and USER_CREDENTIALS[username_input]["password"] == password_input:
                st.session_state.authenticated = True
                st.session_state.username = username_input
                st.session_state.user_role = USER_CREDENTIALS[username_input]["role"]
                st.success("Successfully logged in!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
    st.stop()  # Completely stops execution here if not authenticated

# --- AUTHORIZED AREA (If code reaches here, user is logged in) ---

# Top Header Bar with Logout Option
header_col1, header_col2 = st.columns([5, 1])
with header_col1:
    st.title("🏭 Secure Production & Downtime Dashboard")
    st.caption(f"Logged in as: **{st.session_state.username.upper()}** | Role: **{st.session_state.user_role.capitalize()}**")
with header_col2:
    if st.button("Log Out", type="secondary"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.user_role = ""
        st.rerun()

st.divider()

# 4. Calculator Input Form (Accessible to Operators and Managers)
st.subheader("📥 Log New Shift Performance Data")
col_input1, col_input2 = st.columns(2)

with col_input1:
    line_name = st.selectbox("Select Production Line", options=["CP01", "CP02", "CP03", "CP04"])
    shift_name = st.selectbox("Select Shift", options=["A", "B", "C", "D"])

with col_input2:
    elapsed_hours = st.number_input("Elapsed Time (Hours)", min_value=0.1, value=1.0, step=0.5, format="%.2f")
    actual_bundles = st.number_input("Actual Bundles Produced", min_value=0, value=10, step=1)

if st.button("Submit & Calculate Data", type="primary"):
    elapsed_minutes = elapsed_hours * 60.0
    expected_bundles = elapsed_minutes * 1.0  # 1 bundle/minute standard
    
    if actual_bundles > expected_bundles:
        st.error(f"❌ Error: Actual bundles ({actual_bundles}) cannot exceed capacity ({int(expected_bundles)} bundles for {elapsed_hours} hours).")
    else:
        downtime_minutes = elapsed_minutes - actual_bundles
        efficiency = (actual_bundles / expected_bundles) * 100
        
        st.session_state.production_log.append({
            "Line": line_name,
            "Shift": shift_name,
            "Logged By": st.session_state.username,
            "Elapsed Hours": elapsed_hours,
            "Elapsed Mins": int(elapsed_minutes),
            "Actual Bundles": actual_bundles,
            "Expected Bundles": int(expected_bundles),
            "Downtime Mins": int(downtime_minutes),
            "Efficiency (%)": round(efficiency, 1)
        })
        st.success("Entry securely logged to the temporary data matrix!")

# 5. Restricted Data Display & Actions
if st.session_state.production_log:
    st.divider()
    st.subheader("📊 Current Production Log Matrix")
    
    df = pd.DataFrame(st.session_state.production_log)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # MANAGER-ONLY SECTION: Summary Metrics, Download, and Clear Functions
    if st.session_state.user_role == "manager":
        st.subheader("🔐 Management Administrative Control Panel")
        
        sum_col1, sum_col2, sum_col3 = st.columns(3)
        total_hours = df["Elapsed Hours"].sum()
        total_bundles = df["Actual Bundles"].sum()
        total_downtime = df["Downtime Mins"].sum()
        total_expected = df["Expected Bundles"].sum()
        overall_efficiency = (total_bundles / total_expected) * 100 if total_expected > 0 else 0
        
        with sum_col1:
            st.metric(label="Total Tracked Operating Time", value=f"{total_hours:.1f} Hours")
        with sum_col2:
            st.metric(label="Total Downtime Registered", value=f"{int(total_downtime)} Minutes", delta="-🔴")
        with sum_col3:
            st.metric(label="Overall Plant Efficiency", value=f"{overall_efficiency:.1f}%")
            
        # Export Workbook Setup
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Plant Overview Summary')
        
        # Action Buttons
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            st.download_button(
                label="📥 Download Data Report (.xlsx)",
                data=buffer.getvalue(),
                file_name="secure_production_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with act_col2:
            if st.button("⚠️ Clear Data Log Permanently", type="secondary", use_container_width=True):
                st.session_state.production_log = []
                st.rerun()
    else:
        # What operators see if data exists but they aren't authorized to modify/extract it
        st.info("🔒 Summary metrics and data extraction features are restricted to Management accounts.")


