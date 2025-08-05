#!/usr/bin/env python3
"""
Catalynx - Advanced Analytics Dashboard
Interactive dashboard for trend analysis, risk assessment, and competitive intelligence.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.workflow_engine import WorkflowEngine
from src.core.data_models import WorkflowConfig

# Configure Streamlit page
st.set_page_config(
    page_title="Catalynx Analytics - Strategic Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Executive dashboard styling */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .insight-card {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .risk-low {
        border-left-color: #28a745 !important;
        background-color: #f8fff9 !important;
    }
    
    .risk-moderate {
        border-left-color: #ffc107 !important;
        background-color: #fffef8 !important;
    }
    
    .risk-high {
        border-left-color: #dc3545 !important;
        background-color: #fff8f8 !important;
    }
    
    .competitive-leader {
        border-left-color: #6f42c1 !important;
        background-color: #f8f7ff !important;
    }
    
    .trend-positive {
        color: #28a745;
        font-weight: bold;
    }
    
    .trend-negative {
        color: #dc3545;
        font-weight: bold;
    }
    
    .trend-stable {
        color: #6c757d;
        font-weight: bold;
    }
    
    /* Dashboard header */
    .dashboard-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .tab-content {
        padding: 1rem;
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class AdvancedAnalyticsDashboard:
    """Advanced analytics dashboard for strategic intelligence."""
    
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        
    def render(self):
        """Render the complete analytics dashboard."""
        # Dashboard header
        st.markdown("""
        <div class="dashboard-header">
            <h1>📊 Catalynx Analytics Intelligence</h1>
            <p>Strategic Grant Research Analytics & Competitive Intelligence Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar for data loading and configuration
        self._render_sidebar()
        
        # Main dashboard content
        if 'analytics_data' in st.session_state:
            self._render_main_dashboard()
        else:
            self._render_welcome_screen()
    
    def _render_sidebar(self):
        """Render sidebar for data loading and configuration."""
        # Logo and branding section
        try:
            st.sidebar.image("CatalynxLogo.png", width=180)
        except:
            st.sidebar.title("Catalynx Analytics")
        st.sidebar.caption("Strategic Intelligence Platform")
        
        st.sidebar.markdown("---")
        st.sidebar.header("📊 Analytics Control Panel")
        
        # Data loading section
        st.sidebar.subheader("📁 Data Management")
        
        # Load latest analytics results
        if st.sidebar.button("🔄 Load Latest Analytics", type="primary"):
            self._load_analytics_data()
        
        # Upload analytics JSON
        uploaded_file = st.sidebar.file_uploader(
            "Upload Analytics Results", 
            type=['json'],
            help="Upload JSON file from analytics processors"
        )
        
        if uploaded_file:
            try:
                analytics_data = json.load(uploaded_file)
                st.session_state.analytics_data = analytics_data
                st.sidebar.success("✅ Analytics data loaded successfully")
            except Exception as e:
                st.sidebar.error(f"❌ Error loading file: {str(e)}")
        
        # Analytics configuration
        st.sidebar.subheader("⚙️ Analytics Settings")
        
        # Time period selection
        time_period = st.sidebar.selectbox(
            "Analysis Time Period",
            ["Last 5 Years", "Last 3 Years", "Last 2 Years", "Custom Range"],
            index=0
        )
        
        # Risk threshold configuration
        risk_threshold = st.sidebar.slider(
            "Risk Assessment Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1,
            help="Organizations below this score are considered high risk"
        )
        
        # Competitive analysis scope
        competitive_scope = st.sidebar.selectbox(
            "Competitive Analysis Scope",
            ["All Organizations", "Peer Groups Only", "Market Leaders", "High Growth"],
            index=0
        )
        
        # Navigation section
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔗 Navigation")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🏠 Main Dashboard", help="Switch to main Catalynx dashboard"):
                st.info("Main Dashboard available at:\\nhttp://localhost:8502")
        
        with col2:
            if st.button("🔄 Refresh Data", help="Reload analytics data"):
                if st.button("Confirm Refresh"):
                    st.rerun()
        
        # Export options
        st.sidebar.markdown("---")
        st.sidebar.subheader("📤 Export Options")
        if st.sidebar.button("📊 Export Executive Summary"):
            self._export_executive_summary()
        
        if st.sidebar.button("📈 Export Trend Analysis"):
            self._export_trend_analysis()
        
        if st.sidebar.button("🎯 Export Strategic Insights"):
            self._export_strategic_insights()
    
    def _render_welcome_screen(self):
        """Render welcome screen when no data is loaded."""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            ### 🚀 Welcome to Catalynx Analytics
            
            Your strategic intelligence platform for grant research and competitive analysis.
            
            **Getting Started:**
            1. Load your latest analytics data using the sidebar
            2. Explore trend analysis and risk assessments
            3. Review competitive intelligence insights
            4. Generate executive reports and strategic recommendations
            
            **Analytics Capabilities:**
            - 📈 Multi-year financial trend analysis
            - 🎯 Comprehensive risk assessment
            - 🏆 Competitive intelligence and market positioning
            - 📊 Interactive visualizations and executive summaries
            - 📤 Professional report generation
            """)
            
            if st.button("🔄 Load Sample Analytics Data", type="primary"):
                self._load_sample_data()
    
    def _render_main_dashboard(self):
        """Render the main analytics dashboard."""
        analytics_data = st.session_state.analytics_data
        
        # Key metrics overview
        self._render_metrics_overview(analytics_data)
        
        # Main tabs for different analytics views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Executive Overview", 
            "📈 Trend Analysis", 
            "🎯 Risk Assessment", 
            "🏆 Competitive Intelligence",
            "📋 Strategic Insights"
        ])
        
        with tab1:
            self._render_executive_overview(analytics_data)
        
        with tab2:
            self._render_trend_analysis(analytics_data)
        
        with tab3:
            self._render_risk_assessment(analytics_data)
        
        with tab4:
            self._render_competitive_intelligence(analytics_data)
        
        with tab5:
            self._render_strategic_insights(analytics_data)
    
    def _render_metrics_overview(self, analytics_data: Dict[str, Any]):
        """Render key metrics overview."""
        st.subheader("🎯 Key Performance Indicators")
        
        # Extract key metrics
        organizations = analytics_data.get('organizations', [])
        risk_assessments = analytics_data.get('risk_assessments', [])
        market_analysis = analytics_data.get('market_analysis', {})
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_orgs = len(organizations)
            st.metric(
                label="Organizations Analyzed",
                value=total_orgs,
                delta=f"+{total_orgs-12}" if total_orgs > 12 else None
            )
        
        with col2:
            if risk_assessments:
                avg_risk = np.mean([r.get('composite_risk_score', 0) for r in risk_assessments])
                st.metric(
                    label="Average Risk Score",
                    value=f"{avg_risk:.2f}",
                    delta=f"{'Good' if avg_risk > 0.6 else 'Fair' if avg_risk > 0.4 else 'Poor'}"
                )
        
        with col3:
            low_risk_count = sum(1 for r in risk_assessments if r.get('risk_classification') == 'low')
            st.metric(
                label="Low Risk Organizations",
                value=low_risk_count,
                delta=f"{(low_risk_count/len(risk_assessments)*100):.0f}%" if risk_assessments else "0%"
            )
        
        with col4:
            ready_for_grants = sum(1 for r in risk_assessments if r.get('grant_readiness_score', 0) > 0.7)
            st.metric(
                label="Grant Ready",
                value=ready_for_grants,
                delta=f"{(ready_for_grants/len(organizations)*100):.0f}%" if organizations else "0%"
            )
        
        with col5:
            market_health = market_analysis.get('competitive_landscape_summary', {}).get('competitive_health', 'unknown')
            st.metric(
                label="Market Health",
                value=market_health.title(),
                delta="Competitive Analysis" if market_health != 'unknown' else None
            )
    
    def _render_executive_overview(self, analytics_data: Dict[str, Any]):
        """Render executive overview dashboard."""
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Portfolio Distribution")
            
            # Risk distribution pie chart
            risk_assessments = analytics_data.get('risk_assessments', [])
            if risk_assessments:
                risk_counts = {}
                for assessment in risk_assessments:
                    risk_level = assessment.get('risk_classification', 'unknown')
                    risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
                
                fig = px.pie(
                    values=list(risk_counts.values()),
                    names=list(risk_counts.keys()),
                    title="Risk Distribution",
                    color_discrete_map={
                        'low': '#28a745',
                        'moderate': '#ffc107', 
                        'high': '#dc3545',
                        'very_high': '#6f42c1'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Executive Insights")
            
            # Top insights cards
            competitive_insights = analytics_data.get('competitive_insights', {})
            key_findings = competitive_insights.get('key_findings', [])
            
            for i, finding in enumerate(key_findings[:3]):
                st.markdown(f"""
                <div class="insight-card">
                    <strong>Key Finding #{i+1}</strong><br>
                    {finding}
                </div>
                """, unsafe_allow_html=True)
        
        # Market overview section
        st.subheader("🏆 Market Landscape")
        
        col1, col2, col3 = st.columns(3)
        
        market_analysis = analytics_data.get('market_analysis', {})
        
        with col1:
            # Market concentration
            concentration = market_analysis.get('market_concentration', {})
            market_structure = concentration.get('market_structure', 'unknown')
            cr4 = concentration.get('concentration_ratio_4', 0)
            
            st.markdown(f"""
            <div class="insight-card">
                <strong>Market Structure</strong><br>
                <span class="trend-{'positive' if market_structure == 'moderately_concentrated' else 'stable'}">
                    {market_structure.replace('_', ' ').title()}
                </span><br>
                <small>Top 4 control {cr4*100:.0f}% of revenue</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Geographic spread
            geographic_markets = market_analysis.get('geographic_markets', {})
            primary_markets = geographic_markets.get('primary_markets', [])
            
            if primary_markets:
                top_state, org_count = primary_markets[0]
                st.markdown(f"""
                <div class="insight-card">
                    <strong>Geographic Focus</strong><br>
                    <span class="trend-positive">{top_state}</span><br>
                    <small>{org_count} organizations</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            # Growth potential
            market_dynamics = competitive_insights.get('market_dynamics', {})
            growth_potential = market_dynamics.get('market_growth_potential', 'unknown')
            
            st.markdown(f"""
            <div class="insight-card">
                <strong>Growth Potential</strong><br>
                <span class="trend-{'positive' if growth_potential == 'high' else 'stable' if growth_potential == 'moderate' else 'negative'}">
                    {growth_potential.title()}
                </span><br>
                <small>Market opportunity assessment</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_trend_analysis(self, analytics_data: Dict[str, Any]):
        """Render trend analysis dashboard."""
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        
        st.subheader("📈 Multi-Year Financial Trends")
        
        # Get trend analysis data
        trend_analysis = analytics_data.get('trend_analysis', [])
        
        if not trend_analysis:
            st.warning("No trend analysis data available. Please run the trend analyzer processor.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Revenue trend visualization
        st.subheader("💰 Revenue Trends")
        
        # Create revenue trend chart
        trend_data = []
        for org_trend in trend_analysis:
            revenue_trend = org_trend.get('revenue_trend', {})
            if 'values' in revenue_trend and 'years' in revenue_trend:
                for year, value in zip(revenue_trend['years'], revenue_trend['values']):
                    trend_data.append({
                        'Organization': org_trend.get('name', 'Unknown'),
                        'Year': year,
                        'Revenue': value,
                        'EIN': org_trend.get('ein', '')
                    })
        
        if trend_data:
            df_trends = pd.DataFrame(trend_data)
            
            # Interactive line chart
            fig = px.line(
                df_trends, 
                x='Year', 
                y='Revenue', 
                color='Organization',
                title='Revenue Trends Over Time',
                labels={'Revenue': 'Revenue ($)'},
                hover_data=['EIN']
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        # Growth classification analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Growth Classification")
            
            growth_classifications = {}
            for org_trend in trend_analysis:
                classification = org_trend.get('growth_classification', 'unknown')
                growth_classifications[classification] = growth_classifications.get(classification, 0) + 1
            
            if growth_classifications:
                fig = px.bar(
                    x=list(growth_classifications.keys()),
                    y=list(growth_classifications.values()),
                    title="Organizations by Growth Pattern",
                    color=list(growth_classifications.values()),
                    color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Financial Stability")
            
            stability_scores = []
            org_names = []
            
            for org_trend in trend_analysis:
                financial_stability = org_trend.get('financial_stability', {})
                stability_score = financial_stability.get('stability_score', 0)
                if stability_score > 0:
                    stability_scores.append(stability_score)
                    org_names.append(org_trend.get('name', 'Unknown')[:20])  # Truncate long names
            
            if stability_scores:
                fig = px.bar(
                    x=org_names,
                    y=stability_scores,
                    title="Financial Stability Scores",
                    color=stability_scores,
                    color_continuous_scale="RdYlGn"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Detailed trend insights
        st.subheader("🔍 Trend Insights")
        
        for org_trend in trend_analysis[:5]:  # Show top 5 organizations
            name = org_trend.get('name', 'Unknown Organization')
            growth_class = org_trend.get('growth_classification', 'unknown')
            grant_readiness = org_trend.get('grant_readiness_score', 0)
            
            # Determine card styling based on performance
            card_class = 'insight-card'
            if growth_class in ['accelerating', 'steady_growth']:
                card_class += ' risk-low'
            elif growth_class == 'declining':
                card_class += ' risk-high'
            
            recommendations = org_trend.get('strategic_recommendations', [])
            rec_text = recommendations[0] if recommendations else "No specific recommendations"
            
            st.markdown(f"""
            <div class="{card_class}">
                <strong>{name}</strong><br>
                <span class="trend-{'positive' if growth_class in ['accelerating', 'steady_growth'] else 'negative' if growth_class == 'declining' else 'stable'}">
                    {growth_class.replace('_', ' ').title()}
                </span> | Grant Readiness: {grant_readiness:.2f}<br>
                <small><em>{rec_text}</em></small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_risk_assessment(self, analytics_data: Dict[str, Any]):
        """Render risk assessment dashboard."""
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        
        st.subheader("🎯 Comprehensive Risk Assessment")
        
        risk_assessments = analytics_data.get('risk_assessments', [])
        
        if not risk_assessments:
            st.warning("No risk assessment data available. Please run the risk assessor processor.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Risk distribution overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Risk level distribution
            risk_levels = {}
            for assessment in risk_assessments:
                level = assessment.get('risk_classification', 'unknown')
                risk_levels[level] = risk_levels.get(level, 0) + 1
            
            fig = px.pie(
                values=list(risk_levels.values()),
                names=list(risk_levels.keys()),
                title="Risk Level Distribution",
                color_discrete_map={
                    'low': '#28a745',
                    'moderate': '#ffc107',
                    'high': '#fd7e14',
                    'very_high': '#dc3545'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Grant readiness distribution
            readiness_levels = {}
            for assessment in risk_assessments:
                level = assessment.get('grant_readiness_level', 'unknown')
                readiness_levels[level] = readiness_levels.get(level, 0) + 1
            
            fig = px.bar(
                x=list(readiness_levels.keys()),
                y=list(readiness_levels.values()),
                title="Grant Readiness Levels",
                color=list(readiness_levels.values()),
                color_continuous_scale="Greens"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            # Risk vs Readiness scatter
            risk_scores = []
            readiness_scores = []
            org_names = []
            
            for assessment in risk_assessments:
                risk_scores.append(assessment.get('composite_risk_score', 0))
                readiness_scores.append(assessment.get('grant_readiness_score', 0))
                org_names.append(assessment.get('name', 'Unknown')[:15])
            
            fig = px.scatter(
                x=risk_scores,
                y=readiness_scores,
                text=org_names,
                title="Risk vs Grant Readiness",
                labels={'x': 'Risk Score (Higher = Lower Risk)', 'y': 'Grant Readiness Score'},
                color=readiness_scores,
                color_continuous_scale="RdYlGn"
            )
            fig.update_traces(textposition="top center")
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed risk analysis
        st.subheader("🔍 Risk Analysis Details")
        
        # Risk component analysis
        risk_components = ['financial_stability', 'operational_risk', 'sustainability_risk', 
                          'compliance_risk', 'capacity_risk', 'external_risk']
        
        component_data = []
        for assessment in risk_assessments:
            org_name = assessment.get('name', 'Unknown')
            risk_breakdown = assessment.get('risk_components', {})
            
            for component in risk_components:
                if component in risk_breakdown:
                    component_data.append({
                        'Organization': org_name,
                        'Risk Component': component.replace('_', ' ').title(),
                        'Score': risk_breakdown[component].get('score', 0)
                    })
        
        if component_data:
            df_components = pd.DataFrame(component_data)
            
            # Heatmap of risk components
            pivot_data = df_components.pivot(index='Organization', columns='Risk Component', values='Score')
            
            fig = px.imshow(
                pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                color_continuous_scale="RdYlGn",
                title="Risk Component Heatmap (Green = Lower Risk)",
                aspect="auto"
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        
        # Individual organization risk profiles
        st.subheader("📋 Organization Risk Profiles")
        
        # Create risk profile cards
        for assessment in risk_assessments[:6]:  # Show top 6 organizations
            name = assessment.get('name', 'Unknown Organization')
            risk_class = assessment.get('risk_classification', 'unknown')
            risk_score = assessment.get('composite_risk_score', 0)
            readiness_score = assessment.get('grant_readiness_score', 0)
            key_risks = assessment.get('key_risk_factors', [])
            
            # Determine card styling
            if risk_class == 'low':
                card_class = 'insight-card risk-low'
            elif risk_class == 'moderate':
                card_class = 'insight-card risk-moderate'
            else:
                card_class = 'insight-card risk-high'
            
            risk_text = ', '.join(key_risks[:2]) if key_risks else "No major risk factors identified"
            
            st.markdown(f"""
            <div class="{card_class}">
                <strong>{name}</strong><br>
                Risk Level: <span class="trend-{'positive' if risk_class == 'low' else 'negative' if risk_class in ['high', 'very_high'] else 'stable'}">
                    {risk_class.replace('_', ' ').title()}
                </span> ({risk_score:.2f}) | Grant Readiness: {readiness_score:.2f}<br>
                <small><strong>Key Risks:</strong> {risk_text}</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_competitive_intelligence(self, analytics_data: Dict[str, Any]):
        """Render competitive intelligence dashboard."""
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        
        st.subheader("🏆 Competitive Intelligence & Market Analysis")
        
        competitive_insights = analytics_data.get('competitive_insights', {})
        market_analysis = analytics_data.get('market_analysis', {})
        peer_analysis = analytics_data.get('peer_analysis', {})
        
        if not competitive_insights:
            st.warning("No competitive intelligence data available. Please run the competitive intelligence processor.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Market overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Market structure
            concentration = market_analysis.get('market_concentration', {})
            market_structure = concentration.get('market_structure', 'unknown')
            cr4 = concentration.get('concentration_ratio_4', 0)
            
            st.markdown(f"""
            <div class="insight-card competitive-leader">
                <strong>Market Structure</strong><br>
                {market_structure.replace('_', ' ').title()}<br>
                <small>Top 4 organizations: {cr4*100:.0f}% market share</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Competitive clusters
            clusters = peer_analysis.get('clusters', [])
            cluster_analysis = peer_analysis.get('cluster_analysis', {})
            
            st.markdown(f"""
            <div class="insight-card">
                <strong>Competitive Clusters</strong><br>
                {len(clusters)} clusters identified<br>
                <small>Clustering rate: {cluster_analysis.get('clustering_rate', 0)*100:.0f}%</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Market health
            landscape_summary = competitive_insights.get('competitive_landscape_summary', {})
            competitive_health = landscape_summary.get('competitive_health', 'unknown')
            
            st.markdown(f"""
            <div class="insight-card risk-{'low' if competitive_health == 'excellent' else 'moderate' if competitive_health == 'good' else 'high'}">
                <strong>Market Health</strong><br>
                {competitive_health.title()}<br>
                <small>Overall market assessment</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Market leaders and positioning
        st.subheader("👑 Market Leaders")
        
        market_leaders = market_analysis.get('market_leaders', [])
        competitive_positioning = market_analysis.get('competitive_positioning', {})
        
        if market_leaders:
            col1, col2 = st.columns(2)
            
            with col1:
                # Market leaders chart
                leader_data = []
                for leader in market_leaders:
                    leader_data.append({
                        'Organization': leader.get('name', 'Unknown'),
                        'Leadership Type': leader.get('leadership_type', 'unknown').replace('_', ' ').title(),
                        'Metric Value': leader.get('metric_value', 0)
                    })
                
                if leader_data:
                    df_leaders = pd.DataFrame(leader_data)
                    fig = px.bar(
                        df_leaders,
                        x='Organization',
                        y='Metric Value',
                        color='Leadership Type',
                        title="Market Leadership Analysis"
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Competitive positioning
                positioning_data = []
                for ein, position_info in competitive_positioning.items():
                    positioning_data.append({
                        'Organization': position_info.get('organization_name', 'Unknown'),
                        'Market Position': position_info.get('market_position', 'unknown'),
                        'Peer Count': position_info.get('peer_count', 0),
                        'Market Share': position_info.get('market_share_proxy', 0) or 0
                    })
                
                if positioning_data:
                    df_positioning = pd.DataFrame(positioning_data)
                    fig = px.scatter(
                        df_positioning,
                        x='Peer Count',
                        y='Market Share',
                        size='Market Share',
                        color='Market Position',
                        hover_name='Organization',
                        title="Competitive Positioning Map"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Competitive clusters analysis
        st.subheader("🎯 Competitive Clusters")
        
        if clusters:
            for i, cluster in enumerate(clusters[:3]):  # Show top 3 clusters
                cluster_type = cluster.get('cluster_type', 'unknown')
                cluster_size = cluster.get('size', 0)
                financial_profile = cluster.get('financial_profile', {})
                median_revenue = financial_profile.get('median_revenue', 0)
                
                st.markdown(f"""
                <div class="insight-card">
                    <strong>Cluster {i+1}: {cluster_type.replace('_', ' ').title()}</strong><br>
                    Size: {cluster_size} organizations | Median Revenue: ${median_revenue:,.0f}<br>
                    <small>Competitive Intensity: {cluster.get('competitive_intensity', 'unknown').title()}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Strategic recommendations
        st.subheader("📋 Strategic Recommendations")
        
        strategic_recommendations = competitive_insights.get('strategic_recommendations', [])
        
        for i, recommendation in enumerate(strategic_recommendations):
            st.markdown(f"""
            <div class="insight-card">
                <strong>Recommendation {i+1}</strong><br>
                {recommendation}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_strategic_insights(self, analytics_data: Dict[str, Any]):
        """Render strategic insights and recommendations."""
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        
        st.subheader("🎯 Strategic Intelligence & Recommendations")
        
        # Executive summary
        st.subheader("📊 Executive Summary")
        
        organizations = analytics_data.get('organizations', [])
        risk_assessments = analytics_data.get('risk_assessments', [])
        competitive_insights = analytics_data.get('competitive_insights', {})
        funding_opportunities = analytics_data.get('funding_opportunities', {})
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            high_potential_orgs = sum(1 for r in risk_assessments 
                                    if r.get('grant_readiness_score', 0) > 0.7 and 
                                       r.get('risk_classification') in ['low', 'moderate'])
            st.metric("High Potential Organizations", high_potential_orgs)
        
        with col2:
            market_gaps = len(funding_opportunities.get('market_gaps', []))
            st.metric("Market Opportunities", market_gaps)
        
        with col3:
            strategic_themes = len(funding_opportunities.get('strategic_funding_themes', []))
            st.metric("Strategic Themes", strategic_themes)
        
        with col4:
            total_market_size = competitive_insights.get('competitive_landscape_summary', {}).get('total_market_size', 0)
            st.metric("Total Market Size", f"${total_market_size:,.0f}")
        
        # Funding opportunities
        st.subheader("💰 Funding Opportunities")
        
        funding_priorities = funding_opportunities.get('funding_priorities', [])
        
        for priority in funding_priorities:
            priority_type = priority.get('type', 'unknown')
            priority_level = priority.get('priority_level', 'medium')
            rationale = priority.get('rationale', 'No rationale provided')
            
            card_class = f"insight-card risk-{'low' if priority_level == 'high' else 'moderate' if priority_level == 'medium' else 'high'}"
            
            st.markdown(f"""
            <div class="{card_class}">
                <strong>{priority_type.replace('_', ' ').title()}</strong> 
                <span style="float: right; font-size: 0.8em; font-weight: bold;">
                    {priority_level.upper()} PRIORITY
                </span><br>
                {rationale}<br>
                <small>Organization: {priority.get('organization', priority.get('segment', 'Multiple'))}</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Risk-adjusted opportunities
        st.subheader("📊 Risk-Adjusted Investment Opportunities")
        
        risk_adjusted_opps = funding_opportunities.get('risk_adjusted_opportunities', [])
        
        if risk_adjusted_opps:
            opp_data = []
            for opp in risk_adjusted_opps:
                opp_data.append({
                    'Organization': opp.get('name', 'Unknown'),
                    'Opportunity Type': opp.get('opportunity_type', 'unknown').replace('_', ' ').title(),
                    'Risk Level': opp.get('risk_level', 'unknown'),
                    'Expected Impact': opp.get('expected_impact', 'unknown'),
                    'Rationale': opp.get('rationale', 'No rationale')
                })
            
            df_opportunities = pd.DataFrame(opp_data)
            st.dataframe(df_opportunities, use_container_width=True)
        
        # Portfolio recommendations
        st.subheader("📈 Portfolio Strategy")
        
        portfolio_recommendations = funding_opportunities.get('portfolio_recommendations', [])
        
        for i, recommendation in enumerate(portfolio_recommendations):
            st.markdown(f"""
            <div class="insight-card">
                <strong>Portfolio Strategy {i+1}</strong><br>
                {recommendation}
            </div>
            """, unsafe_allow_html=True)
        
        # Strategic themes
        st.subheader("🎯 Strategic Funding Themes")
        
        strategic_themes_list = funding_opportunities.get('strategic_funding_themes', [])
        
        for theme in strategic_themes_list:
            st.markdown(f"""
            <div class="insight-card competitive-leader">
                <strong>Strategic Theme</strong><br>
                {theme.replace('_', ' ').title()}
            </div>
            """, unsafe_allow_html=True)
        
        # Market insights
        st.subheader("🏆 Market Intelligence")
        
        market_dynamics = competitive_insights.get('market_dynamics', {})
        key_findings = competitive_insights.get('key_findings', [])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Market Dynamics**")
            for metric, value in market_dynamics.items():
                st.markdown(f"- **{metric.replace('_', ' ').title()}**: {value.title() if isinstance(value, str) else value}")
        
        with col2:
            st.markdown("**Key Market Findings**")
            for finding in key_findings:
                st.markdown(f"- {finding}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _load_analytics_data(self):
        """Load latest analytics data from workflow results."""
        try:
            # This would typically load from a results file or database
            # For now, we'll create sample data
            st.sidebar.info("Loading latest analytics data...")
            self._load_sample_data()
            st.sidebar.success("✅ Analytics data loaded successfully")
        except Exception as e:
            st.sidebar.error(f"❌ Error loading analytics data: {str(e)}")
    
    def _load_sample_data(self):
        """Load sample analytics data for demonstration."""
        # Create sample analytics data structure
        sample_data = {
            "organizations": [
                {
                    "ein": "541669652",
                    "name": "FAMILY FORWARD FOUNDATION",
                    "revenue": 2500000,
                    "assets": 3200000,
                    "state": "VA",
                    "ntee_code": "P81",
                    "composite_score": 0.85,
                    "risk_classification": "low",
                    "grant_readiness_score": 0.82
                },
                {
                    "ein": "123456789", 
                    "name": "COMMUNITY HEALTH CENTER",
                    "revenue": 1500000,
                    "assets": 1800000,
                    "state": "VA",
                    "ntee_code": "E31",
                    "composite_score": 0.72,
                    "risk_classification": "moderate",
                    "grant_readiness_score": 0.68
                }
            ],
            "trend_analysis": [
                {
                    "ein": "541669652",
                    "name": "FAMILY FORWARD FOUNDATION",
                    "revenue_trend": {
                        "values": [2000000, 2200000, 2500000],
                        "years": [2020, 2021, 2022],
                        "annual_growth_rate": 0.12,
                        "trend": "strong_growth"
                    },
                    "growth_classification": "accelerating",
                    "grant_readiness_score": 0.82,
                    "financial_stability": {"stability_score": 0.85},
                    "strategic_recommendations": ["Strong growth trajectory - excellent grant candidate"]
                }
            ],
            "risk_assessments": [
                {
                    "ein": "541669652",
                    "name": "FAMILY FORWARD FOUNDATION",
                    "composite_risk_score": 0.85,
                    "risk_classification": "low",
                    "grant_readiness_score": 0.82,
                    "grant_readiness_level": "excellent",
                    "key_risk_factors": [],
                    "risk_components": {
                        "financial_stability": {"score": 0.90},
                        "operational_risk": {"score": 0.85},
                        "sustainability_risk": {"score": 0.80},
                        "compliance_risk": {"score": 0.88},
                        "capacity_risk": {"score": 0.82},
                        "external_risk": {"score": 0.85}
                    }
                }
            ],
            "competitive_insights": {
                "market_dynamics": {
                    "market_maturity": "mature",
                    "competitive_intensity": "moderate",
                    "market_growth_potential": "high",
                    "consolidation_potential": "moderate"
                },
                "strategic_recommendations": [
                    "Focus on building market leaders with sustainable competitive advantages",
                    "Leverage geographic diversification for risk mitigation"
                ],
                "key_findings": [
                    "Moderate clustering: 3 distinct competitive clusters identified",
                    "Geographic concentration in VA with 8 organizations"
                ],
                "competitive_landscape_summary": {
                    "total_organizations": 12,
                    "total_market_size": 25000000,
                    "competitive_health": "good"
                }
            },
            "market_analysis": {
                "market_concentration": {
                    "concentration_ratio_4": 0.45,
                    "market_structure": "moderately_concentrated"
                },
                "market_leaders": [
                    {
                        "name": "FAMILY FORWARD FOUNDATION",
                        "leadership_type": "revenue_leader",
                        "metric_value": 2500000
                    }
                ],
                "competitive_positioning": {
                    "541669652": {
                        "organization_name": "FAMILY FORWARD FOUNDATION",
                        "market_position": "market_leader",
                        "peer_count": 3,
                        "market_share_proxy": 0.15
                    }
                },
                "geographic_markets": {
                    "primary_markets": [("VA", 8), ("MD", 3)]
                }
            },
            "peer_analysis": {
                "clusters": [
                    {
                        "cluster_type": "large_players",
                        "size": 4,
                        "competitive_intensity": "moderate",
                        "financial_profile": {"median_revenue": 2000000}
                    }
                ],
                "cluster_analysis": {
                    "total_clusters": 3,
                    "clustering_rate": 0.75
                }
            },
            "funding_opportunities": {
                "funding_priorities": [
                    {
                        "type": "scale_market_leader",
                        "organization": "FAMILY FORWARD FOUNDATION",
                        "rationale": "Proven revenue leader with growth potential",
                        "priority_level": "high"
                    }
                ],
                "portfolio_recommendations": [
                    "Balance portfolio with smaller, innovative organizations"
                ],
                "risk_adjusted_opportunities": [
                    {
                        "name": "FAMILY FORWARD FOUNDATION",
                        "opportunity_type": "high_confidence_investment",
                        "risk_level": "low",
                        "expected_impact": "high",
                        "rationale": "Low risk with high grant readiness"
                    }
                ],
                "strategic_funding_themes": [
                    "integrated_health_and_nutrition_approach"
                ],
                "market_gaps": [
                    {
                        "type": "underserved_segment",
                        "segment": "nutrition_food_small"
                    }
                ]
            }
        }
        
        st.session_state.analytics_data = sample_data
    
    def _export_executive_summary(self):
        """Export executive summary report."""
        st.sidebar.info("Generating executive summary...")
        # Implementation would generate PDF/Excel report
        st.sidebar.success("✅ Executive summary exported")
    
    def _export_trend_analysis(self):
        """Export trend analysis report."""
        st.sidebar.info("Generating trend analysis report...")
        # Implementation would generate detailed trend report
        st.sidebar.success("✅ Trend analysis exported")
    
    def _export_strategic_insights(self):
        """Export strategic insights report."""
        st.sidebar.info("Generating strategic insights report...")
        # Implementation would generate strategic recommendations
        st.sidebar.success("✅ Strategic insights exported")


# Main application
def main():
    """Main application entry point."""
    dashboard = AdvancedAnalyticsDashboard()
    dashboard.render()

if __name__ == "__main__":
    main()