#!/usr/bin/env python3
"""
Minimal Test Dashboard - Isolate the issue
"""

import streamlit as st

# Configure page
st.set_page_config(
    page_title="Catalynx - Test",
    page_icon="🎯",
    layout="wide"
)

def main():
    st.title("🎯 Catalynx - Minimal Test Dashboard")
    st.write("If you can see this, the basic dashboard is working!")
    
    with st.sidebar:
        st.title("Test Navigation")
        if st.button("Home"):
            st.write("Home clicked!")
        if st.button("Test"):
            st.write("Test clicked!")
    
    st.subheader("System Status")
    st.success("✅ Dashboard is loading correctly")
    
    st.subheader("Available Commands")
    st.code("""
# Intelligent Classification
python main.py classify-organizations --detailed --max-results 100

# Enhanced Workflow
python main.py run-workflow --include-classified --classification-score-threshold 0.5

# Export Results  
python export_classification_results.py --min-score 0.3
    """)

if __name__ == "__main__":
    main()