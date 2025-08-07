#!/usr/bin/env python3
"""
Multi-Profile Management Dashboard
Manages multiple organization profiles for comprehensive opportunity discovery.
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.profiles.service import ProfileService
from src.profiles.models import OrganizationProfile, OrganizationType, ProfileStatus, FundingType


class ProfileManager:
    """Multi-profile management interface"""
    
    def __init__(self):
        """Initialize profile manager"""
        self.profile_service = ProfileService()
        
        # Initialize session state
        if 'selected_profile_id' not in st.session_state:
            st.session_state.selected_profile_id = None
        if 'profile_action' not in st.session_state:
            st.session_state.profile_action = "list"
    
    def render_profile_management(self):
        """Main profile management interface"""
        
        # Logo and header section
        col1, col2 = st.columns([1, 3])
        with col1:
            try:
                st.image("CatalynxLogo.png", width=150)
            except:
                st.write("**Catalynx**")
        
        with col2:
            st.title("Organization Profile Management")
            st.markdown("**Opportunistic Grantmogrifier**")
            st.caption("Manage multiple organization profiles and their opportunity ecosystems")
        
        # Action selection
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 View All Profiles", use_container_width=True):
                st.session_state.profile_action = "list"
                st.rerun()
        
        with col2:
            if st.button("➕ Create New Profile", use_container_width=True):
                st.session_state.profile_action = "create"
                st.rerun()
        
        with col3:
            if st.button("📊 Profile Analytics", use_container_width=True):
                st.session_state.profile_action = "analytics"
                st.rerun()
        
        with col4:
            if st.button("🔗 Network Overview", use_container_width=True):
                st.session_state.profile_action = "network"
                st.rerun()
        
        st.markdown("---")
        
        # Render selected action
        if st.session_state.profile_action == "list":
            self.render_profile_list()
        elif st.session_state.profile_action == "create":
            self.render_create_profile()
        elif st.session_state.profile_action == "edit":
            self.render_edit_profile()
        elif st.session_state.profile_action == "analytics":
            self.render_profile_analytics()
        elif st.session_state.profile_action == "network":
            self.render_network_overview()
    
    def render_profile_list(self):
        """Render list of all profiles"""
        st.subheader("Organization Profiles")
        
        # Get all active profiles
        profiles = self.profile_service.list_profiles(status=ProfileStatus.ACTIVE)
        
        if not profiles:
            st.info("No organization profiles found. Create your first profile to get started!")
            return
        
        # Display profiles in cards
        for profile in profiles:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.subheader(profile.name)
                    st.write(f"**EIN:** {profile.ein or 'Not provided'}")
                    st.write(f"**Type:** {profile.organization_type.value}")
                    
                    # Show focus areas as tags
                    if profile.focus_areas:
                        focus_tags = " | ".join(profile.focus_areas[:3])
                        st.caption(f"Focus Areas: {focus_tags}")
                
                with col2:
                    st.metric("Annual Revenue", f"${profile.annual_revenue:,}" if profile.annual_revenue else "Not specified")
                    st.caption(f"Created: {profile.created_at.strftime('%Y-%m-%d')}")
                
                with col3:
                    # Get profile analytics
                    analytics = self.profile_service.get_profile_analytics(profile.profile_id)
                    st.metric("Opportunities", analytics.get('total_opportunities', 0))
                    st.caption(f"Last Updated: {profile.updated_at.strftime('%Y-%m-%d')}")
                
                with col4:
                    if st.button("🔍 View", key=f"view_{profile.profile_id}"):
                        st.session_state.selected_profile_id = profile.profile_id
                        st.session_state.profile_action = "detail"
                        st.rerun()
                    
                    if st.button("✏️ Edit", key=f"edit_{profile.profile_id}"):
                        st.session_state.selected_profile_id = profile.profile_id
                        st.session_state.profile_action = "edit"
                        st.rerun()
                    
                    if st.button("🚀 Run Discovery", key=f"discover_{profile.profile_id}"):
                        st.session_state.selected_profile_id = profile.profile_id
                        st.info(f"Starting opportunity discovery for {profile.name}...")
                        # TODO: Integration with workflow engine
                
                st.markdown("---")
    
    def render_create_profile(self):
        """Render profile creation form"""
        st.subheader("Create New Organization Profile")
        
        with st.form("create_profile_form"):
            # Basic Information
            st.markdown("### Basic Information")
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Organization Name*", help="Full legal name of the organization")
                ein = st.text_input("EIN", help="Tax identification number (format: XX-XXXXXXX)")
                organization_type = st.selectbox("Organization Type*", options=[t.value for t in OrganizationType])
            
            with col2:
                annual_revenue = st.number_input("Annual Revenue ($)", min_value=0, help="Approximate annual budget")
                staff_size = st.number_input("Staff Size", min_value=0, help="Number of employees/staff")
                board_size = st.number_input("Board Size", min_value=0, help="Number of board members")
            
            # Mission and Focus
            st.markdown("### Mission and Focus")
            mission_statement = st.text_area("Mission Statement*", help="Brief description of organization's mission")
            
            col1, col2 = st.columns(2)
            with col1:
                focus_areas = st.text_area("Focus Areas*", help="Main areas of focus (one per line)")
                program_areas = st.text_area("Program Areas", help="Specific programs or services (one per line)")
            
            with col2:
                target_populations = st.text_area("Target Populations", help="Populations served (one per line)")
                service_areas = st.text_area("Service Areas", help="Geographic areas served (one per line)")
            
            # Geographic Scope
            st.markdown("### Geographic Scope")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                states = st.text_area("Target States", help="State codes (e.g., VA, MD, DC)")
                nationwide = st.checkbox("Nationwide Scope")
            
            with col2:
                regions = st.text_area("Regions", help="Geographic regions of interest")
                international = st.checkbox("International Scope")
            
            # Funding Preferences
            st.markdown("### Funding Preferences")
            col1, col2 = st.columns(2)
            
            with col1:
                min_amount = st.number_input("Minimum Funding Amount ($)", min_value=0)
                max_amount = st.number_input("Maximum Funding Amount ($)", min_value=0)
            
            with col2:
                funding_types = st.multiselect("Funding Types", options=[t.value for t in FundingType], default=["grants"])
                recurring = st.checkbox("Interested in Recurring Funding")
            
            # Strategic Information
            st.markdown("### Strategic Information")
            col1, col2 = st.columns(2)
            
            with col1:
                strategic_priorities = st.text_area("Strategic Priorities", help="Current strategic goals (one per line)")
                growth_goals = st.text_area("Growth Goals", help="Expansion and growth objectives (one per line)")
            
            with col2:
                partnership_interests = st.text_area("Partnership Interests", help="Types of partnerships sought (one per line)")
                certifications = st.text_area("Certifications", help="Relevant certifications held (one per line)")
            
            # Additional Notes
            notes = st.text_area("Additional Notes", help="Any additional information about the organization")
            
            # Form submission
            submitted = st.form_submit_button("Create Profile", use_container_width=True)
            
            if submitted:
                if not name or not mission_statement or not focus_areas:
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    try:
                        # Prepare profile data
                        profile_data = {
                            "name": name,
                            "organization_type": organization_type,
                            "ein": ein if ein else None,
                            "mission_statement": mission_statement,
                            "focus_areas": [area.strip() for area in focus_areas.split('\n') if area.strip()],
                            "program_areas": [area.strip() for area in program_areas.split('\n') if area.strip()],
                            "target_populations": [pop.strip() for pop in target_populations.split('\n') if pop.strip()],
                            "service_areas": [area.strip() for area in service_areas.split('\n') if area.strip()],
                            "geographic_scope": {
                                "states": [state.strip().upper() for state in states.split('\n') if state.strip()] if states else [],
                                "regions": [region.strip() for region in regions.split('\n') if region.strip()],
                                "nationwide": nationwide,
                                "international": international
                            },
                            "funding_preferences": {
                                "min_amount": min_amount if min_amount > 0 else None,
                                "max_amount": max_amount if max_amount > 0 else None,
                                "funding_types": funding_types,
                                "recurring": recurring
                            },
                            "annual_revenue": annual_revenue if annual_revenue > 0 else None,
                            "staff_size": staff_size if staff_size > 0 else None,
                            "board_size": board_size if board_size > 0 else None,
                            "strategic_priorities": [priority.strip() for priority in strategic_priorities.split('\n') if priority.strip()],
                            "growth_goals": [goal.strip() for goal in growth_goals.split('\n') if goal.strip()],
                            "partnership_interests": [interest.strip() for interest in partnership_interests.split('\n') if interest.strip()],
                            "certifications": [cert.strip() for cert in certifications.split('\n') if cert.strip()],
                            "notes": notes if notes else None
                        }
                        
                        # Create profile
                        profile = self.profile_service.create_profile(profile_data)
                        
                        st.success(f"Profile '{profile.name}' created successfully!")
                        st.info(f"Profile ID: {profile.profile_id}")
                        
                        # Switch to profile list view
                        st.session_state.profile_action = "list"
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Failed to create profile: {str(e)}")
    
    def render_profile_analytics(self):
        """Render analytics for all profiles"""
        st.subheader("Profile Analytics Overview")
        
        profiles = self.profile_service.list_profiles(status=ProfileStatus.ACTIVE)
        
        if not profiles:
            st.info("No profiles found for analytics.")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_profiles = len(profiles)
        total_opportunities = sum(self.profile_service.get_profile_analytics(p.profile_id).get('total_opportunities', 0) for p in profiles)
        
        with col1:
            st.metric("Total Profiles", total_profiles)
        
        with col2:
            st.metric("Total Opportunities", total_opportunities)
        
        with col3:
            avg_opportunities = total_opportunities / total_profiles if total_profiles > 0 else 0
            st.metric("Avg Opportunities per Profile", f"{avg_opportunities:.1f}")
        
        with col4:
            active_profiles = len([p for p in profiles if p.status == ProfileStatus.ACTIVE])
            st.metric("Active Profiles", active_profiles)
        
        st.markdown("---")
        
        # Individual profile analytics
        st.subheader("Individual Profile Performance")
        
        for profile in profiles:
            analytics = self.profile_service.get_profile_analytics(profile.profile_id)
            
            with st.expander(f"{profile.name} - {analytics.get('total_opportunities', 0)} opportunities"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**EIN:** {profile.ein or 'Not provided'}")
                    st.write(f"**Type:** {profile.organization_type.value}")
                    st.write(f"**Revenue:** ${profile.annual_revenue:,}" if profile.annual_revenue else "Not specified")
                    
                with col2:
                    st.write(f"**Focus Areas:** {', '.join(profile.focus_areas[:3])}")
                    st.write(f"**Last Updated:** {profile.updated_at.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Compatibility Score:** {analytics.get('average_compatibility_score', 'N/A')}")
                
                # Pipeline distribution
                if analytics.get('pipeline_distribution'):
                    st.write("**Pipeline Distribution:**")
                    pipeline_data = analytics['pipeline_distribution']
                    for stage, count in pipeline_data.items():
                        if count > 0:
                            st.write(f"  - {stage.replace('_', ' ').title()}: {count}")
    
    def render_network_overview(self):
        """Render network analysis overview"""
        st.subheader("Network Analysis Overview")
        st.info("Network analysis provides insights into board connections and funding relationships across all profiles.")
        
        # Instructions for running network analysis
        st.markdown("""
        ### Running Network Analysis
        
        To generate comprehensive network analysis across all profiles:
        
        ```bash
        # Run strategic network analysis
        python strategic_network_analysis.py
        
        # Or launch the analysis batch file
        launch_strategic_analysis.bat
        ```
        
        ### Network Analysis Features:
        - **Board Connection Mapping** - Identify shared board members across organizations
        - **Schedule I Relationship Discovery** - Find funding relationships through 990 filings
        - **Network Influence Scoring** - Calculate organizational influence metrics  
        - **Interactive Visualizations** - Spider web network graphs
        - **Strategic Recommendations** - AI-powered partnership opportunities
        """)
        
        # Check for existing network analysis results
        network_files = list(Path(".").glob("*network*.html"))
        if network_files:
            st.success(f"Found {len(network_files)} network visualization files")
            
            for file_path in network_files[:5]:  # Show up to 5 files
                st.write(f"📊 [{file_path.name}](./{file_path.name})")
        else:
            st.warning("No network analysis results found. Run the analysis commands above to generate insights.")
    
    def render_edit_profile(self):
        """Render profile editing form"""
        if not st.session_state.selected_profile_id:
            st.error("No profile selected for editing")
            return
        
        profile = self.profile_service.get_profile(st.session_state.selected_profile_id)
        if not profile:
            st.error("Profile not found")
            return
        
        st.subheader(f"Edit Profile: {profile.name}")
        
        with st.form("edit_profile_form"):
            # Pre-populate form with existing data
            name = st.text_input("Organization Name", value=profile.name)
            mission_statement = st.text_area("Mission Statement", value=profile.mission_statement)
            
            # Focus areas (convert list to text)
            focus_areas_text = '\n'.join(profile.focus_areas)
            focus_areas = st.text_area("Focus Areas", value=focus_areas_text)
            
            # Annual revenue
            annual_revenue = st.number_input("Annual Revenue ($)", value=profile.annual_revenue or 0)
            
            # Notes
            notes = st.text_area("Notes", value=profile.notes or "")
            
            # Form submission
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Update Profile", use_container_width=True):
                    try:
                        update_data = {
                            "name": name,
                            "mission_statement": mission_statement,
                            "focus_areas": [area.strip() for area in focus_areas.split('\n') if area.strip()],
                            "annual_revenue": annual_revenue if annual_revenue > 0 else None,
                            "notes": notes if notes else None
                        }
                        
                        updated_profile = self.profile_service.update_profile(profile.profile_id, update_data)
                        
                        if updated_profile:
                            st.success("Profile updated successfully!")
                            st.session_state.profile_action = "list"
                            st.rerun()
                        else:
                            st.error("Failed to update profile")
                    
                    except Exception as e:
                        st.error(f"Error updating profile: {str(e)}")
            
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.profile_action = "list"
                    st.rerun()


def render_profile_management():
    """Main entry point for profile management"""
    manager = ProfileManager()
    manager.render_profile_management()


if __name__ == "__main__":
    render_profile_management()