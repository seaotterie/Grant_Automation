#!/usr/bin/env python3
"""
Automated Backup Scheduler
Extends the existing backup system with automated scheduling and retention management
"""

import asyncio
import logging
import schedule
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Import existing database components
try:
    from src.database.database_manager import DatabaseManager
    from src.database.query_interface import DatabaseQueryInterface, QueryFilter
    from src.core.ai_cost_tracker import get_cost_tracker
except ImportError:
    from database.database_manager import DatabaseManager
    from database.query_interface import DatabaseQueryInterface, QueryFilter
    from core.ai_cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)


class BackupFrequency(Enum):
    """Backup frequency options"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class BackupConfiguration:
    """Configuration for automated backups"""
    frequency: BackupFrequency = BackupFrequency.DAILY
    retention_days: int = 30
    backup_directory: str = "data/consolidated/backups"
    include_exports: bool = True
    include_cost_reports: bool = True
    compress_backups: bool = False
    max_backup_size_mb: int = 1000
    notification_enabled: bool = True
    
    
@dataclass 
class BackupResult:
    """Result of a backup operation"""
    success: bool
    backup_path: str
    file_size: int
    records_backed_up: int
    duration_seconds: float
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AutomatedBackupScheduler:
    """
    Automated backup scheduler that extends the existing backup system
    Provides scheduling, retention management, and monitoring
    """
    
    def __init__(self, config: BackupConfiguration, database_path: str = "data/catalynx.db"):
        self.config = config
        self.database_path = database_path
        self.db = DatabaseManager(database_path)
        self.qi = DatabaseQueryInterface(database_path)
        self.cost_tracker = get_cost_tracker()
        
        # Setup backup directory
        self.backup_dir = Path(config.backup_directory)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup tracking
        self.backup_history: List[BackupResult] = []
        self.is_running = False
        self.scheduler_thread = None
        
        logger.info(f"Automated backup scheduler initialized: {config.frequency.value} backups, {config.retention_days} day retention")
    
    def start_scheduler(self) -> bool:
        """Start the automated backup scheduler"""
        try:
            if self.is_running:
                logger.warning("Backup scheduler is already running")
                return False
            
            # Clear any existing schedule
            schedule.clear()
            
            # Schedule backups based on frequency
            if self.config.frequency == BackupFrequency.HOURLY:
                schedule.every().hour.do(self._perform_scheduled_backup)
            elif self.config.frequency == BackupFrequency.DAILY:
                schedule.every().day.at("02:00").do(self._perform_scheduled_backup)
            elif self.config.frequency == BackupFrequency.WEEKLY:
                schedule.every().sunday.at("01:00").do(self._perform_scheduled_backup)
            elif self.config.frequency == BackupFrequency.MONTHLY:
                schedule.every().month.do(self._perform_scheduled_backup)
            
            # Schedule daily cleanup
            schedule.every().day.at("03:00").do(self._cleanup_old_backups)
            
            self.is_running = True
            
            # Start scheduler in background thread
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info(f"Backup scheduler started: {self.config.frequency.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start backup scheduler: {e}")
            return False
    
    def stop_scheduler(self) -> bool:
        """Stop the automated backup scheduler"""
        try:
            self.is_running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            logger.info("Backup scheduler stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop backup scheduler: {e}")
            return False
    
    def create_manual_backup(self, backup_type: str = "manual") -> BackupResult:
        """Create a manual backup immediately"""
        return self._create_backup(backup_type)
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup system status"""
        try:
            # Get recent backups
            recent_backups = self.backup_history[-10:] if self.backup_history else []
            
            # Calculate statistics
            total_backups = len(self.backup_history)
            successful_backups = sum(1 for b in self.backup_history if b.success)
            success_rate = (successful_backups / total_backups * 100) if total_backups > 0 else 0
            
            # Get backup directory info
            backup_files = list(self.backup_dir.glob("*.db"))
            total_backup_size = sum(f.stat().st_size for f in backup_files if f.exists())
            
            # Get last backup info
            last_backup = self.backup_history[-1] if self.backup_history else None
            
            return {
                "scheduler_running": self.is_running,
                "backup_frequency": self.config.frequency.value,
                "retention_days": self.config.retention_days,
                "total_backups_created": total_backups,
                "success_rate_percent": round(success_rate, 1),
                "total_backup_size_mb": round(total_backup_size / (1024*1024), 2),
                "backup_directory": str(self.backup_dir),
                "backup_files_count": len(backup_files),
                "last_backup": {
                    "timestamp": last_backup.timestamp.isoformat() if last_backup else None,
                    "success": last_backup.success if last_backup else None,
                    "size_mb": round(last_backup.file_size / (1024*1024), 2) if last_backup else None,
                    "records": last_backup.records_backed_up if last_backup else None
                } if last_backup else None,
                "recent_backups": [
                    {
                        "timestamp": b.timestamp.isoformat(),
                        "success": b.success,
                        "size_mb": round(b.file_size / (1024*1024), 2),
                        "duration_seconds": b.duration_seconds
                    } for b in recent_backups
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return {"error": str(e)}
    
    def cleanup_old_backups(self, dry_run: bool = False) -> Dict[str, Any]:
        """Clean up old backups based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            
            backup_files = list(self.backup_dir.glob("catalynx_backup_*.db"))
            files_to_delete = []
            total_size_to_free = 0
            
            for backup_file in backup_files:
                # Extract timestamp from filename
                try:
                    timestamp_str = backup_file.stem.split("_")[-2] + "_" + backup_file.stem.split("_")[-1]
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if file_date < cutoff_date:
                        files_to_delete.append(backup_file)
                        total_size_to_free += backup_file.stat().st_size
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse timestamp from {backup_file}: {e}")
            
            cleanup_result = {
                "files_to_delete": len(files_to_delete),
                "space_to_free_mb": round(total_size_to_free / (1024*1024), 2),
                "cutoff_date": cutoff_date.isoformat(),
                "dry_run": dry_run
            }
            
            if not dry_run and files_to_delete:
                deleted_files = []
                for backup_file in files_to_delete:
                    try:
                        backup_file.unlink()
                        deleted_files.append(str(backup_file))
                        logger.info(f"Deleted old backup: {backup_file}")
                    except Exception as e:
                        logger.error(f"Failed to delete {backup_file}: {e}")
                
                cleanup_result["deleted_files"] = deleted_files
                cleanup_result["actual_deleted"] = len(deleted_files)
            
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return {"error": str(e)}
    
    def restore_from_backup(self, backup_path: str, target_path: str = None) -> bool:
        """Restore database from backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            target = target_path or f"{self.database_path}.restored"
            
            # Copy backup to target location
            import shutil
            shutil.copy2(backup_file, target)
            
            # Verify restored database
            test_db = DatabaseManager(target)
            test_qi = DatabaseQueryInterface(target)
            profiles, _ = test_qi.filter_profiles(QueryFilter())
            
            logger.info(f"Database restored from {backup_path} to {target} with {len(profiles)} profiles")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def _run_scheduler(self):
        """Main scheduler loop running in background thread"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _perform_scheduled_backup(self) -> BackupResult:
        """Perform a scheduled backup"""
        logger.info("Performing scheduled backup")
        result = self._create_backup("scheduled")
        
        if result.success:
            logger.info(f"Scheduled backup completed: {result.backup_path}")
        else:
            logger.error(f"Scheduled backup failed: {result.error_message}")
        
        return result
    
    def _create_backup(self, backup_type: str = "manual") -> BackupResult:
        """Create a backup using the existing database backup system"""
        start_time = time.time()
        
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"catalynx_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Create backup using existing database manager
            success = self.db.backup_database(str(backup_path))
            
            if not success or not backup_path.exists():
                raise Exception("Database backup creation failed")
            
            # Get backup info
            file_size = backup_path.stat().st_size
            duration = time.time() - start_time
            
            # Count records
            profiles, _ = self.qi.filter_profiles(QueryFilter())
            opportunities, _ = self.qi.filter_opportunities(QueryFilter())
            records_count = len(profiles) + len(opportunities)
            
            # Record backup in database
            self.db.record_backup(backup_type, backup_filename, str(backup_path), 
                                file_size, records_count)
            
            # Create result
            result = BackupResult(
                success=True,
                backup_path=str(backup_path),
                file_size=file_size,
                records_backed_up=records_count,
                duration_seconds=duration
            )
            
            # Add to history
            self.backup_history.append(result)
            
            # Keep only last 100 backup results in memory
            if len(self.backup_history) > 100:
                self.backup_history = self.backup_history[-100:]
            
            logger.info(f"Backup created successfully: {backup_path} ({file_size} bytes, {records_count} records)")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            result = BackupResult(
                success=False,
                backup_path="",
                file_size=0,
                records_backed_up=0,
                duration_seconds=duration,
                error_message=error_msg
            )
            
            self.backup_history.append(result)
            logger.error(f"Backup failed: {error_msg}")
            return result
    
    def _cleanup_old_backups(self):
        """Scheduled cleanup of old backups"""
        logger.info("Performing scheduled backup cleanup")
        result = self.cleanup_old_backups(dry_run=False)
        
        if "error" not in result:
            deleted = result.get("actual_deleted", 0)
            freed_mb = result.get("space_to_free_mb", 0)
            logger.info(f"Cleanup completed: {deleted} files deleted, {freed_mb} MB freed")
        else:
            logger.error(f"Cleanup failed: {result['error']}")


# Factory function for easy access
def get_automated_backup_scheduler(config: BackupConfiguration = None, 
                                 database_path: str = "data/catalynx.db") -> AutomatedBackupScheduler:
    """Get a configured automated backup scheduler"""
    if config is None:
        config = BackupConfiguration()  # Use defaults
    
    return AutomatedBackupScheduler(config, database_path)


# Convenience function to start daily backups
def start_daily_backups(retention_days: int = 30) -> AutomatedBackupScheduler:
    """Start daily automated backups with specified retention"""
    config = BackupConfiguration(
        frequency=BackupFrequency.DAILY,
        retention_days=retention_days,
        include_exports=True,
        notification_enabled=True
    )
    
    scheduler = get_automated_backup_scheduler(config)
    scheduler.start_scheduler()
    return scheduler


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration
    config = BackupConfiguration(
        frequency=BackupFrequency.DAILY,
        retention_days=7,
        include_exports=True
    )
    
    # Initialize scheduler
    scheduler = get_automated_backup_scheduler(config)
    
    # Test manual backup
    print("Testing manual backup...")
    result = scheduler.create_manual_backup()
    print(f"Manual backup result: success={result.success}, size={result.file_size} bytes")
    
    # Test backup status
    print("\\nBackup status:")
    status = scheduler.get_backup_status()
    for key, value in status.items():
        if key != "recent_backups":
            print(f"  {key}: {value}")
    
    # Test cleanup (dry run)
    print("\\nTesting cleanup (dry run):")
    cleanup_result = scheduler.cleanup_old_backups(dry_run=True)
    print(f"Files to delete: {cleanup_result.get('files_to_delete', 0)}")
    print(f"Space to free: {cleanup_result.get('space_to_free_mb', 0)} MB")
    
    print("\\nAutomated backup scheduler testing completed!")