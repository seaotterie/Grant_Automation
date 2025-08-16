#!/usr/bin/env python3
"""
Nonprofit Data Migration

Migrates nonprofit organization data from hash-based cache to EIN-based structure.
"""

import json
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import logging

from .migration_framework import DataMigrationFramework, MigrationStep
from .entity_extractor import EntityExtractor, EntityType


class NonprofitMigrator:
    """
    Migrates nonprofit data to EIN-based directory structure
    """
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.source_cache_dir = self.base_path / "cache" / "api_response"
        self.target_nonprofits_dir = self.base_path / "source_data" / "nonprofits"
        self.logger = logging.getLogger(__name__)
        
        # Initialize migration framework and entity extractor
        self.migration_framework = DataMigrationFramework(self.base_path)
        self.entity_extractor = EntityExtractor()
        
        # Track EIN mappings
        self.ein_mappings: Dict[str, Dict[str, Any]] = {}
    
    def analyze_nonprofit_cache(self) -> Dict[str, Any]:
        """
        Analyze current cache to identify nonprofit data files and EINs
        """
        self.logger.info("Analyzing nonprofit cache files...")
        
        identifications = self.entity_extractor.analyze_cache_directory(self.source_cache_dir)
        
        # Filter for nonprofit entities only
        nonprofit_files = {
            file_path: identification 
            for file_path, identification in identifications.items()
            if identification.entity_type == EntityType.NONPROFIT and identification.confidence > 0.5
        }
        
        self.logger.info(f"Found {len(nonprofit_files)} nonprofit cache files")
        
        # Group by EIN
        ein_groups = {}
        for file_path, identification in nonprofit_files.items():
            ein = identification.entity_id
            if ein not in ein_groups:
                ein_groups[ein] = []
            
            ein_groups[ein].append({
                'file_path': file_path,
                'identification': identification
            })
        
        self.logger.info(f"Organized into {len(ein_groups)} unique EINs")
        return ein_groups
    
    def extract_nonprofit_metadata(self, cache_file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from nonprofit cache file
        """
        try:
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract common nonprofit fields
            metadata = {
                'organization_name': self._extract_org_name(data),
                'ntee_code': self._extract_field(data, ['ntee_cd', 'ntee_code', 'ntee']),
                'ruling_date': self._extract_field(data, ['ruling_dt', 'ruling_date']),
                'tax_exempt_status': self._extract_field(data, ['tax_exempt_status', 'exemption_type']),
                'subsection_code': self._extract_field(data, ['subsection_cd', 'subsection_code']),
                'classification_codes': self._extract_field(data, ['classification_codes']),
                'income_amount': self._extract_field(data, ['income_amt', 'revenue', 'total_revenue']),
                'revenue_amount': self._extract_field(data, ['revenue_amt', 'revenue', 'total_revenue']),
                'asset_amount': self._extract_field(data, ['asset_amt', 'assets', 'total_assets']),
                'activity_codes': self._extract_field(data, ['activity_codes']),
                'foundation_code': self._extract_field(data, ['foundation_cd', 'foundation_code']),
                'organization_code': self._extract_field(data, ['organization_cd', 'organization_code']),
                'deductibility_code': self._extract_field(data, ['deductibility_cd', 'deductibility_code']),
                'affiliation_code': self._extract_field(data, ['affiliation_cd', 'affiliation_code']),
                'state': self._extract_field(data, ['state', 'state_cd']),
                'city': self._extract_field(data, ['city']),
                'zip_code': self._extract_field(data, ['zip_cd', 'zip_code', 'zip']),
                'group_exemption_number': self._extract_field(data, ['group_exemption_num']),
                'data_source': self._determine_data_source(data),
                'last_updated': datetime.now().isoformat()
            }
            
            # Clean up None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {cache_file_path}: {e}")
            return {}
    
    def _extract_org_name(self, data: Dict) -> Optional[str]:
        """Extract organization name from various possible fields"""
        name_fields = [
            'name', 'organization_name', 'org_name', 'entity_name',
            'legal_name', 'doing_business_as_name', 'taxpayer_name'
        ]
        
        for field in name_fields:
            value = self._extract_field(data, [field])
            if value and isinstance(value, str) and len(value.strip()) > 0:
                return value.strip()
        
        return None
    
    def _extract_field(self, data: Dict, field_names: List[str]) -> Any:
        """Extract field value from data, trying multiple field names"""
        if not isinstance(data, dict):
            return None
        
        for field_name in field_names:
            # Try direct access
            if field_name in data:
                return data[field_name]
            
            # Try case-insensitive access
            for key, value in data.items():
                if key.lower() == field_name.lower():
                    return value
            
            # Try nested access
            for key, value in data.items():
                if isinstance(value, dict):
                    nested_result = self._extract_field(value, [field_name])
                    if nested_result is not None:
                        return nested_result
        
        return None
    
    def _determine_data_source(self, data: Dict) -> str:
        """Determine the source of the data (IRS, ProPublica, etc.)"""
        data_str = json.dumps(data, default=str).lower()
        
        if 'propublica' in data_str:
            return 'propublica'
        elif 'irs' in data_str or 'business_master_file' in data_str:
            return 'irs_bmf'
        elif '990' in data_str:
            return 'form_990'
        else:
            return 'unknown'
    
    def create_nonprofit_directory_structure(self, ein: str, metadata: Dict[str, Any]) -> Path:
        """
        Create directory structure for a nonprofit organization
        """
        nonprofit_dir = self.target_nonprofits_dir / ein
        nonprofit_dir.mkdir(exist_ok=True, parents=True)
        
        # Create subdirectories
        subdirs = ['filings', 'schedules']
        for subdir in subdirs:
            (nonprofit_dir / subdir).mkdir(exist_ok=True)
        
        # Create metadata file
        metadata_file = nonprofit_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return nonprofit_dir
    
    def migrate_nonprofit_file(self, source_file: Path, target_dir: Path, data_source: str) -> str:
        """
        Migrate a single nonprofit cache file to the EIN-based structure
        """
        # Determine target filename based on data source
        if data_source == 'irs_bmf':
            target_filename = 'bmf.json'
        elif data_source == 'propublica':
            target_filename = 'propublica.json'
        elif data_source == 'form_990':
            # Try to extract year from filename or content
            target_filename = 'form_990.json'  # Could be enhanced with year
        else:
            # Use hash-based filename as fallback
            target_filename = f'cache_{source_file.stem}.json'
        
        target_file = target_dir / target_filename
        
        # Copy file with data validation
        shutil.copy2(source_file, target_file)
        
        return target_filename
    
    def generate_migration_steps(self) -> List[MigrationStep]:
        """
        Generate migration steps for all nonprofit data
        """
        steps = []
        
        # Analyze cache files
        ein_groups = self.analyze_nonprofit_cache()
        
        for ein, file_group in ein_groups.items():
            # Create step for each EIN directory
            step_id = f"migrate_nonprofit_{ein}"
            
            # Use first file for primary metadata extraction
            primary_file_info = file_group[0]
            primary_file_path = Path(primary_file_info['file_path'])
            
            target_dir = self.target_nonprofits_dir / ein
            
            step = MigrationStep(
                step_id=step_id,
                description=f"Migrate nonprofit data for EIN {ein}",
                source_path=str(primary_file_path),  # Individual file, not directory
                target_path=str(target_dir),
                transform_func=lambda src, tgt, file_group=file_group, ein=ein: self._migrate_ein_group(file_group, ein),
                validation_func=lambda src, tgt, ein=ein: self._validate_nonprofit_migration(Path(tgt), ein)
            )
            
            steps.append(step)
        
        return steps
    
    def _migrate_ein_group(self, file_group: List[Dict], ein: str) -> int:
        """
        Migrate all files for a specific EIN
        """
        files_processed = 0
        
        # Extract metadata from first file
        primary_file_path = Path(file_group[0]['file_path'])
        metadata = self.extract_nonprofit_metadata(primary_file_path)
        metadata['ein'] = ein
        metadata['total_cache_files'] = len(file_group)
        
        # Create directory structure
        target_dir = self.create_nonprofit_directory_structure(ein, metadata)
        
        # Migrate each cache file
        migrated_files = []
        for file_info in file_group:
            source_file = Path(file_info['file_path'])
            data_source = metadata.get('data_source', 'unknown')
            
            try:
                target_filename = self.migrate_nonprofit_file(source_file, target_dir, data_source)
                migrated_files.append(target_filename)
                files_processed += 1
                
                self.logger.info(f"Migrated {source_file.name} -> {ein}/{target_filename}")
                
            except Exception as e:
                self.logger.error(f"Error migrating {source_file}: {e}")
        
        # Update metadata with migrated files list
        metadata['migrated_files'] = migrated_files
        metadata_file = target_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update EIN mappings
        self.ein_mappings[ein] = metadata
        
        return files_processed
    
    def _validate_nonprofit_migration(self, target_dir: Path, ein: str) -> bool:
        """
        Validate migration for a nonprofit EIN directory
        """
        try:
            # Check directory exists
            if not target_dir.exists():
                return False
            
            # Check metadata file exists
            metadata_file = target_dir / 'metadata.json'
            if not metadata_file.exists():
                return False
            
            # Validate metadata content
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            if metadata.get('ein') != ein:
                return False
            
            # Check that migrated files exist
            migrated_files = metadata.get('migrated_files', [])
            for filename in migrated_files:
                if not (target_dir / filename).exists():
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error for EIN {ein}: {e}")
            return False
    
    def execute_migration(self) -> bool:
        """
        Execute the complete nonprofit data migration
        """
        self.logger.info("Starting nonprofit data migration...")
        
        # Generate migration steps
        migration_steps = self.generate_migration_steps()
        
        if not migration_steps:
            self.logger.warning("No nonprofit migration steps generated")
            return True
        
        # Execute migration
        migration_id = f"nonprofit_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success = self.migration_framework.execute_migration(migration_steps, migration_id)
        
        if success:
            # Create nonprofit index
            self._create_nonprofit_index()
            self.logger.info("Nonprofit data migration completed successfully")
        else:
            self.logger.error("Nonprofit data migration failed")
        
        return success
    
    def _create_nonprofit_index(self):
        """
        Create index file for nonprofit organizations
        """
        nonprofit_index = {
            "version": "1.0.0",
            "description": "Index of nonprofit organizations by EIN",
            "last_updated": datetime.now().isoformat(),
            "total_organizations": len(self.ein_mappings),
            "organizations": {}
        }
        
        for ein, metadata in self.ein_mappings.items():
            nonprofit_index["organizations"][ein] = {
                "name": metadata.get('organization_name', 'Unknown'),
                "ntee_code": metadata.get('ntee_code'),
                "state": metadata.get('state'),
                "data_files": metadata.get('migrated_files', []),
                "last_updated": metadata.get('last_updated')
            }
        
        index_file = self.target_nonprofits_dir / "index.json"
        with open(index_file, 'w') as f:
            json.dump(nonprofit_index, f, indent=2)
        
        self.logger.info(f"Created nonprofit index with {len(self.ein_mappings)} organizations")


if __name__ == "__main__":
    # Example usage
    migrator = NonprofitMigrator(Path("data"))
    success = migrator.execute_migration()
    
    if success:
        print("Nonprofit migration completed successfully")
    else:
        print("Nonprofit migration failed")