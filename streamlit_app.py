import streamlit as st
import pandas as pd

st.title("📊 Production Shift Log & Downtime Calculator")

# Initialize session storage so data doesn't disappear when clicking buttons
if "history" not in st.session_state:
    st.session_state.history = []

# Inputs
line_name = st.text_input("Line Name / Number", value="Line 1")
elapsed_time = st.number_input("Elapsed Time (Minutes)", min_value=1, value=60)
actual_bundles = st.number_input("Actual Bundles", min_value=0, value=10)

if st.button("Log Submissions", type="primary"):
    expected = elapsed_time * 1.0
    if actual_bundles > expected:
        st.error("Invalid entry: Actual items exceed capacity.")
    else:
        downtime = elapsed_time - actual_bundles
        efficiency = (actual_bundles / expected) * 100
        
        # Add entry to history list
        st.session_state.history.append({
            "Line": line_name,
            "Elapsed Mins": elapsed_time,
            "Actual Bundles": actual_bundles,
            "Downtime Mins": downtime,
            "Efficiency %": f"{efficiency:.1f}%"
        })

# Show the history table if entries exist
if st.session_state.history:
    st.write("### Today's Production Log")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)
    
    # Simple clear button
    if st.button("Clear Log"):
        st.session_state.history = []
        st.rerun()

