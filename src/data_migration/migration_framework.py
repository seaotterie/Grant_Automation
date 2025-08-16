#!/usr/bin/env python3
"""
Data Migration Framework for Entity-Based Architecture Refactoring

This framework provides:
- Safe data migration with rollback capabilities
- Data validation and integrity checking
- Progress tracking and logging
- Backup and restore functionality
"""

import json
import shutil
import hashlib
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import traceback


class MigrationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationStep:
    """Individual migration step definition"""
    step_id: str
    description: str
    source_path: str
    target_path: str
    validation_func: Optional[Callable] = None
    transform_func: Optional[Callable] = None
    rollback_func: Optional[Callable] = None


@dataclass
class MigrationRecord:
    """Migration execution record for tracking and rollback"""
    migration_id: str
    step_id: str
    status: MigrationStatus
    started_at: datetime
    completed_at: Optional[datetime]
    source_path: str
    target_path: str
    backup_path: Optional[str]
    checksum_source: Optional[str]
    checksum_target: Optional[str]
    error_message: Optional[str]
    files_processed: int = 0
    files_failed: int = 0


class DataMigrationFramework:
    """
    Core migration framework with rollback and validation capabilities
    """
    
    def __init__(self, base_data_path: Path, backup_path: Path = None):
        self.base_data_path = Path(base_data_path)
        self.backup_path = backup_path or self.base_data_path / "backups"
        self.migration_log_path = self.base_data_path / "migration_logs"
        
        # Create required directories
        self.backup_path.mkdir(exist_ok=True, parents=True)
        self.migration_log_path.mkdir(exist_ok=True, parents=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Migration tracking
        self.migration_records: List[MigrationRecord] = []
        self.current_migration_id: Optional[str] = None
    
    def _setup_logging(self) -> logging.Logger:
        """Setup migration-specific logging"""
        logger = logging.getLogger("data_migration")
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = self.migration_log_path / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        if not file_path.exists():
            return ""
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def create_backup(self, source_path: Path, migration_id: str, step_id: str = "") -> Path:
        """Create backup of source data before migration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.backup_path / f"{migration_id}_{timestamp}"
        backup_dir.mkdir(exist_ok=True, parents=True)
        
        if source_path.is_file():
            backup_file = backup_dir / f"{step_id}_{source_path.name}" if step_id else source_path.name
            shutil.copy2(source_path, backup_file)
            return backup_file
        elif source_path.is_dir():
            backup_subdir = backup_dir / f"{step_id}_{source_path.name}" if step_id else source_path.name
            if backup_subdir.exists():
                # If backup already exists, use unique name
                counter = 1
                while backup_subdir.exists():
                    backup_subdir = backup_dir / f"{step_id}_{source_path.name}_{counter}"
                    counter += 1
            shutil.copytree(source_path, backup_subdir)
            return backup_subdir
        
        return backup_dir
    
    def validate_migration_step(self, record: MigrationRecord, step: MigrationStep) -> bool:
        """Validate a completed migration step"""
        try:
            # Check target path exists
            target_path = Path(record.target_path)
            if not target_path.exists():
                self.logger.error(f"Target path does not exist: {target_path}")
                return False
            
            # Verify checksum if available
            if record.checksum_target:
                current_checksum = self.calculate_checksum(target_path) if target_path.is_file() else ""
                if current_checksum != record.checksum_target:
                    self.logger.error(f"Checksum mismatch for {target_path}")
                    return False
            
            # Run custom validation function
            if step.validation_func:
                if not step.validation_func(record.source_path, record.target_path):
                    self.logger.error(f"Custom validation failed for step {step.step_id}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error for step {step.step_id}: {e}")
            return False
    
    def execute_migration_step(self, step: MigrationStep, migration_id: str) -> MigrationRecord:
        """Execute a single migration step with full tracking"""
        record = MigrationRecord(
            migration_id=migration_id,
            step_id=step.step_id,
            status=MigrationStatus.IN_PROGRESS,
            started_at=datetime.now(),
            completed_at=None,
            source_path=step.source_path,
            target_path=step.target_path,
            backup_path=None,
            checksum_source=None,
            checksum_target=None,
            error_message=None
        )
        
        try:
            self.logger.info(f"Starting migration step: {step.step_id} - {step.description}")
            
            source_path = Path(step.source_path)
            target_path = Path(step.target_path)
            
            # Calculate source checksum
            if source_path.exists() and source_path.is_file():
                record.checksum_source = self.calculate_checksum(source_path)
            
            # Create backup
            if source_path.exists():
                backup_path = self.create_backup(source_path, migration_id, step.step_id)
                record.backup_path = str(backup_path)
                self.logger.info(f"Created backup at: {backup_path}")
            
            # Ensure target directory exists
            target_path.parent.mkdir(exist_ok=True, parents=True)
            
            # Execute transformation or simple copy
            if step.transform_func:
                # Custom transformation
                files_processed = step.transform_func(source_path, target_path)
                record.files_processed = files_processed
            else:
                # Simple copy operation
                if source_path.is_file():
                    shutil.copy2(source_path, target_path)
                    record.files_processed = 1
                elif source_path.is_dir():
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
                    record.files_processed = len(list(target_path.rglob("*")))
            
            # Calculate target checksum
            if target_path.exists() and target_path.is_file():
                record.checksum_target = self.calculate_checksum(target_path)
            
            # Validate migration
            if self.validate_migration_step(record, step):
                record.status = MigrationStatus.COMPLETED
                record.completed_at = datetime.now()
                self.logger.info(f"Migration step completed successfully: {step.step_id}")
            else:
                record.status = MigrationStatus.FAILED
                record.error_message = "Validation failed"
                self.logger.error(f"Migration step validation failed: {step.step_id}")
            
        except Exception as e:
            record.status = MigrationStatus.FAILED
            record.error_message = str(e)
            self.logger.error(f"Migration step failed: {step.step_id} - {e}")
            self.logger.error(traceback.format_exc())
        
        self.migration_records.append(record)
        return record
    
    def rollback_migration_step(self, record: MigrationRecord) -> bool:
        """Rollback a migration step using backup"""
        try:
            if not record.backup_path:
                self.logger.error(f"No backup available for rollback: {record.step_id}")
                return False
            
            backup_path = Path(record.backup_path)
            target_path = Path(record.target_path)
            
            if not backup_path.exists():
                self.logger.error(f"Backup path does not exist: {backup_path}")
                return False
            
            # Remove current target
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                elif target_path.is_dir():
                    shutil.rmtree(target_path)
            
            # Restore from backup
            if backup_path.is_file():
                shutil.copy2(backup_path, target_path)
            elif backup_path.is_dir():
                shutil.copytree(backup_path, target_path)
            
            record.status = MigrationStatus.ROLLED_BACK
            self.logger.info(f"Successfully rolled back migration step: {record.step_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed for step {record.step_id}: {e}")
            return False
    
    def execute_migration(self, steps: List[MigrationStep], migration_id: str) -> bool:
        """Execute a complete migration with rollback on failure"""
        self.current_migration_id = migration_id
        self.logger.info(f"Starting migration: {migration_id}")
        
        completed_steps = []
        
        try:
            for step in steps:
                record = self.execute_migration_step(step, migration_id)
                
                if record.status == MigrationStatus.COMPLETED:
                    completed_steps.append(record)
                else:
                    # Migration step failed, rollback all completed steps
                    self.logger.error(f"Migration failed at step: {step.step_id}")
                    self.logger.info("Initiating rollback of completed steps...")
                    
                    for completed_record in reversed(completed_steps):
                        self.rollback_migration_step(completed_record)
                    
                    return False
            
            self.logger.info(f"Migration completed successfully: {migration_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration framework error: {e}")
            self.logger.error(traceback.format_exc())
            return False
        finally:
            # Save migration log
            self.save_migration_log(migration_id)
    
    def save_migration_log(self, migration_id: str):
        """Save migration records to JSON log file"""
        log_file = self.migration_log_path / f"{migration_id}_records.json"
        
        records_data = []
        for record in self.migration_records:
            record_dict = asdict(record)
            # Convert datetime objects to strings
            if record_dict['started_at']:
                record_dict['started_at'] = record_dict['started_at'].isoformat()
            if record_dict['completed_at']:
                record_dict['completed_at'] = record_dict['completed_at'].isoformat()
            records_data.append(record_dict)
        
        with open(log_file, 'w') as f:
            json.dump({
                'migration_id': migration_id,
                'total_steps': len(self.migration_records),
                'completed_steps': len([r for r in self.migration_records if r.status == MigrationStatus.COMPLETED]),
                'failed_steps': len([r for r in self.migration_records if r.status == MigrationStatus.FAILED]),
                'records': records_data
            }, f, indent=2)
        
        self.logger.info(f"Migration log saved: {log_file}")


def extract_ein_from_filename(filename: str) -> Optional[str]:
    """Extract EIN from various filename patterns"""
    # Common patterns: ein_123456789.json, 123456789_data.json, etc.
    import re
    
    # Pattern for 9-digit EIN
    ein_pattern = r'(\d{9})'
    match = re.search(ein_pattern, filename)
    if match:
        return match.group(1)
    
    return None


def extract_opportunity_id_from_filename(filename: str) -> Optional[str]:
    """Extract opportunity ID from government opportunity filenames"""
    # Patterns for opportunity IDs vary by source
    import re
    
    # Grants.gov pattern: typically alphanumeric
    if 'grants_gov' in filename.lower():
        pattern = r'([A-Z0-9\-]+)'
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    # USASpending pattern: typically numeric
    if 'usaspending' in filename.lower():
        pattern = r'(\d+)'
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    return None


def create_entity_directories(base_path: Path):
    """Create the new entity-based directory structure"""
    directories = [
        "source_data/nonprofits",
        "source_data/foundations", 
        "source_data/corporations",
        "source_data/government/federal/grants_gov",
        "source_data/government/federal/usaspending",
        "source_data/government/state/virginia/agencies",
        "source_data/government/state/virginia/historical_awards",
        "cache/networks",
        "cache/indices", 
        "cache/market_data",
        "profiles/analysis"
    ]
    
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(exist_ok=True, parents=True)
    
    return [base_path / d for d in directories]


if __name__ == "__main__":
    # Example usage and testing
    base_path = Path("data")
    migration_framework = DataMigrationFramework(base_path)
    
    # Create new directory structure
    created_dirs = create_entity_directories(base_path)
    print(f"Created {len(created_dirs)} directories for new data structure")