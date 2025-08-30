#!/usr/bin/env python3
"""
Filesystem Consolidation Utility for Catalynx Grant Research Platform
Consolidates scattered files, cleans up cache, and organizes data structure
"""

import os
import shutil
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional

logger = logging.getLogger(__name__)


class FilesystemConsolidator:
    """
    Utility to consolidate and cleanup scattered files after database migration
    Maintains essential files while removing redundant cached data
    """
    
    def __init__(self, data_root: str = "data"):
        self.data_root = Path(data_root)
        self.consolidated_root = self.data_root / "consolidated"
        self.archive_root = self.data_root / "archive"
        
        # Create directories if they don't exist
        self.consolidated_root.mkdir(exist_ok=True)
        self.archive_root.mkdir(exist_ok=True)
        
        # Track operations for reporting
        self.operations_log = {
            'files_archived': [],
            'files_removed': [],
            'directories_cleaned': [],
            'space_saved_bytes': 0,
            'consolidation_date': datetime.now().isoformat()
        }
        
    def analyze_file_structure(self) -> Dict:
        """Analyze current file structure and identify consolidation opportunities"""
        analysis = {
            'total_files': 0,
            'total_size_bytes': 0,
            'file_types': {},
            'directory_sizes': {},
            'redundant_files': [],
            'cache_files': [],
            'backup_files': [],
            'profile_files': [],
            'log_files': []
        }
        
        try:
            for root, dirs, files in os.walk(self.data_root):
                root_path = Path(root)
                
                # Skip already consolidated directories
                if 'consolidated' in root or 'archive' in root:
                    continue
                    
                dir_size = 0
                
                for file in files:
                    file_path = root_path / file
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        analysis['total_files'] += 1
                        analysis['total_size_bytes'] += file_size
                        dir_size += file_size
                        
                        # Categorize file
                        file_ext = file_path.suffix.lower()
                        analysis['file_types'][file_ext] = analysis['file_types'].get(file_ext, 0) + 1
                        
                        # Identify file categories
                        relative_path = str(file_path.relative_to(self.data_root))
                        
                        if 'cache' in relative_path.lower():
                            analysis['cache_files'].append(str(file_path))
                        elif 'backup' in relative_path.lower():
                            analysis['backup_files'].append(str(file_path))
                        elif 'profile' in relative_path.lower() and file_ext == '.json':
                            analysis['profile_files'].append(str(file_path))
                        elif file_ext in ['.log', '.txt'] and 'log' in file.lower():
                            analysis['log_files'].append(str(file_path))
                        elif file.startswith('profile_') and 'opportunity_' in file:
                            analysis['redundant_files'].append(str(file_path))
                            
                # Record directory size
                if dir_size > 0:
                    analysis['directory_sizes'][str(root_path.relative_to(self.data_root))] = dir_size
                    
        except Exception as e:
            logger.error(f"Failed to analyze file structure: {e}")
            
        return analysis
    
    def consolidate_profile_data(self) -> int:
        """
        Consolidate profile and opportunity JSON files into archive
        Since data is now in database, these can be archived
        """
        files_consolidated = 0
        
        try:
            # Archive profile files
            profiles_dir = self.data_root / "profiles"
            if profiles_dir.exists():
                archive_profiles = self.archive_root / "legacy_profiles" / datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_profiles.mkdir(parents=True, exist_ok=True)
                
                # Copy profiles to archive
                if (profiles_dir / "profiles").exists():
                    shutil.copytree(profiles_dir / "profiles", archive_profiles / "profiles")
                    files_consolidated += len(list((profiles_dir / "profiles").glob("*.json")))
                    
                if (profiles_dir / "opportunities").exists():
                    shutil.copytree(profiles_dir / "opportunities", archive_profiles / "opportunities") 
                    files_consolidated += len(list((profiles_dir / "opportunities").glob("*.json")))
                    
                # Remove original after successful archive
                shutil.rmtree(profiles_dir)
                self.operations_log['directories_cleaned'].append(str(profiles_dir))
                
                logger.info(f"Archived {files_consolidated} profile/opportunity files to {archive_profiles}")
                
        except Exception as e:
            logger.error(f"Failed to consolidate profile data: {e}")
            
        return files_consolidated
    
    def cleanup_cache_files(self) -> int:
        """Clean up scattered cache files and organize essential cache"""
        files_cleaned = 0
        
        try:
            cache_dir = self.data_root / "cache"
            if cache_dir.exists():
                # Archive cache metadata but remove cached responses
                essential_cache = self.consolidated_root / "cache"
                essential_cache.mkdir(exist_ok=True)
                
                # Keep cache metadata for reference
                metadata_file = cache_dir / "cache_metadata.json"
                if metadata_file.exists():
                    shutil.copy2(metadata_file, essential_cache / "cache_metadata.json")
                    
                # Count files before cleanup
                for file_path in cache_dir.rglob("*"):
                    if file_path.is_file():
                        files_cleaned += 1
                        self.operations_log['space_saved_bytes'] += file_path.stat().st_size
                        
                # Remove cache directory
                shutil.rmtree(cache_dir)
                self.operations_log['directories_cleaned'].append(str(cache_dir))
                
                logger.info(f"Cleaned {files_cleaned} cache files, kept metadata")
                
        except Exception as e:
            logger.error(f"Failed to cleanup cache files: {e}")
            
        return files_cleaned
    
    def consolidate_logs_and_monitoring(self) -> int:
        """Consolidate log files and monitoring data"""
        files_consolidated = 0
        
        try:
            # Consolidate monitoring data
            monitoring_dir = self.data_root / "monitoring"
            if monitoring_dir.exists():
                consolidated_monitoring = self.consolidated_root / "monitoring"
                consolidated_monitoring.mkdir(exist_ok=True)
                
                # Keep only recent monitoring data (last 30 days)
                cutoff_date = datetime.now().timestamp() - (30 * 24 * 3600)
                
                for file_path in monitoring_dir.rglob("*.json"):
                    if file_path.is_file():
                        if file_path.stat().st_mtime > cutoff_date:
                            # Keep recent file
                            relative_path = file_path.relative_to(monitoring_dir)
                            dest_path = consolidated_monitoring / relative_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(file_path, dest_path)
                        files_consolidated += 1
                        
                # Remove original
                shutil.rmtree(monitoring_dir)
                self.operations_log['directories_cleaned'].append(str(monitoring_dir))
                
            # Consolidate audit logs
            audit_logs_dir = self.data_root / "audit_logs"
            if audit_logs_dir.exists():
                consolidated_logs = self.consolidated_root / "audit_logs" 
                consolidated_logs.mkdir(exist_ok=True)
                
                # Keep only recent audit logs
                for file_path in audit_logs_dir.rglob("*.log"):
                    if file_path.is_file():
                        if file_path.stat().st_mtime > cutoff_date:
                            shutil.copy2(file_path, consolidated_logs / file_path.name)
                        files_consolidated += 1
                        
                # Remove original
                shutil.rmtree(audit_logs_dir)
                self.operations_log['directories_cleaned'].append(str(audit_logs_dir))
                
            logger.info(f"Consolidated {files_consolidated} log and monitoring files")
            
        except Exception as e:
            logger.error(f"Failed to consolidate logs: {e}")
            
        return files_consolidated
    
    def organize_essential_data(self) -> int:
        """Organize essential data that should be kept"""
        files_organized = 0
        
        try:
            essential_data = self.consolidated_root / "essential"
            essential_data.mkdir(exist_ok=True)
            
            # Keep source data structure for reference
            source_data_dir = self.data_root / "source_data"
            if source_data_dir.exists():
                # Copy structure but not all files (too large)
                essential_source = essential_data / "source_data_structure"
                essential_source.mkdir(exist_ok=True)
                
                # Just copy structure info, not actual files
                structure_info = {
                    'directories': [],
                    'file_counts': {},
                    'last_updated': datetime.now().isoformat()
                }
                
                for root, dirs, files in os.walk(source_data_dir):
                    rel_path = Path(root).relative_to(source_data_dir)
                    structure_info['directories'].append(str(rel_path))
                    structure_info['file_counts'][str(rel_path)] = len(files)
                    
                with open(essential_source / "structure_info.json", 'w') as f:
                    json.dump(structure_info, f, indent=2)
                    
                files_organized += 1
                
            # Keep cost tracking data
            cost_tracking_dir = self.data_root / "cost_tracking"
            if cost_tracking_dir.exists():
                shutil.copytree(cost_tracking_dir, essential_data / "cost_tracking")
                files_organized += len(list(cost_tracking_dir.rglob("*")))
                shutil.rmtree(cost_tracking_dir)
                self.operations_log['directories_cleaned'].append(str(cost_tracking_dir))
                
            # Keep essential config files
            config_files = ['data_structure.json', 'README.md']
            for config_file in config_files:
                config_path = self.data_root / config_file
                if config_path.exists():
                    shutil.copy2(config_path, essential_data / config_file)
                    files_organized += 1
                    
            logger.info(f"Organized {files_organized} essential data files")
            
        except Exception as e:
            logger.error(f"Failed to organize essential data: {e}")
            
        return files_organized
    
    def create_consolidation_summary(self) -> Dict:
        """Create summary of consolidation operations"""
        
        # Calculate space savings
        space_saved_mb = self.operations_log['space_saved_bytes'] / (1024 * 1024)
        
        summary = {
            'consolidation_completed': True,
            'consolidation_date': self.operations_log['consolidation_date'],
            'space_saved_mb': round(space_saved_mb, 2),
            'directories_cleaned': len(self.operations_log['directories_cleaned']),
            'files_processed': len(self.operations_log['files_archived']) + len(self.operations_log['files_removed']),
            'new_structure': {
                'database': 'data/catalynx.db - Primary data store',
                'consolidated': 'data/consolidated/ - Essential files only',
                'archive': 'data/archive/ - Historical data backup'
            },
            'cleanup_recommendations': [
                'Verify database integrity before removing archive',
                'Set up automated backup of catalynx.db',
                'Monitor consolidated directory size',
                'Review archive files quarterly for cleanup'
            ]
        }
        
        # Save summary
        summary_path = self.consolidated_root / "consolidation_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"Consolidation summary saved to {summary_path}")
        return summary
    
    def run_full_consolidation(self) -> Dict:
        """Run complete filesystem consolidation"""
        logger.info("Starting filesystem consolidation...")
        
        try:
            # Analyze current structure
            analysis = self.analyze_file_structure()
            logger.info(f"Analysis: {analysis['total_files']} files, {analysis['total_size_bytes']/1024/1024:.2f} MB")
            
            # Run consolidation steps
            profile_files = self.consolidate_profile_data()
            cache_files = self.cleanup_cache_files()
            log_files = self.consolidate_logs_and_monitoring()
            essential_files = self.organize_essential_data()
            
            # Create summary
            summary = self.create_consolidation_summary()
            summary['analysis'] = analysis
            summary['files_consolidated'] = {
                'profile_files': profile_files,
                'cache_files': cache_files,
                'log_files': log_files,
                'essential_files': essential_files
            }
            
            logger.info(f"Consolidation completed: {summary['space_saved_mb']} MB saved")
            return summary
            
        except Exception as e:
            logger.error(f"Consolidation failed: {e}")
            return {'consolidation_completed': False, 'error': str(e)}


def main():
    """Main consolidation execution"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    consolidator = FilesystemConsolidator()
    
    # Ask for confirmation before proceeding
    print("⚠️  This will consolidate and cleanup the data directory structure.")
    print("🔍 Profile and opportunity data has been migrated to catalynx.db")
    print("📦 Files will be archived and cache will be cleaned")
    print("🔄 This operation cannot be easily undone.")
    
    response = input("\nProceed with consolidation? (y/N): ").lower().strip()
    
    if response in ['y', 'yes']:
        result = consolidator.run_full_consolidation()
        
        if result.get('consolidation_completed'):
            print("\n✅ Consolidation completed successfully!")
            print(f"💾 Space saved: {result['space_saved_mb']} MB")
            print(f"📁 Directories cleaned: {result['directories_cleaned']}")
            print(f"📄 Files processed: {result['files_processed']}")
            print("\n📋 New structure:")
            for key, desc in result['new_structure'].items():
                print(f"  - {desc}")
        else:
            print(f"\n❌ Consolidation failed: {result.get('error', 'Unknown error')}")
    else:
        print("\n🚫 Consolidation cancelled by user")


if __name__ == "__main__":
    main()