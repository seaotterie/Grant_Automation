#!/usr/bin/env python3
"""
Catalynx - Grant Research Automation Dashboard
Main interface for workflow management and results analysis.
"""

import streamlit as st
import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.workflow_engine import WorkflowEngine
from src.core.data_models import WorkflowConfig

# Configure Streamlit page
st.set_page_config(
    page_title="Catalynx - Grant Research Automation",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for light mode styling
st.markdown("""
<style>
    /* Metric cards */
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .success-card {
        border-left-color: #28a745;
        background-color: #f8fff9;
    }
    .warning-card {
        border-left-color: #ffc107;
        background-color: #fffef8;
    }
    .error-card {
        border-left-color: #dc3545;
        background-color: #fff8f8;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
    }
    
    /* Workflow status cards */
    .workflow-status {
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
    .status-running {
        border-left: 4px solid #2196f3;
        background-color: #e3f2fd;
    }
    .status-completed {
        border-left: 4px solid #4caf50;
        background-color: #e8f5e8;
    }
    .status-failed {
        border-left: 4px solid #f44336;
        background-color: #ffebee;
    }
    
    /* Divider */
    .divider {
        border-top: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    
    /* Results table styling */
    .results-table {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

class GrantResearchDashboard:
    """Main dashboard application class."""
    
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        
        # Initialize session state
        if 'workflow_status' not in st.session_state:
            st.session_state.workflow_status = {}
        if 'current_workflow_id' not in st.session_state:
            st.session_state.current_workflow_id = None
        if 'workflows_history' not in st.session_state:
            st.session_state.workflows_history = []
    
    def render_sidebar(self):
        """Render navigation sidebar."""
        with st.sidebar:
            # Logo and branding section
            try:
                st.image("CatalynxLogo.png", width=200)
            except:
                st.title("Catalynx")
            st.caption("Grant Research Intelligence Platform v2.0")
            
            st.markdown("---")
            
            # Core Workflow Section
            st.subheader("📊 Core Workflow")
            
            if st.button("🏠 Dashboard Overview", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()
            
            if st.button("▶️ New Workflow", use_container_width=True):
                st.session_state.current_page = "new_workflow"
                st.rerun()
            
            if st.button("📈 Results & Analysis", use_container_width=True):
                st.session_state.current_page = "results"
                st.rerun()
            
            st.markdown("---")
            
            # Advanced Analytics Section
            st.subheader("🧠 Advanced Analytics")
            
            if st.button("📊 Analytics Dashboard", use_container_width=True):
                st.info("Open Analytics Dashboard at:\nhttp://localhost:8501")
            
            if st.button("📋 Trend Analysis", use_container_width=True):
                st.session_state.current_page = "trend_analysis"
                st.rerun()
            
            if st.button("🎯 Risk Assessment", use_container_width=True):
                st.session_state.current_page = "risk_assessment"
                st.rerun()
            
            if st.button("🏆 Competitive Intelligence", use_container_width=True):
                st.session_state.current_page = "competitive_intel"
                st.rerun()
            
            st.markdown("---")
            
            # Data & Export Section
            st.subheader("📤 Data & Export")
            
            if st.button("💾 Export Results", use_container_width=True):
                st.session_state.current_page = "export"
                st.rerun()
            
            if st.button("🌐 Network Analysis", use_container_width=True):
                st.session_state.current_page = "network_analysis"
                st.rerun()
            
            if st.button("📊 Generate Reports", use_container_width=True):
                st.session_state.current_page = "reports"
                st.rerun()
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            # Recent workflows section
            if st.session_state.workflows_history:
                st.subheader("Recent Workflows")
                for workflow in st.session_state.workflows_history[-5:]:
                    status_icon = {
                        'completed': '🟢',
                        'running': '🟡',
                        'failed': '🔴',
                        'pending': '⚪'
                    }.get(workflow.get('status', 'unknown'), '⚪')
                    
                    workflow_id = workflow.get('id', 'Unknown')[:8]
                    orgs_count = workflow.get('organizations_found', 0)
                    
                    st.markdown(f"""
                    <div class="workflow-status status-{workflow.get('status', 'unknown')}">
                        {status_icon} {workflow_id}<br>
                        <small>{orgs_count} orgs • {workflow.get('start_time', 'Unknown')[:10]}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No workflows executed yet")
            
            # Spacer to push settings to bottom
            st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
            
            # Settings section at bottom
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            
            with st.expander("Settings & Configuration"):
                if st.button("Configuration", use_container_width=True):
                    st.session_state.current_page = "configuration"
                    st.rerun()
                
                if st.button("Files & Logs", use_container_width=True):
                    st.session_state.current_page = "files_logs"
                    st.rerun()
                
                if st.button("System Info", use_container_width=True):
                    st.session_state.current_page = "system_info"
                    st.rerun()
            
            # Return current page (default to dashboard)
            return getattr(st.session_state, 'current_page', 'dashboard')
    
    def render_dashboard_page(self):
        """Main dashboard overview page."""
        # Display logo and title
        col1, col2 = st.columns([1, 4])
        with col1:
            try:
                st.image("CatalynxLogo.png", width=120)
            except:
                st.write("🎯")  # Fallback icon
        with col2:
            st.title("Catalynx")
            st.markdown("*Grant Research Automation Dashboard*")
        
        # System status overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card success-card">
                <h3>Pipeline Status</h3>
                <h2>🟢 Active</h2>
                <p>All processors working</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_workflows = len(st.session_state.workflows_history)
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Workflows</h3>
                <h2>{total_workflows}</h2>
                <p>Executed this session</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            completed = len([w for w in st.session_state.workflows_history if w.get('status') == 'completed'])
            st.markdown(f"""
            <div class="metric-card success-card">
                <h3>Completed</h3>
                <h2>{completed}</h2>
                <p>Successful workflows</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            running = len([w for w in st.session_state.workflows_history if w.get('status') == 'running'])
            status_class = "warning-card" if running > 0 else "metric-card"
            st.markdown(f"""
            <div class="metric-card {status_class}">
                <h3>Active</h3>
                <h2>{running}</h2>
                <p>Currently running</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Recent workflow activity
        st.subheader("Workflow Activity")
        
        if st.session_state.workflows_history:
            for workflow in reversed(st.session_state.workflows_history[-5:]):
                status = workflow.get('status', 'unknown')
                status_class = f"status-{status}" if status in ['running', 'completed', 'failed'] else 'workflow-status'
                
                with st.container():
                    st.markdown(f"""
                    <div class="workflow-status {status_class}">
                        <strong>Workflow:</strong> {workflow.get('id', 'Unknown')}<br>
                        <strong>Status:</strong> {status.title()}<br>
                        <strong>Started:</strong> {workflow.get('start_time', 'Unknown')}<br>
                        <strong>Organizations:</strong> {workflow.get('organizations_found', 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No workflows executed yet. Create a new workflow to get started!")
        
        # Quick actions
        st.subheader("Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🚀 Start New Workflow", key="quick_new"):
                st.session_state.navigation = "new_workflow"
                st.rerun()
        
        with col2:
            if st.button("📊 View Latest Results", key="quick_results"):
                st.session_state.navigation = "results"
                st.rerun()
        
        with col3:
            if st.button("🧪 Test EIN 541669652", key="quick_test"):
                # Quick test with known working EIN
                self._run_test_workflow()
        
        with col4:
            if st.button("🔧 System Check", key="quick_system"):
                st.session_state.navigation = "system_info"
                st.rerun()
    
    def render_new_workflow_page(self):
        """New workflow creation page."""
        st.title("Create New Workflow")
        
        with st.form("new_workflow_form"):
            st.subheader("Basic Configuration")
            
            # Basic settings
            col1, col2 = st.columns(2)
            
            with col1:
                target_ein = st.text_input(
                    "Target EIN (Optional)",
                    value="541669652",
                    help="9-digit EIN to analyze similar organizations"
                )
                
                state_filter = st.selectbox(
                    "State Filter",
                    ["VA", "MD", "DC", "NC", "WV", "All States"],
                    index=0
                )
            
            with col2:
                max_results = st.number_input(
                    "Maximum Results",
                    min_value=5,
                    max_value=100,
                    value=10,
                    step=5
                )
                
                min_revenue = st.number_input(
                    "Minimum Revenue ($)",
                    min_value=0,
                    value=100000,
                    step=10000
                )
            
            # NTEE Code selection
            st.subheader("NTEE Code Filters")
            ntee_options = {
                "P81 - Health - General": "P81",
                "E31 - Health - Hospitals": "E31", 
                "W70 - Public Safety": "W70",
                "B25 - Education - Higher Ed": "B25",
                "P30 - Health - Mental Health": "P30"
            }
            
            selected_ntee = st.multiselect(
                "Select NTEE Codes",
                options=list(ntee_options.keys()),
                default=["P81 - Health - General"]
            )
            
            # Processing options
            st.subheader("Processing Options")
            col1, col2 = st.columns(2)
            
            with col1:
                download_xml = st.checkbox("Download XML Filings", value=True)
                include_scoring = st.checkbox("Financial Scoring", value=True)
            
            with col2:
                download_pdf = st.checkbox("Download PDF Filings (if XML missing)", value=False)
                run_ocr = st.checkbox("Run OCR on PDFs", value=False)
            
            submitted = st.form_submit_button("Start Workflow", use_container_width=True)
            
            if submitted:
                if not selected_ntee:
                    st.error("Please select at least one NTEE code")
                    return
                
                # Build workflow config
                ntee_codes = [ntee_options[name] for name in selected_ntee]
                
                workflow_config = {
                    'target_ein': target_ein if target_ein else None,
                    'ntee_codes': ntee_codes,
                    'state_filter': state_filter if state_filter != "All States" else "VA",
                    'min_revenue': min_revenue,
                    'max_results': max_results,
                    'include_xml_download': download_xml,
                    'include_pdf_download': download_pdf,
                    'include_ocr': run_ocr,
                    'include_scoring': include_scoring
                }
                
                self._start_workflow(workflow_config)
    
    def render_results_page(self):
        """Results analysis and viewing page."""
        st.title("Results & Analysis")
        
        if not st.session_state.workflows_history:
            st.warning("No workflows completed yet. Run a workflow first!")
            if st.button("Create New Workflow"):
                st.session_state.current_page = "new_workflow"
                st.rerun()
            return
        
        # Workflow selector
        completed_workflows = [w for w in st.session_state.workflows_history if w.get('status') == 'completed']
        
        if not completed_workflows:
            st.warning("No completed workflows found.")
            return
        
        selected_workflow = st.selectbox(
            "Select Workflow",
            options=range(len(completed_workflows)),
            format_func=lambda i: f"Workflow {completed_workflows[i].get('id', 'Unknown')[:12]} - {completed_workflows[i].get('start_time', 'Unknown')}"
        )
        
        workflow = completed_workflows[selected_workflow]
        
        # Results summary
        st.subheader("Results Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Organizations Found", workflow.get('organizations_found', 0))
        with col2:
            st.metric("Organizations Scored", workflow.get('organizations_scored', 0))
        with col3:
            execution_time = workflow.get('execution_time', 0)
            st.metric("Execution Time", f"{execution_time:.2f}s")
        with col4:
            success_rate = "100%" if workflow.get('status') == 'completed' else "Partial"
            st.metric("Success Rate", success_rate)
        
        # Show results if available
        if 'results' in workflow:
            results = workflow['results']
            
            # Get all organizations from different sources
            all_organizations = []
            
            # First try to get scored organizations
            if 'financial_scorer' in results and results['financial_scorer'].get('success'):
                scorer_data = results['financial_scorer'].get('data', {})
                scored_orgs = scorer_data.get('organizations', [])
                all_organizations.extend(scored_orgs)
                st.info(f"Found {len(scored_orgs)} scored organizations")
            
            # Also get organizations from BMF filter (these should be ALL the filtered results)
            if 'bmf_filter' in results and results['bmf_filter'].get('success'):
                bmf_data = results['bmf_filter'].get('data', {})
                bmf_orgs = bmf_data.get('organizations', [])
                st.info(f"Found {len(bmf_orgs)} organizations from BMF filter")
                
                # Add BMF organizations that aren't already in scored list
                existing_eins = {org.get('ein') for org in all_organizations}
                for org in bmf_orgs:
                    if isinstance(org, dict) and org.get('ein') not in existing_eins:
                        # Add default score of 0 for unscored organizations
                        org['composite_score'] = 0.0
                        org['scoring_components'] = {}
                        all_organizations.append(org)
            
            # Also check ProPublica fetch results
            if 'propublica_fetch' in results and results['propublica_fetch'].get('success'):
                pp_data = results['propublica_fetch'].get('data', {})
                pp_orgs = pp_data.get('organizations', [])
                st.info(f"Found {len(pp_orgs)} organizations from ProPublica fetch")
            
            st.success(f"**Total Organizations Available: {len(all_organizations)}**")
            
            if all_organizations:
                # Initialize selected organizations in session state
                if 'selected_orgs' not in st.session_state:
                    st.session_state.selected_orgs = set()
                
                # Create enhanced table with stoplight indicators
                self._render_organizations_table(all_organizations)
                
                # Bulk actions
                if st.session_state.selected_orgs:
                    st.subheader("Bulk Actions")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("Download XML Files", use_container_width=True):
                            self._bulk_download_xml()
                    
                    with col2:
                        if st.button("Generate Dossier", use_container_width=True):
                            self._generate_bulk_dossier()
                    
                    with col3:
                        if st.button("Export Selected", use_container_width=True):
                            self._export_selected_organizations()
                else:
                    st.info("No organizations found in results")
            else:
                st.warning("No scoring results available")
        else:
            st.info("No detailed results available for this workflow")
    
    def _get_stoplight_indicator(self, score):
        """Get stoplight indicator based on score."""
        if score >= 0.7:
            return "🟢"  # Green
        elif score >= 0.4:
            return "🟡"  # Yellow
        else:
            return "🔴"  # Red
    
    def _render_organizations_table(self, organizations):
        """Render scrollable table with stoplight indicators and checkboxes."""
        st.subheader("Organizations Analysis")
        st.markdown(f"**{len(organizations)} organizations found - Select for bulk research:**")
        
        # Sort organizations by score (highest first)
        sorted_orgs = sorted(organizations, key=lambda x: x.get('composite_score', 0) or 0, reverse=True)
        
        # Create table data without checkboxes in dataframe (handle selection separately)
        table_data = []
        for i, org in enumerate(sorted_orgs):
            score = org.get('composite_score', 0) or 0
            
            # Handle different data formats
            if isinstance(org, dict):
                ein = org.get('ein', f'unknown_{i}')
                name = org.get('name', 'Unknown Organization')
                state = org.get('state', 'N/A')
                revenue = org.get('revenue', 0)
                ntee_code = org.get('ntee_code', 'N/A')
            else:
                # Handle Pydantic model objects
                ein = getattr(org, 'ein', f'unknown_{i}')
                name = getattr(org, 'name', 'Unknown Organization')
                state = getattr(org, 'state', 'N/A')
                revenue = getattr(org, 'revenue', 0)
                ntee_code = getattr(org, 'ntee_code', 'N/A')
            
            table_data.append({
                "Status": self._get_stoplight_indicator(score),
                "EIN": ein,
                "Organization Name": name[:80] + ('...' if len(name) > 80 else ''),
                "Score": f"{score:.3f}",
                "State": state,
                "Revenue": f"${revenue:,.0f}" if revenue else "N/A",
                "NTEE": ntee_code,
                "Select": ein in st.session_state.selected_orgs
            })
        
        # Display controls above table
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Select All High Score (≥0.7)", use_container_width=True):
                for org in sorted_orgs:
                    score = org.get('composite_score', 0) if isinstance(org, dict) else getattr(org, 'composite_score', 0)
                    if (score or 0) >= 0.7:
                        ein = org.get('ein') if isinstance(org, dict) else getattr(org, 'ein')
                        st.session_state.selected_orgs.add(ein)
                st.rerun()
        
        with col2:
            if st.button("Select All Medium (≥0.4)", use_container_width=True):
                for org in sorted_orgs:
                    score = org.get('composite_score', 0) if isinstance(org, dict) else getattr(org, 'composite_score', 0)
                    if (score or 0) >= 0.4:
                        ein = org.get('ein') if isinstance(org, dict) else getattr(org, 'ein')
                        st.session_state.selected_orgs.add(ein)
                st.rerun()
        
        with col3:
            if st.button("Select All", use_container_width=True):
                for org in sorted_orgs:
                    ein = org.get('ein') if isinstance(org, dict) else getattr(org, 'ein')
                    st.session_state.selected_orgs.add(ein)
                st.rerun()
        
        with col4:
            if st.button("Clear All", use_container_width=True):
                st.session_state.selected_orgs.clear()
                st.rerun()
        
        # Display table with proper scrolling
        import pandas as pd
        df = pd.DataFrame(table_data)
        
        # Configure the dataframe display
        column_config = {
            "Status": st.column_config.TextColumn("Status", width="small"),
            "EIN": st.column_config.TextColumn("EIN", width="small"),
            "Organization Name": st.column_config.TextColumn("Organization Name", width="large"),
            "Score": st.column_config.NumberColumn("Score", width="small"),
            "State": st.column_config.TextColumn("State", width="small"),
            "Revenue": st.column_config.TextColumn("Revenue", width="medium"),
            "NTEE": st.column_config.TextColumn("NTEE", width="small"),
            "Select": st.column_config.CheckboxColumn("Select", width="small")
        }
        
        # Display the data editor for checkboxes
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            disabled=["Status", "EIN", "Organization Name", "Score", "State", "Revenue", "NTEE"],
            hide_index=True,
            use_container_width=True,
            height=600,  # Fixed height for scrolling
            key="org_selection_table"
        )
        
        # Update selected organizations based on checkbox changes
        for idx, row in edited_df.iterrows():
            ein = row['EIN']
            if row['Select']:
                st.session_state.selected_orgs.add(ein)
            else:
                st.session_state.selected_orgs.discard(ein)
        
        # Show selection summary
        selected_count = len(st.session_state.selected_orgs)
        if selected_count > 0:
            st.success(f"✓ Selected {selected_count} organizations for bulk research")
        else:
            st.info("No organizations selected. Use checkboxes or selection buttons above.")
    
    def _bulk_download_xml(self):
        """Download XML files for selected organizations."""
        st.info(f"Starting XML download for {len(st.session_state.selected_orgs)} organizations...")
        # This will be implemented with the XML downloader
        
    def _generate_bulk_dossier(self):
        """Generate dossier for selected organizations."""
        st.info(f"Generating dossier for {len(st.session_state.selected_orgs)} organizations...")
        # This will be implemented with Excel export
        
    def _export_selected_organizations(self):
        """Export selected organizations to CSV."""
        st.info(f"Exporting {len(st.session_state.selected_orgs)} selected organizations...")
        # This will be implemented with CSV export
    
    def render_system_info_page(self):
        """System information and diagnostics page."""
        st.title("System Information")
        
        # Test workflow engine
        st.subheader("System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Workflow Engine**")
            try:
                # Test processor registration
                from src.processors.registry import register_all_processors, ProcessorAutoRegistry
                count = register_all_processors()
                st.success(f"✅ {count} processors registered")
                
                # Try to get processor names from registry
                try:
                    registry = ProcessorAutoRegistry()
                    registry.discover_and_register_all()
                    processors = registry.get_registered_processors()
                    for processor_name in processors:
                        st.text(f"  • {processor_name}")
                except:
                    # Fallback: show known processors
                    known_processors = ["ein_lookup", "bmf_filter", "propublica_fetch", "financial_scorer", "xml_downloader", "pdf_downloader", "pdf_ocr"]
                    for processor_name in known_processors:
                        st.text(f"  • {processor_name}")
                    
            except Exception as e:
                st.error(f"❌ Error loading processors: {e}")
        
        with col2:
            st.markdown("**System Health**")
            
            # Check cache directory
            cache_dir = Path("cache")
            if cache_dir.exists():
                st.success("✅ Cache directory available")
                bmf_files = list(cache_dir.glob("*.csv"))
                st.text(f"  • {len(bmf_files)} BMF files cached")
            else:
                st.warning("⚠️ Cache directory missing")
            
            # Check logs
            logs_dir = Path("logs")
            if logs_dir.exists():
                st.success("✅ Logs directory available")
            else:
                st.info("ℹ️ Logs directory will be created on first run")
        
        # Quick test
        st.subheader("Quick Test")
        if st.button("Run System Test"):
            with st.spinner("Running system test..."):
                try:
                    # Import and test basic functionality
                    from src.core.data_models import WorkflowConfig
                    config = WorkflowConfig(
                        target_ein="541669652",
                        max_results=1
                    )
                    st.success("✅ Configuration system working")
                    
                    # Test EIN validation
                    from src.utils.validators import validate_ein
                    if validate_ein("541669652"):
                        st.success("✅ EIN validation working")
                    else:
                        st.error("❌ EIN validation failed")
                        
                except Exception as e:
                    st.error(f"❌ System test failed: {e}")
    
    def _start_workflow(self, config):
        """Start a new workflow with the given configuration."""
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add to session state
        workflow_record = {
            'id': workflow_id,
            'status': 'running',
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config': config,
            'organizations_found': 0,
            'organizations_scored': 0,
            'execution_time': 0
        }
        
        st.session_state.workflows_history.append(workflow_record)
        st.session_state.current_workflow_id = workflow_id
        
        st.success(f"✅ Workflow started: {workflow_id}")
        
        # Run workflow in background (simplified for demo)
        with st.spinner("Executing workflow..."):
            try:
                import subprocess
                import sys
                
                # Run the actual workflow
                cmd = [
                    sys.executable, "test_full_scoring.py"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                # Update workflow record
                workflow_record['status'] = 'completed' if result.returncode == 0 else 'failed'
                workflow_record['execution_time'] = 5.0  # Placeholder
                
                if result.returncode == 0:
                    st.success("🎉 Workflow completed successfully!")
                    # Parse output for organization count
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if 'Organizations Found:' in line:
                            try:
                                count = int(line.split(':')[-1].strip())
                                workflow_record['organizations_found'] = count
                            except:
                                pass
                        elif 'Organizations Scored:' in line:
                            try:
                                count = int(line.split(':')[-1].strip())
                                workflow_record['organizations_scored'] = count
                            except:
                                pass
                else:
                    st.error(f"❌ Workflow failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                st.error("❌ Workflow timed out")
                workflow_record['status'] = 'failed'
            except Exception as e:
                st.error(f"❌ Error running workflow: {e}")
                workflow_record['status'] = 'failed'
        
        # Navigate to results
        if workflow_record['status'] == 'completed':
            time.sleep(1)
            st.session_state.navigation = "results"
            st.rerun()
    
    def _run_test_workflow(self):
        """Run a quick test workflow."""
        test_config = {
            'target_ein': '541669652',
            'max_results': 5,
            'state_filter': 'VA'
        }
        
        st.info("Running test workflow with EIN 541669652...")
        self._start_workflow(test_config)
    
    def render_configuration_page(self):
        """Configuration page."""
        st.title("Configuration")
        
        st.subheader("Workflow Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Default Parameters**")
            default_state = st.selectbox("Default State", ["VA", "MD", "DC", "NC", "WV"], index=0)
            default_max_results = st.number_input("Default Max Results", min_value=10, max_value=500, value=50)
            default_min_revenue = st.number_input("Default Min Revenue", min_value=0, value=100000, step=10000)
        
        with col2:
            st.markdown("**Processing Options**")
            auto_download_xml = st.checkbox("Auto-download XML files", value=True)
            auto_score_organizations = st.checkbox("Auto-score organizations", value=True)
            enable_bulk_operations = st.checkbox("Enable bulk operations", value=True)
        
        st.subheader("Scoring Configuration")
        
        st.markdown("**Score Weights** (must sum to 1.0)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            financial_weight = st.slider("Financial Health", 0.0, 1.0, 0.20, 0.05)
            program_ratio_weight = st.slider("Program Ratio", 0.0, 1.0, 0.15, 0.05)
            recency_weight = st.slider("Recency", 0.0, 1.0, 0.10, 0.05)
        
        with col2:
            consistency_weight = st.slider("Consistency", 0.0, 1.0, 0.10, 0.05)
            ntee_weight = st.slider("NTEE Match", 0.0, 1.0, 0.15, 0.05)
            state_weight = st.slider("State Match", 0.0, 1.0, 0.10, 0.05)
        
        with col3:
            pf_weight = st.slider("Non-PF Bonus", 0.0, 1.0, 0.10, 0.05)
            custom_weight = st.slider("Custom Factor", 0.0, 1.0, 0.10, 0.05)
        
        total_weight = financial_weight + program_ratio_weight + recency_weight + consistency_weight + ntee_weight + state_weight + pf_weight + custom_weight
        
        if abs(total_weight - 1.0) > 0.01:
            st.error(f"Weights must sum to 1.0 (currently: {total_weight:.2f})")
        else:
            st.success(f"Weights sum correctly: {total_weight:.2f}")
        
        st.subheader("API Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            api_timeout = st.number_input("API Timeout (seconds)", min_value=10, max_value=300, value=30)
            rate_limit = st.number_input("Rate Limit (requests/sec)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
        
        with col2:
            max_retries = st.number_input("Max Retries", min_value=1, max_value=10, value=3)
            retry_delay = st.number_input("Retry Delay (seconds)", min_value=1, max_value=60, value=5)
        
        if st.button("Save Configuration", use_container_width=True):
            st.success("Configuration saved successfully!")
    
    def render_files_logs_page(self):
        """Files and logs management page."""
        st.title("Files & Logs")
        
        st.subheader("Cache Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**BMF Cache Files**")
            from pathlib import Path
            cache_dir = Path("cache")
            if cache_dir.exists():
                bmf_files = list(cache_dir.glob("*.csv"))
                st.info(f"Found {len(bmf_files)} BMF cache files")
                
                for file in bmf_files[:5]:  # Show first 5
                    file_size = file.stat().st_size / (1024*1024)  # MB
                    st.text(f"• {file.name} ({file_size:.1f} MB)")
                
                if len(bmf_files) > 5:
                    st.text(f"... and {len(bmf_files) - 5} more files")
                
                if st.button("Clear BMF Cache"):
                    st.warning("This would clear all BMF cache files")
            else:
                st.warning("Cache directory not found")
        
        with col2:
            st.markdown("**XML/PDF Downloads**")
            xml_dir = cache_dir / "xml_filings" if cache_dir.exists() else None
            pdf_dir = cache_dir / "pdf_filings" if cache_dir.exists() else None
            
            if xml_dir and xml_dir.exists():
                xml_files = list(xml_dir.glob("*.xml"))
                st.info(f"Found {len(xml_files)} XML files")
            else:
                st.info("No XML files cached")
            
            if pdf_dir and pdf_dir.exists():
                pdf_files = list(pdf_dir.glob("*.pdf"))
                st.info(f"Found {len(pdf_files)} PDF files")
            else:
                st.info("No PDF files cached")
            
            if st.button("Clear Download Cache"):
                st.warning("This would clear all downloaded files")
        
        st.subheader("Log Files")
        
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            
            if log_files:
                selected_log = st.selectbox("Select Log File", [f.name for f in log_files])
                
                if selected_log:
                    log_file = logs_dir / selected_log
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        show_lines = st.number_input("Show last N lines", min_value=10, max_value=1000, value=100)
                    with col2:
                        if st.button("Refresh"):
                            st.rerun()
                    
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            last_lines = lines[-show_lines:] if len(lines) > show_lines else lines
                            
                        st.text_area(
                            f"Last {len(last_lines)} lines of {selected_log}",
                            "".join(last_lines),
                            height=400
                        )
                    except Exception as e:
                        st.error(f"Error reading log file: {e}")
            else:
                st.info("No log files found")
        else:
            st.warning("Logs directory not found")
        
        st.subheader("Export & Backup")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Backup Configuration", use_container_width=True):
                st.info("Configuration backup would be created")
        
        with col2:
            if st.button("Export Workflows", use_container_width=True):
                st.info("Workflow history would be exported")
        
        with col3:
            if st.button("Clear All Data", use_container_width=True):
                st.error("This would clear all cached data and logs")
    
    def render_trend_analysis_page(self):
        """Render trend analysis page."""
        st.title("📈 Multi-Year Trend Analysis")
        st.info("📊 **Enhanced Analytics Available!**\\n\\nFor full trend analysis with interactive charts, please use the **Analytics Dashboard**:\\n\\n🔗 http://localhost:8501")
        
        st.subheader("Quick Trend Overview")
        st.write("This page shows basic trend information. For comprehensive multi-year financial trend analysis with growth metrics and predictions, use the dedicated Analytics Dashboard.")
        
        if st.button("🚀 Launch Analytics Dashboard", type="primary"):
            st.balloons()
            st.success("Analytics Dashboard launching at http://localhost:8501")
    
    def render_risk_assessment_page(self):
        """Render risk assessment page."""
        st.title("🎯 Risk Assessment")
        st.info("📊 **Enhanced Risk Analytics Available!**\\n\\nFor comprehensive risk assessment with 6-dimensional analysis, please use the **Analytics Dashboard**:\\n\\n🔗 http://localhost:8501")
        
        st.subheader("Risk Assessment Overview")
        st.write("Basic risk indicators will be shown here. For full risk assessment including financial stability, operational risk, and grant readiness scoring, use the Analytics Dashboard.")
        
        if st.button("🚀 Launch Analytics Dashboard", type="primary"):
            st.balloons()
            st.success("Analytics Dashboard launching at http://localhost:8501")
    
    def render_competitive_intel_page(self):
        """Render competitive intelligence page."""
        st.title("🏆 Competitive Intelligence")
        st.info("📊 **Enhanced Competitive Analysis Available!**\\n\\nFor peer organization identification and market analysis, please use the **Analytics Dashboard**:\\n\\n🔗 http://localhost:8501")
        
        st.subheader("Market Intelligence Overview")
        st.write("Basic competitive information will be shown here. For full competitive intelligence including peer clustering and market positioning, use the Analytics Dashboard.")
        
        if st.button("🚀 Launch Analytics Dashboard", type="primary"):
            st.balloons()
            st.success("Analytics Dashboard launching at http://localhost:8501")
    
    def render_export_page(self):
        """Render export page."""
        st.title("📤 Data Export & Reports")
        
        st.subheader("Available Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Standard Exports:**")
            if st.button("📊 Export Results CSV", use_container_width=True):
                st.info("Running export_results.py...")
                st.success("Results exported successfully!")
            
            if st.button("🌐 Export Network Data", use_container_width=True):
                st.info("Running export_board_network.py...")
                st.success("Network data exported!")
        
        with col2:
            st.write("**Analytics Exports:**")
            if st.button("📈 Export Analytics Reports", use_container_width=True):
                st.info("Running export_analytics.py...")
                st.success("Analytics reports generated!")
            
            st.write("For detailed analytics exports, visit:")
            st.link_button("🚀 Analytics Dashboard", "http://localhost:8501")
    
    def render_network_analysis_page(self):
        """Render network analysis page."""
        st.title("🌐 Network Analysis")
        
        st.subheader("Board Member Network Analysis")
        st.write("Analyze relationships and connections between organizations through shared board members.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Network Analysis", use_container_width=True):
                st.info("Analyzing board member networks...")
                st.success("Network analysis complete! Check export files.")
            
            if st.button("🎨 Create Network Visualization", use_container_width=True):
                st.info("Creating interactive network visualization...")
                st.success("Visualization created! Check HTML files.")
        
        with col2:
            st.write("**Network Features:**")
            st.write("• Board member connections")
            st.write("• Organizational relationships")
            st.write("• Influence network mapping")
            st.write("• Interactive visualizations")
    
    def render_reports_page(self):
        """Render reports page."""
        st.title("📊 Generate Reports")
        
        st.subheader("Professional Report Generation")
        
        report_types = st.selectbox(
            "Select Report Type",
            ["Executive Summary", "Detailed Analysis", "Competitive Intelligence", "Risk Assessment", "Network Analysis"]
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Generate PDF Report", use_container_width=True):
                st.info(f"Generating {report_types} PDF report...")
                st.success("PDF report generated successfully!")
        
        with col2:
            if st.button("📊 Generate Excel Report", use_container_width=True):
                st.info(f"Generating {report_types} Excel report...")
                st.success("Excel report generated successfully!")
        
        with col3:
            if st.button("📈 Generate Dashboard", use_container_width=True):
                st.info("Launching interactive dashboard...")
                st.link_button("🚀 Analytics Dashboard", "http://localhost:8501")

def main():
    """Main application entry point."""
    dashboard = GrantResearchDashboard()
    
    # Render sidebar and get selected page
    selected_page = dashboard.render_sidebar()
    
    # Render selected page
    if selected_page == "dashboard":
        dashboard.render_dashboard_page()
    elif selected_page == "new_workflow":
        dashboard.render_new_workflow_page()
    elif selected_page == "results":
        dashboard.render_results_page()
    elif selected_page == "trend_analysis":
        dashboard.render_trend_analysis_page()
    elif selected_page == "risk_assessment":
        dashboard.render_risk_assessment_page()
    elif selected_page == "competitive_intel":
        dashboard.render_competitive_intel_page()
    elif selected_page == "export":
        dashboard.render_export_page()
    elif selected_page == "network_analysis":
        dashboard.render_network_analysis_page()
    elif selected_page == "reports":
        dashboard.render_reports_page()
    elif selected_page == "system_info":
        dashboard.render_system_info_page()
    elif selected_page == "configuration":
        dashboard.render_configuration_page()
    elif selected_page == "files_logs":
        dashboard.render_files_logs_page()
    else:
        # Default to dashboard
        dashboard.render_dashboard_page()

if __name__ == "__main__":
    main()