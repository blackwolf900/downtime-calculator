import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Production Downtime Calculator", page_icon="🏭", layout="wide")

st.title("🏭 Production Line Shift Log & Downtime Calculator")
st.write("Track line efficiency, calculate downtime, and export shift metrics directly to Excel.")

# 1. Initialize session storage for persistent data tracking
if "production_log" not in st.session_state:
    st.session_state.production_log = []

# 2. Layout columns for user inputs
col_input1, col_input2 = st.columns(2)

with col_input1:
    line_name = st.selectbox("Select Production Line", options=["CP01", "CP02", "CP03", "CP04"])
    shift_name = st.selectbox("Select Shift", options=["A", "B", "C", "D"])

with col_input2:
    elapsed_hours = st.number_input("Elapsed Time (Hours)", min_value=0.1, value=1.0, step=0.5, format="%.2f")
    actual_bundles = st.number_input("Actual Bundles Produced", min_value=0, value=10, step=1)

# 3. Form processing logic on button click
if st.button("Log Entry & Calculate", type="primary"):
    # Convert hours to minutes for the underlying calculation
    elapsed_minutes = elapsed_hours * 60.0
    
    # Baseline capability: 1 bundle every minute
    expected_bundles = elapsed_minutes * 1.0 
    
    if actual_bundles > expected_bundles:
        st.error(f"❌ Error: Actual bundles ({actual_bundles}) cannot exceed maximum capacity ({int(expected_bundles)} bundles for {elapsed_hours} hours).")
    else:
        # Calculate downtime and shift performance metrics
        downtime_minutes = elapsed_minutes - actual_bundles
        efficiency = (actual_bundles / expected_bundles) * 100
        
        # Save entry dictionary to session memory
        st.session_state.production_log.append({
            "Line": line_name,
            "Shift": shift_name,
            "Elapsed Hours": elapsed_hours,
            "Elapsed Mins": int(elapsed_minutes),
            "Actual Bundles": actual_bundles,
            "Expected Bundles": int(expected_bundles),
            "Downtime Mins": int(downtime_minutes),
            "Efficiency (%)": round(efficiency, 1)
        })
        st.success("Entry successfully logged below!")

# 4. History Table and Reporting Dashboard
if st.session_state.production_log:
    st.divider()
    st.subheader("📊 Active Production History Log")
    
    # Construct a working dataframe from recorded data
    df = pd.DataFrame(st.session_state.production_log)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 5. Summary Metrics Aggregation
    st.subheader("📈 Summary Report Metrics")
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
        
    # 6. Streamlit Binary Excel Exporter
    # Build excel file straight into an in-memory byte buffer
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Downtime Summary')
    
    # Download Button Trigger
    st.download_button(
        label="📥 Download Summary Report (.xlsx)",
        data=buffer.getvalue(),
        file_name="production_downtime_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Optional wipe option
    if st.button("Clear Log Data"):
        st.session_state.production_log = []
        st.invalidate_all() if hasattr(st, "invalidate_all") else st.rerun()

