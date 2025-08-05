#!/bin/bash
echo "🎯 Starting Grant Research Automation Dashboard..."
echo ""
echo "Dashboard will open in your default browser at http://localhost:8501"
echo "Press Ctrl+C to stop the dashboard"
echo ""

grant-research-env/Scripts/streamlit run src/dashboard/app.py --server.port 8501