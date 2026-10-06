import streamlit as st

st.set_page_config(page_title="Downtime Calculator", page_icon="🏭", layout="centered")

st.title("🏭 Production Line Downtime Calculator")
st.write("Calculate your line's performance instantly based on standard capacity.")

# Inputs
elapsed_time = st.number_input("Total Elapsed Time (Minutes)", min_value=1, value=60, step=1)
actual_bundles = st.number_input("Actual Bundles Produced", min_value=0, value=10, step=1)

# Calculation
if st.button("Calculate Performance", type="primary"):
    expected_bundles = elapsed_time * 1.0 # 1 bundle per minute
    
    if actual_bundles > expected_bundles:
        st.error(f"❌ Error: Actual bundles ({actual_bundles}) cannot be greater than maximum capacity ({int(expected_bundles)}).")
    else:
        downtime = elapsed_time - actual_bundles
        efficiency = (actual_bundles / expected_bundles) * 100
        
        # Display Results
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Downtime", value=f"{int(downtime)} mins", delta="Downtime", delta_color="inverse")
        with col2:
            st.metric(label="Line Efficiency", value=f"{efficiency:.1f}%")
