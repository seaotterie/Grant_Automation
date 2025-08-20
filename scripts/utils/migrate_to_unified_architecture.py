#!/usr/bin/env python3
"""
Migration Script: Multi-File Leads → Unified Opportunity Architecture

Converts the current multi-file lead structure to the simplified unified architecture:
- Consolidates lead_*_*_discovery.json + lead_*_*_pre_scoring.json etc. into single opportunity files
- Creates profile directories with profile.json + opportunities/ subdirectory
- Preserves all historical data, scoring, and analysis
- Generates real-time analytics embedded in profile files

Usage:
    python migrate_to_unified_architecture.py --dry-run    # Preview changes
    python migrate_to_unified_architecture.py --execute   # Perform migration
"""

import os
import json
import glob
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedArchitectureMigrator:
    """Migrates from multi-file lead structure to unified opportunity architecture"""
    
    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = Path(data_dir)
        self.leads_dir = self.data_dir / "leads"
        self.profiles_dir = self.data_dir / "profiles"
        self.sessions_dir = self.data_dir / "sessions"
        
        # Migration tracking
        self.migration_stats = {
            'profiles_processed': 0,
            'opportunities_consolidated': 0,
            'stage_files_merged': 0,
            'errors': []
        }
    
    def analyze_current_structure(self) -> Dict[str, Any]:
        """Analyze current lead file structure"""
        logger.info("Analyzing current lead file structure...")
        
        analysis = {
            'profiles': defaultdict(lambda: {'opportunities': defaultdict(list)}),
            'total_files': 0,
            'file_patterns': defaultdict(int)
        }
        
        # Scan all lead files
        for lead_file in self.leads_dir.glob("lead_*.json"):
            filename = lead_file.name
            analysis['total_files'] += 1
            
            # Parse filename pattern: lead_{lead_id}_profile_{profile_id}_{stage}.json
            try:
                parts = filename.replace('.json', '').split('_')
                if len(parts) >= 4:
                    lead_id = parts[1]
                    profile_id = f"profile_{parts[3]}"
                    stage = '_'.join(parts[4:]) if len(parts) > 4 else 'unknown'
                    
                    analysis['profiles'][profile_id]['opportunities'][lead_id].append({
                        'file_path': str(lead_file),
                        'stage': stage,
                        'filename': filename
                    })
                    
                    analysis['file_patterns'][stage] += 1
            except Exception as e:
                logger.warning(f"Could not parse filename {filename}: {e}")
        
        # Summary statistics
        analysis['summary'] = {
            'total_profiles': len(analysis['profiles']),
            'total_unique_opportunities': sum(len(profile_data['opportunities']) 
                                             for profile_data in analysis['profiles'].values()),
            'avg_files_per_opportunity': analysis['total_files'] / max(1, sum(len(profile_data['opportunities']) 
                                                                              for profile_data in analysis['profiles'].values()))
        }
        
        return analysis
    
    def consolidate_opportunity_stages(self, stage_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidate multiple stage files into unified opportunity record"""
        
        # Load all stage files
        stage_data = {}
        base_opportunity = None
        
        for file_info in stage_files:
            try:
                with open(file_info['file_path'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stage_data[file_info['stage']] = data
                    
                    # Use first file as base template
                    if base_opportunity is None:
                        base_opportunity = data.copy()
            except Exception as e:
                logger.error(f"Failed to load {file_info['file_path']}: {e}")
                continue
        
        if not base_opportunity:
            raise ValueError("No valid stage files found for consolidation")
        
        # Build stage history from available files
        stage_history = []
        stage_order = ['discovery', 'pre_scoring', 'deep_analysis', 'recommendations']
        current_stage = 'discovery'  # Default
        
        for stage in stage_order:
            if stage in stage_data:
                stage_entry = {
                    'stage': stage,
                    'entered_at': stage_data[stage].get('discovered_at') or stage_data[stage].get('last_analyzed'),
                    'exited_at': None,  # Will be filled by next stage
                    'duration_hours': None
                }
                
                # Set exit time from next stage's entry time
                if stage_history:
                    stage_history[-1]['exited_at'] = stage_entry['entered_at']
                    if stage_history[-1]['entered_at'] and stage_entry['entered_at']:
                        try:
                            enter_time = datetime.fromisoformat(stage_history[-1]['entered_at'].replace('Z', '+00:00'))
                            exit_time = datetime.fromisoformat(stage_entry['entered_at'].replace('Z', '+00:00'))
                            stage_history[-1]['duration_hours'] = (exit_time - enter_time).total_seconds() / 3600
                        except:
                            pass
                
                stage_history.append(stage_entry)
                current_stage = stage
        
        # Build stage-specific analysis
        analysis_by_stage = {}
        for stage, data in stage_data.items():
            analysis_by_stage[stage] = {
                'match_factors': data.get('match_factors', {}),
                'risk_factors': data.get('risk_factors', {}),
                'recommendations': data.get('recommendations', []),
                'network_insights': data.get('network_insights', {}),
                'analyzed_at': data.get('last_analyzed') or data.get('discovered_at')
            }
            
            # Add stage-specific fields
            if stage == 'discovery':
                analysis_by_stage[stage].update({
                    'source': data.get('source'),
                    'opportunity_type': data.get('opportunity_type')
                })
            elif stage == 'pre_scoring':
                if 'external_data' in data:
                    analysis_by_stage[stage]['enhanced_data'] = data['external_data']
        
        # Extract scoring information (use highest stage available)
        scoring_data = None
        for stage in reversed(stage_order):
            if stage in stage_data and 'compatibility_score' in stage_data[stage]:
                scoring_data = {
                    'overall_score': stage_data[stage].get('compatibility_score', 0.0),
                    'auto_promotion_eligible': stage_data[stage].get('compatibility_score', 0.0) >= 0.75,
                    'promotion_recommended': stage_data[stage].get('compatibility_score', 0.0) >= 0.65,
                    'confidence_level': stage_data[stage].get('success_probability', 0.8),
                    'scored_at': stage_data[stage].get('last_analyzed') or stage_data[stage].get('discovered_at'),
                    'scorer_version': '1.0.0'  # Legacy data
                }
                break
        
        # Build promotion history from stage transitions
        promotion_history = []
        for i in range(len(stage_history) - 1):
            current = stage_history[i]
            next_stage = stage_history[i + 1]
            
            promotion_history.append({
                'from_stage': current['stage'],
                'to_stage': next_stage['stage'],
                'decision_type': 'auto_promote' if scoring_data and scoring_data['overall_score'] >= 0.75 else 'manual_promote',
                'score_at_promotion': scoring_data['overall_score'] if scoring_data else 0.5,
                'reason': 'Migration from legacy multi-file structure',
                'promoted_at': next_stage['entered_at'],
                'promoted_by': 'system_migration'
            })
        
        # Build unified opportunity record
        unified_opportunity = {
            'opportunity_id': f"opp_{base_opportunity['lead_id']}",
            'profile_id': base_opportunity['profile_id'],
            'organization_name': base_opportunity['organization_name'],
            'ein': base_opportunity.get('external_data', {}).get('ein'),
            
            # Pipeline status
            'current_stage': current_stage,
            'stage_history': stage_history,
            
            # Scoring (if available)
            'scoring': scoring_data,
            
            # Stage-specific analysis
            'analysis': analysis_by_stage,
            
            # User assessments (initialize empty)
            'user_assessment': {
                'user_rating': None,
                'priority_level': None,
                'assessment_notes': None,
                'tags': [],
                'last_assessed_at': None
            },
            
            # Promotion history
            'promotion_history': promotion_history,
            
            # Metadata
            'source': base_opportunity.get('source'),
            'opportunity_type': base_opportunity.get('opportunity_type', 'grants'),
            'discovered_at': base_opportunity.get('discovered_at'),
            'last_updated': datetime.now().isoformat(),
            'status': base_opportunity.get('status', 'active'),
            
            # Legacy fields (preserved for compatibility)
            'legacy_lead_id': base_opportunity['lead_id'],
            'legacy_pipeline_stage': base_opportunity.get('pipeline_stage'),
            'description': base_opportunity.get('description'),
            'funding_amount': base_opportunity.get('funding_amount'),
            'program_name': base_opportunity.get('program_name')
        }
        
        return unified_opportunity
    
    def generate_profile_with_analytics(self, profile_id: str, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate profile.json with embedded analytics"""
        
        # Load existing profile data if available
        existing_profile_file = self.profiles_dir / f"{profile_id}.json"
        base_profile = {}
        
        if existing_profile_file.exists():
            try:
                with open(existing_profile_file, 'r', encoding='utf-8') as f:
                    base_profile = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing profile {profile_id}: {e}")
        
        # Compute analytics from opportunities
        analytics = self.compute_profile_analytics(opportunities)
        
        # Build enhanced profile
        profile = {
            'profile_id': profile_id,
            'organization_name': base_profile.get('organization_name', 'Unknown Organization'),
            'focus_areas': base_profile.get('focus_areas', []),
            'geographic_scope': base_profile.get('geographic_scope', 'National'),
            'ntee_codes': base_profile.get('ntee_codes', []),
            'created_at': base_profile.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat(),
            
            # Embedded analytics
            'analytics': analytics,
            
            # Recent activity summary
            'recent_activity': self.generate_recent_activity(opportunities)
        }
        
        return profile
    
    def compute_profile_analytics(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute analytics from opportunities"""
        
        if not opportunities:
            return self.empty_analytics()
        
        # Stage distribution
        stages_dist = defaultdict(int)
        for opp in opportunities:
            stages_dist[opp.get('current_stage', 'discovery')] += 1
        
        # Scoring statistics
        scores = [opp.get('scoring', {}).get('overall_score', 0) for opp in opportunities if opp.get('scoring')]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        high_potential_count = len([s for s in scores if s >= 0.80])
        auto_promotion_eligible = len([opp for opp in opportunities 
                                     if opp.get('scoring', {}).get('auto_promotion_eligible', False)])
        
        # Discovery statistics
        discovery_sessions = len(set(opp.get('discovered_at', '')[:10] for opp in opportunities if opp.get('discovered_at')))
        last_discovery = max((opp.get('discovered_at') for opp in opportunities if opp.get('discovered_at')), default=None)
        
        # Promotion statistics
        total_promotions = sum(len(opp.get('promotion_history', [])) for opp in opportunities)
        auto_promotions = sum(1 for opp in opportunities for promo in opp.get('promotion_history', []) 
                             if promo.get('decision_type') == 'auto_promote')
        
        return {
            'opportunity_count': len(opportunities),
            'stages_distribution': dict(stages_dist),
            'scoring_stats': {
                'avg_score': round(avg_score, 3),
                'high_potential_count': high_potential_count,
                'auto_promotion_eligible': auto_promotion_eligible,
                'last_scored': max((opp.get('scoring', {}).get('scored_at') for opp in opportunities 
                                   if opp.get('scoring', {}).get('scored_at')), default=None)
            },
            'discovery_stats': {
                'total_sessions': max(discovery_sessions, 1),
                'last_discovery': last_discovery,
                'last_session_results': len([opp for opp in opportunities if opp.get('discovered_at') and opp['discovered_at'].startswith(last_discovery[:10])]) if last_discovery else 0,
                'avg_results_per_session': len(opportunities) / max(discovery_sessions, 1)
            },
            'promotion_stats': {
                'total_promotions': total_promotions,
                'auto_promotions': auto_promotions,
                'manual_promotions': total_promotions - auto_promotions,
                'promotion_rate': round(total_promotions / len(opportunities), 2) if opportunities else 0.0
            }
        }
    
    def empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            'opportunity_count': 0,
            'stages_distribution': {},
            'scoring_stats': {
                'avg_score': 0.0,
                'high_potential_count': 0,
                'auto_promotion_eligible': 0,
                'last_scored': None
            },
            'discovery_stats': {
                'total_sessions': 0,
                'last_discovery': None,
                'last_session_results': 0,
                'avg_results_per_session': 0.0
            },
            'promotion_stats': {
                'total_promotions': 0,
                'auto_promotions': 0,
                'manual_promotions': 0,
                'promotion_rate': 0.0
            }
        }
    
    def generate_recent_activity(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recent activity summary"""
        activities = []
        
        # Add discovery sessions
        discovery_dates = {}
        for opp in opportunities:
            if opp.get('discovered_at'):
                date = opp['discovered_at'][:10]
                if date not in discovery_dates:
                    discovery_dates[date] = 0
                discovery_dates[date] += 1
        
        for date, count in sorted(discovery_dates.items(), reverse=True)[:3]:
            activities.append({
                'type': 'discovery_session',
                'date': f"{date}T12:00:00",
                'results': count,
                'source': 'Multiple Sources'
            })
        
        # Add recent promotions
        for opp in opportunities:
            for promo in opp.get('promotion_history', [])[-2:]:  # Last 2 promotions
                activities.append({
                    'type': 'auto_promotion' if promo.get('decision_type') == 'auto_promote' else 'manual_promotion',
                    'date': promo.get('promoted_at'),
                    'opportunity': opp.get('organization_name'),
                    'from_stage': promo.get('from_stage'),
                    'to_stage': promo.get('to_stage')
                })
        
        # Sort by date and return recent activities
        activities.sort(key=lambda x: x.get('date', ''), reverse=True)
        return activities[:5]
    
    def migrate_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> bool:
        """Migrate single profile to new structure"""
        try:
            logger.info(f"Migrating profile {profile_id} with {len(profile_data['opportunities'])} opportunities...")
            
            # Create profile directory
            profile_dir = self.data_dir / profile_id
            opportunities_dir = profile_dir / "opportunities"
            profile_dir.mkdir(parents=True, exist_ok=True)
            opportunities_dir.mkdir(exist_ok=True)
            
            # Consolidate opportunities
            opportunities = []
            for lead_id, stage_files in profile_data['opportunities'].items():
                try:
                    unified_opportunity = self.consolidate_opportunity_stages(stage_files)
                    opportunities.append(unified_opportunity)
                    
                    # Save individual opportunity file
                    opp_file = opportunities_dir / f"opportunity_{lead_id}.json"
                    with open(opp_file, 'w', encoding='utf-8') as f:
                        json.dump(unified_opportunity, f, indent=2, ensure_ascii=False)
                    
                    self.migration_stats['opportunities_consolidated'] += 1
                    self.migration_stats['stage_files_merged'] += len(stage_files)
                    
                except Exception as e:
                    logger.error(f"Failed to consolidate opportunity {lead_id}: {e}")
                    self.migration_stats['errors'].append(f"Opportunity {lead_id}: {str(e)}")
                    continue
            
            # Generate and save profile with analytics
            profile = self.generate_profile_with_analytics(profile_id, opportunities)
            profile_file = profile_dir / "profile.json"
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            self.migration_stats['profiles_processed'] += 1
            logger.info(f"Successfully migrated profile {profile_id}: {len(opportunities)} opportunities")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate profile {profile_id}: {e}")
            self.migration_stats['errors'].append(f"Profile {profile_id}: {str(e)}")
            return False
    
    def create_backup(self):
        """Create backup of current structure"""
        backup_dir = Path("data_backup_pre_migration")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        logger.info("Creating backup of current structure...")
        shutil.copytree(self.data_dir, backup_dir)
        logger.info(f"Backup created at {backup_dir}")
    
    def run_migration(self, dry_run: bool = True):
        """Run the complete migration"""
        logger.info(f"Starting migration ({'DRY RUN' if dry_run else 'EXECUTING'})...")
        
        # Analyze current structure
        analysis = self.analyze_current_structure()
        logger.info(f"Analysis complete: {analysis['summary']}")
        
        if dry_run:
            logger.info("=== DRY RUN ANALYSIS ===")
            logger.info(f"Profiles to migrate: {analysis['summary']['total_profiles']}")
            logger.info(f"Opportunities to consolidate: {analysis['summary']['total_unique_opportunities']}")
            logger.info(f"Files to process: {analysis['total_files']}")
            logger.info(f"File patterns: {dict(analysis['file_patterns'])}")
            
            # Show sample of what would be created
            for profile_id, profile_data in list(analysis['profiles'].items())[:2]:
                logger.info(f"\nProfile {profile_id}:")
                logger.info(f"  - Opportunities: {len(profile_data['opportunities'])}")
                for lead_id, stage_files in list(profile_data['opportunities'].items())[:3]:
                    logger.info(f"    - {lead_id}: {len(stage_files)} stage files -> 1 unified file")
            
            return analysis
        
        # Execute migration
        logger.info("EXECUTING MIGRATION...")
        
        # Create backup
        self.create_backup()
        
        # Migrate each profile
        for profile_id, profile_data in analysis['profiles'].items():
            self.migrate_profile(profile_id, profile_data)
        
        # Print migration summary
        logger.info("=== MIGRATION COMPLETE ===")
        logger.info(f"Profiles processed: {self.migration_stats['profiles_processed']}")
        logger.info(f"Opportunities consolidated: {self.migration_stats['opportunities_consolidated']}")
        logger.info(f"Stage files merged: {self.migration_stats['stage_files_merged']}")
        logger.info(f"Errors: {len(self.migration_stats['errors'])}")
        
        if self.migration_stats['errors']:
            logger.error("Migration errors:")
            for error in self.migration_stats['errors'][:10]:  # Show first 10 errors
                logger.error(f"  - {error}")
        
        return self.migration_stats


def main():
    parser = argparse.ArgumentParser(description='Migrate to unified opportunity architecture')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')
    parser.add_argument('--execute', action='store_true', help='Execute migration')
    parser.add_argument('--data-dir', default='data/profiles', help='Data directory path')
    
    args = parser.parse_args()
    
    if not (args.dry_run or args.execute):
        parser.print_help()
        print("\nPlease specify either --dry-run or --execute")
        return
    
    migrator = UnifiedArchitectureMigrator(args.data_dir)
    result = migrator.run_migration(dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"\nDry run complete. Found {result['summary']['total_profiles']} profiles to migrate.")
        print("Run with --execute to perform the migration.")
    else:
        print(f"\nMigration complete! Processed {result['profiles_processed']} profiles.")


if __name__ == "__main__":
    main()