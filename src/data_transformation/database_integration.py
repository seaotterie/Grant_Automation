#!/usr/bin/env python3
"""
Database Integration Layer for Data Transformation Pipeline
Integrates transformed data with existing DatabaseManager and schema

Features:
- Seamless integration with existing DatabaseManager
- Normalized table creation and management
- Batch insert operations with rollback support
- Data migration and update detection
- Performance monitoring and optimization
"""

import logging
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from ..database.database_manager import DatabaseManager, Profile
from .models import (
    TransformationResult, Person, OrganizationRole, Program, Contact, BoardConnection,
    DataSource, ContactType, ProgramType, ValidationStatus
)

logger = logging.getLogger(__name__)


class NormalizedDatabaseManager:
    """Extended database manager for normalized transformation data"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
        self.database_path = database_manager.database_path
        self._ensure_normalized_schema()
        
    def _ensure_normalized_schema(self):
        """Ensure normalized tables exist for transformation data"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create normalized people table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS people (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_key TEXT UNIQUE NOT NULL,
                        full_name TEXT NOT NULL,
                        first_name TEXT,
                        middle_name TEXT,
                        last_name TEXT,
                        prefix TEXT,
                        suffix TEXT,
                        normalized_name TEXT NOT NULL,
                        primary_title TEXT,
                        all_titles TEXT, -- JSON array
                        biography TEXT,
                        confidence_score REAL DEFAULT 1.0,
                        data_sources TEXT, -- JSON array
                        quality_flags TEXT, -- JSON array
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create organization roles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS organization_roles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        person_match_key TEXT NOT NULL,
                        organization_ein TEXT NOT NULL,
                        position_title TEXT NOT NULL,
                        start_date DATE,
                        end_date DATE,
                        is_current BOOLEAN DEFAULT TRUE,
                        is_board_member BOOLEAN DEFAULT FALSE,
                        is_executive BOOLEAN DEFAULT FALSE,
                        compensation DECIMAL(12,2),
                        data_source TEXT NOT NULL,
                        confidence_score REAL DEFAULT 1.0,
                        committees TEXT, -- JSON array
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (person_match_key) REFERENCES people (match_key),
                        UNIQUE(person_match_key, organization_ein, position_title)
                    )
                """)
                
                # Create organization programs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS organization_programs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        organization_ein TEXT NOT NULL,
                        match_key TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        program_type TEXT,
                        keywords TEXT, -- JSON array
                        data_source TEXT NOT NULL,
                        confidence_score REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(organization_ein, match_key)
                    )
                """)
                
                # Create organization contacts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS organization_contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        organization_ein TEXT NOT NULL,
                        contact_type TEXT NOT NULL,
                        value TEXT NOT NULL,
                        label TEXT,
                        is_verified BOOLEAN DEFAULT FALSE,
                        validation_status TEXT DEFAULT 'pending',
                        last_verified TIMESTAMP,
                        data_source TEXT NOT NULL,
                        confidence_score REAL DEFAULT 1.0,
                        is_public BOOLEAN DEFAULT TRUE,
                        contact_preferences TEXT, -- JSON object
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(organization_ein, contact_type, value)
                    )
                """)
                
                # Create board connections table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS board_connections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_ein TEXT NOT NULL,
                        target_ein TEXT NOT NULL,
                        connection_person TEXT NOT NULL,
                        connection_strength REAL DEFAULT 1.0,
                        connection_type TEXT DEFAULT 'board_overlap',
                        connection_start DATE,
                        connection_end DATE,
                        is_current BOOLEAN DEFAULT TRUE,
                        data_source TEXT NOT NULL,
                        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (connection_person) REFERENCES people (match_key),
                        UNIQUE(source_ein, target_ein, connection_person)
                    )
                """)
                
                # Create transformation tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transformation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transformation_id TEXT UNIQUE NOT NULL,
                        profile_id TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        source_data_hash TEXT,
                        processing_version TEXT,
                        records_processed INTEGER DEFAULT 0,
                        records_created INTEGER DEFAULT 0,
                        records_updated INTEGER DEFAULT 0,
                        validation_errors INTEGER DEFAULT 0,
                        duplicates_found INTEGER DEFAULT 0,
                        processing_time_seconds REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes for performance (updated to match actual schema)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_name_hash ON people (name_hash)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_normalized_name ON people (normalized_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_roles_person ON organization_roles (person_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_roles_org ON organization_roles (organization_ein)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_programs_org ON organization_programs (organization_ein)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_org ON organization_contacts (organization_ein)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_type ON organization_contacts (contact_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_target ON board_connections (target_ein)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_person ON board_connections (connection_person)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_transformation_profile ON transformation_history (profile_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_transformation_hash ON transformation_history (source_data_hash)")
                
                conn.commit()
                logger.info("Normalized database schema ensured")
                
        except Exception as e:
            logger.error(f"Failed to ensure normalized schema: {e}")
            raise
            
    def save_transformation_result(self, result: TransformationResult, 
                                 profile_ein: str) -> bool:
        """Save complete transformation result to database"""
        start_time = time.time()
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Check if we've already processed this data
                    if self._is_data_already_processed(cursor, result):
                        logger.info(f"Data already processed for {result.profile_id}, skipping")
                        cursor.execute("ROLLBACK")
                        return True
                    
                    # Save transformation tracking record
                    self._save_transformation_record(cursor, result)
                    
                    # Save people
                    people_created, people_updated = self._save_people(cursor, result.people)
                    
                    # Save roles
                    roles_created, roles_updated = self._save_roles(cursor, result.roles, profile_ein)
                    
                    # Save programs
                    programs_created, programs_updated = self._save_programs(cursor, result.programs, profile_ein)
                    
                    # Save contacts
                    contacts_created, contacts_updated = self._save_contacts(cursor, result.contacts, profile_ein)
                    
                    # Save board connections
                    connections_created, connections_updated = self._save_connections(cursor, result.connections)
                    
                    # Update transformation record with final counts
                    total_created = people_created + roles_created + programs_created + contacts_created + connections_created
                    total_updated = people_updated + roles_updated + programs_updated + contacts_updated + connections_updated
                    
                    cursor.execute("""
                        UPDATE transformation_history 
                        SET records_created = ?, records_updated = ?, processing_time_seconds = ?
                        WHERE transformation_id = ?
                    """, (
                        total_created, total_updated, 
                        time.time() - start_time, result.transformation_id
                    ))
                    
                    # Commit transaction
                    cursor.execute("COMMIT")
                    
                    logger.info(f"Transformation saved for {result.profile_id}: "
                               f"{total_created} created, {total_updated} updated")
                    
                    return True
                    
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    logger.error(f"Failed to save transformation result: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Database transaction failed for transformation {result.transformation_id}: {e}")
            return False
    
    def _is_data_already_processed(self, cursor: sqlite3.Cursor, 
                                 result: TransformationResult) -> bool:
        """Check if this data has already been processed"""
        if not result.source_data_hash:
            return False
            
        cursor.execute("""
            SELECT COUNT(*) FROM transformation_history 
            WHERE profile_id = ? AND source_data_hash = ? AND success = TRUE
        """, (result.profile_id, result.source_data_hash))
        
        return cursor.fetchone()[0] > 0
    
    def _save_transformation_record(self, cursor: sqlite3.Cursor, 
                                  result: TransformationResult):
        """Save transformation tracking record"""
        cursor.execute("""
            INSERT INTO transformation_history (
                transformation_id, profile_id, success, source_data_hash, 
                processing_version, records_processed, validation_errors, 
                duplicates_found, processing_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.transformation_id, result.profile_id, result.success,
            result.source_data_hash, result.processing_version,
            result.statistics.total_records_processed,
            result.statistics.validation_errors,
            result.statistics.duplicates_found,
            result.statistics.processing_time_seconds
        ))
    
    def _save_people(self, cursor: sqlite3.Cursor, 
                   people: List[Person]) -> Tuple[int, int]:
        """Save people records with upsert logic"""
        created_count = 0
        updated_count = 0
        
        for person in people:
            # Check if person already exists
            cursor.execute(
                "SELECT id FROM people WHERE match_key = ?", 
                (person.match_key,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing person
                cursor.execute("""
                    UPDATE people SET
                        full_name = ?, first_name = ?, middle_name = ?, last_name = ?,
                        prefix = ?, suffix = ?, normalized_name = ?, primary_title = ?,
                        all_titles = ?, biography = ?, confidence_score = ?,
                        data_sources = ?, quality_flags = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE match_key = ?
                """, (
                    person.parsed_name.full_name, person.parsed_name.first_name,
                    person.parsed_name.middle_name, person.parsed_name.last_name,
                    person.parsed_name.prefix, person.parsed_name.suffix,
                    person.parsed_name.normalized_name, person.primary_title,
                    json.dumps(person.all_titles), person.biography,
                    person.confidence_score, json.dumps([ds.value for ds in person.data_sources]),
                    json.dumps(person.quality_flags), person.match_key
                ))
                updated_count += 1
            else:
                # Insert new person
                cursor.execute("""
                    INSERT INTO people (
                        match_key, full_name, first_name, middle_name, last_name,
                        prefix, suffix, normalized_name, primary_title, all_titles,
                        biography, confidence_score, data_sources, quality_flags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    person.match_key, person.parsed_name.full_name,
                    person.parsed_name.first_name, person.parsed_name.middle_name,
                    person.parsed_name.last_name, person.parsed_name.prefix,
                    person.parsed_name.suffix, person.parsed_name.normalized_name,
                    person.primary_title, json.dumps(person.all_titles),
                    person.biography, person.confidence_score,
                    json.dumps([ds.value for ds in person.data_sources]),
                    json.dumps(person.quality_flags)
                ))
                created_count += 1
                
        return created_count, updated_count
    
    def _save_roles(self, cursor: sqlite3.Cursor, roles: List[OrganizationRole], 
                  organization_ein: str) -> Tuple[int, int]:
        """Save organization roles with upsert logic"""
        created_count = 0
        updated_count = 0
        
        for role in roles:
            # Check if role already exists
            cursor.execute("""
                SELECT id FROM organization_roles 
                WHERE person_match_key = ? AND organization_ein = ? AND position_title = ?
            """, (role.person_match_key, role.organization_ein, role.position_title))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing role
                cursor.execute("""
                    UPDATE organization_roles SET
                        start_date = ?, end_date = ?, is_current = ?, 
                        is_board_member = ?, is_executive = ?, compensation = ?,
                        data_source = ?, confidence_score = ?, committees = ?,
                        notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE person_match_key = ? AND organization_ein = ? AND position_title = ?
                """, (
                    role.start_date, role.end_date, role.is_current,
                    role.is_board_member, role.is_executive, role.compensation,
                    role.data_source.value, role.confidence_score,
                    json.dumps(role.committees), role.notes,
                    role.person_match_key, role.organization_ein, role.position_title
                ))
                updated_count += 1
            else:
                # Insert new role
                cursor.execute("""
                    INSERT INTO organization_roles (
                        person_match_key, organization_ein, position_title, start_date,
                        end_date, is_current, is_board_member, is_executive, compensation,
                        data_source, confidence_score, committees, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    role.person_match_key, role.organization_ein, role.position_title,
                    role.start_date, role.end_date, role.is_current,
                    role.is_board_member, role.is_executive, role.compensation,
                    role.data_source.value, role.confidence_score,
                    json.dumps(role.committees), role.notes
                ))
                created_count += 1
                
        return created_count, updated_count
    
    def _save_programs(self, cursor: sqlite3.Cursor, programs: List[Program], 
                     organization_ein: str) -> Tuple[int, int]:
        """Save organization programs with upsert logic"""
        created_count = 0
        updated_count = 0
        
        for program in programs:
            # Check if program already exists
            cursor.execute("""
                SELECT id FROM organization_programs 
                WHERE organization_ein = ? AND match_key = ?
            """, (organization_ein, program.match_key))
            existing = cursor.fetchone()
            
            program_type_value = program.program_type.value if program.program_type else None
            
            if existing:
                # Update existing program
                cursor.execute("""
                    UPDATE organization_programs SET
                        name = ?, description = ?, program_type = ?, keywords = ?,
                        data_source = ?, confidence_score = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE organization_ein = ? AND match_key = ?
                """, (
                    program.name, program.description, program_type_value,
                    json.dumps(program.keywords), program.data_source.value,
                    program.confidence_score, organization_ein, program.match_key
                ))
                updated_count += 1
            else:
                # Insert new program
                cursor.execute("""
                    INSERT INTO organization_programs (
                        organization_ein, match_key, name, description, program_type,
                        keywords, data_source, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    organization_ein, program.match_key, program.name,
                    program.description, program_type_value,
                    json.dumps(program.keywords), program.data_source.value,
                    program.confidence_score
                ))
                created_count += 1
                
        return created_count, updated_count
    
    def _save_contacts(self, cursor: sqlite3.Cursor, contacts: List[Contact], 
                     organization_ein: str) -> Tuple[int, int]:
        """Save organization contacts with upsert logic"""
        created_count = 0
        updated_count = 0
        
        for contact in contacts:
            # Check if contact already exists
            cursor.execute("""
                SELECT id FROM organization_contacts 
                WHERE organization_ein = ? AND contact_type = ? AND value = ?
            """, (organization_ein, contact.contact_type.value, contact.value))
            existing = cursor.fetchone()
            
            contact_prefs = json.dumps(contact.contact_preferences) if contact.contact_preferences else None
            
            if existing:
                # Update existing contact
                cursor.execute("""
                    UPDATE organization_contacts SET
                        label = ?, is_verified = ?, validation_status = ?,
                        last_verified = ?, data_source = ?, confidence_score = ?,
                        is_public = ?, contact_preferences = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE organization_ein = ? AND contact_type = ? AND value = ?
                """, (
                    contact.label, contact.is_verified, contact.validation_status.value,
                    contact.last_verified, contact.data_source.value, contact.confidence_score,
                    contact.is_public, contact_prefs, organization_ein,
                    contact.contact_type.value, contact.value
                ))
                updated_count += 1
            else:
                # Insert new contact
                cursor.execute("""
                    INSERT INTO organization_contacts (
                        organization_ein, contact_type, value, label, is_verified,
                        validation_status, last_verified, data_source, confidence_score,
                        is_public, contact_preferences
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    organization_ein, contact.contact_type.value, contact.value,
                    contact.label, contact.is_verified, contact.validation_status.value,
                    contact.last_verified, contact.data_source.value, contact.confidence_score,
                    contact.is_public, contact_prefs
                ))
                created_count += 1
                
        return created_count, updated_count
    
    def _save_connections(self, cursor: sqlite3.Cursor, 
                        connections: List[BoardConnection]) -> Tuple[int, int]:
        """Save board connections with upsert logic"""
        created_count = 0
        updated_count = 0
        
        for connection in connections:
            # Check if connection already exists
            cursor.execute("""
                SELECT id FROM board_connections 
                WHERE source_ein = ? AND target_ein = ? AND connection_person = ?
            """, (connection.source_ein, connection.target_ein, connection.connection_person))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing connection
                cursor.execute("""
                    UPDATE board_connections SET
                        connection_strength = ?, connection_type = ?, connection_start = ?,
                        connection_end = ?, is_current = ?, data_source = ?
                    WHERE source_ein = ? AND target_ein = ? AND connection_person = ?
                """, (
                    connection.connection_strength, connection.connection_type,
                    connection.connection_start, connection.connection_end,
                    connection.is_current, connection.data_source.value,
                    connection.source_ein, connection.target_ein, connection.connection_person
                ))
                updated_count += 1
            else:
                # Insert new connection
                cursor.execute("""
                    INSERT INTO board_connections (
                        source_ein, target_ein, connection_person, connection_strength,
                        connection_type, connection_start, connection_end, is_current,
                        data_source, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    connection.source_ein, connection.target_ein, connection.connection_person,
                    connection.connection_strength, connection.connection_type,
                    connection.connection_start, connection.connection_end,
                    connection.is_current, connection.data_source.value, connection.discovered_at
                ))
                created_count += 1
                
        return created_count, updated_count
    
    def get_organization_people(self, ein: str) -> List[Dict[str, Any]]:
        """Get all people associated with an organization"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, r.position_title, r.is_board_member, r.is_executive,
                           r.is_current, r.compensation
                    FROM people p
                    JOIN organization_roles r ON p.match_key = r.person_match_key
                    WHERE r.organization_ein = ?
                    ORDER BY r.is_executive DESC, r.is_board_member DESC, p.normalized_name
                """, (ein,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # Parse JSON fields
                    row_dict['all_titles'] = json.loads(row_dict['all_titles']) if row_dict['all_titles'] else []
                    row_dict['data_sources'] = json.loads(row_dict['data_sources']) if row_dict['data_sources'] else []
                    row_dict['quality_flags'] = json.loads(row_dict['quality_flags']) if row_dict['quality_flags'] else []
                    results.append(row_dict)
                    
                return results
                
        except Exception as e:
            logger.error(f"Failed to get organization people for {ein}: {e}")
            return []
    
    def get_organization_programs(self, ein: str) -> List[Dict[str, Any]]:
        """Get all programs for an organization"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM organization_programs 
                    WHERE organization_ein = ?
                    ORDER BY confidence_score DESC, name
                """, (ein,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # Parse JSON fields
                    row_dict['keywords'] = json.loads(row_dict['keywords']) if row_dict['keywords'] else []
                    results.append(row_dict)
                    
                return results
                
        except Exception as e:
            logger.error(f"Failed to get organization programs for {ein}: {e}")
            return []
    
    def get_organization_contacts(self, ein: str) -> List[Dict[str, Any]]:
        """Get all contacts for an organization"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM organization_contacts 
                    WHERE organization_ein = ?
                    ORDER BY contact_type, confidence_score DESC
                """, (ein,))
                
                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # Parse JSON fields
                    if row_dict['contact_preferences']:
                        row_dict['contact_preferences'] = json.loads(row_dict['contact_preferences'])
                    results.append(row_dict)
                    
                return results
                
        except Exception as e:
            logger.error(f"Failed to get organization contacts for {ein}: {e}")
            return []
    
    def get_board_connections(self, ein: str) -> List[Dict[str, Any]]:
        """Get board connections for an organization"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT bc.*, p.full_name as person_name, p.normalized_name
                    FROM board_connections bc
                    JOIN people p ON bc.connection_person = p.match_key
                    WHERE bc.source_ein = ? OR bc.target_ein = ?
                    ORDER BY bc.connection_strength DESC, bc.discovered_at DESC
                """, (ein, ein))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get board connections for {ein}: {e}")
            return []
    
    def get_transformation_history(self, profile_id: str) -> List[Dict[str, Any]]:
        """Get transformation history for a profile"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM transformation_history 
                    WHERE profile_id = ?
                    ORDER BY created_at DESC
                """, (profile_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get transformation history for {profile_id}: {e}")
            return []
    
    def cleanup_old_transformations(self, days_old: int = 30) -> int:
        """Clean up old transformation records"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM transformation_history 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days_old))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old transformation records")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old transformations: {e}")
            return 0
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics across all normalized tables"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                metrics = {}
                
                # People metrics
                cursor.execute("SELECT COUNT(*), AVG(confidence_score) FROM people")
                people_count, avg_people_confidence = cursor.fetchone()
                metrics['people'] = {
                    'total_count': people_count,
                    'avg_confidence': round(avg_people_confidence or 0, 3)
                }
                
                # Roles metrics
                cursor.execute("""
                    SELECT COUNT(*), 
                           COUNT(CASE WHEN is_current THEN 1 END) as current_roles,
                           COUNT(CASE WHEN is_board_member THEN 1 END) as board_roles,
                           AVG(confidence_score)
                    FROM organization_roles
                """)
                roles_row = cursor.fetchone()
                metrics['roles'] = {
                    'total_count': roles_row[0],
                    'current_roles': roles_row[1],
                    'board_roles': roles_row[2],
                    'avg_confidence': round(roles_row[3] or 0, 3)
                }
                
                # Programs metrics
                cursor.execute("SELECT COUNT(*), AVG(confidence_score) FROM organization_programs")
                programs_count, avg_programs_confidence = cursor.fetchone()
                metrics['programs'] = {
                    'total_count': programs_count,
                    'avg_confidence': round(avg_programs_confidence or 0, 3)
                }
                
                # Contacts metrics
                cursor.execute("""
                    SELECT COUNT(*), 
                           COUNT(CASE WHEN is_verified THEN 1 END) as verified_contacts,
                           AVG(confidence_score)
                    FROM organization_contacts
                """)
                contacts_row = cursor.fetchone()
                metrics['contacts'] = {
                    'total_count': contacts_row[0],
                    'verified_count': contacts_row[1],
                    'avg_confidence': round(contacts_row[2] or 0, 3)
                }
                
                # Connections metrics
                cursor.execute("""
                    SELECT COUNT(*), 
                           COUNT(CASE WHEN is_current THEN 1 END) as current_connections,
                           AVG(connection_strength)
                    FROM board_connections
                """)
                connections_row = cursor.fetchone()
                metrics['connections'] = {
                    'total_count': connections_row[0],
                    'current_count': connections_row[1],
                    'avg_strength': round(connections_row[2] or 0, 3)
                }
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to get data quality metrics: {e}")
            return {}


class DataTransformationIntegrator:
    """Main integration service combining transformation and database operations"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager
        self.normalized_db = NormalizedDatabaseManager(database_manager)
        
    def process_profile_transformation(self, profile: Profile, 
                                     transformation_result: TransformationResult) -> bool:
        """Process and save transformation result for a profile"""
        try:
            # Save normalized data
            success = self.normalized_db.save_transformation_result(
                transformation_result, profile.ein or ""
            )
            
            if success:
                # Update profile with transformation metadata
                self._update_profile_metadata(profile, transformation_result)
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to process transformation for profile {profile.id}: {e}")
            return False
    
    def _update_profile_metadata(self, profile: Profile, 
                               result: TransformationResult):
        """Update profile with transformation metadata"""
        try:
            # Add transformation info to processing history
            if not profile.processing_history:
                profile.processing_history = []
                
            transformation_info = {
                'type': 'data_transformation',
                'timestamp': datetime.now().isoformat(),
                'transformation_id': result.transformation_id,
                'success': result.success,
                'records_processed': result.statistics.total_records_processed,
                'validation_errors': len(result.validation_errors),
                'duplicates_found': result.statistics.duplicates_found,
                'processing_time': result.statistics.processing_time_seconds
            }
            
            profile.processing_history.append(transformation_info)
            
            # Keep only last 10 transformation records
            if len(profile.processing_history) > 10:
                profile.processing_history = profile.processing_history[-10:]
                
            # Update profile in database
            self.db_manager.update_profile(profile)
            
        except Exception as e:
            logger.error(f"Failed to update profile metadata: {e}")
    
    def get_enhanced_profile_data(self, profile_id: str, ein: str) -> Dict[str, Any]:
        """Get enhanced profile data including normalized transformation data"""
        try:
            # Get base profile
            profile = self.db_manager.get_profile(profile_id)
            if not profile:
                return {}
                
            # Get normalized data
            people = self.normalized_db.get_organization_people(ein)
            programs = self.normalized_db.get_organization_programs(ein)
            contacts = self.normalized_db.get_organization_contacts(ein)
            connections = self.normalized_db.get_board_connections(ein)
            transformation_history = self.normalized_db.get_transformation_history(profile_id)
            
            return {
                'profile': profile.__dict__,
                'normalized_data': {
                    'people': people,
                    'programs': programs,
                    'contacts': contacts,
                    'board_connections': connections
                },
                'transformation_history': transformation_history,
                'data_quality_summary': self._calculate_profile_quality_summary(people, programs, contacts)
            }
            
        except Exception as e:
            logger.error(f"Failed to get enhanced profile data for {profile_id}: {e}")
            return {}
    
    def _calculate_profile_quality_summary(self, people: List[Dict], 
                                         programs: List[Dict], 
                                         contacts: List[Dict]) -> Dict[str, Any]:
        """Calculate data quality summary for a profile"""
        try:
            total_records = len(people) + len(programs) + len(contacts)
            
            if total_records == 0:
                return {'total_records': 0, 'avg_confidence': 0.0, 'quality_score': 0.0}
                
            # Calculate average confidence
            all_confidences = []
            all_confidences.extend([p.get('confidence_score', 0) for p in people])
            all_confidences.extend([p.get('confidence_score', 0) for p in programs])
            all_confidences.extend([c.get('confidence_score', 0) for c in contacts])
            
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
            
            # Calculate quality score based on data completeness and confidence
            verified_contacts = sum(1 for c in contacts if c.get('is_verified', False))
            board_members = sum(1 for p in people if p.get('is_board_member', False))
            
            quality_score = (
                (avg_confidence * 0.4) +  # 40% confidence
                (min(len(people) / 5, 1.0) * 0.2) +  # 20% people completeness (target 5)
                (min(len(programs) / 3, 1.0) * 0.2) +  # 20% programs completeness (target 3)
                (min(verified_contacts / max(len(contacts), 1), 1.0) * 0.2)  # 20% contact verification
            ) * 100
            
            return {
                'total_records': total_records,
                'people_count': len(people),
                'programs_count': len(programs),
                'contacts_count': len(contacts),
                'board_members_count': board_members,
                'verified_contacts_count': verified_contacts,
                'avg_confidence': round(avg_confidence, 3),
                'quality_score': round(quality_score, 1)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate quality summary: {e}")
            return {'total_records': 0, 'avg_confidence': 0.0, 'quality_score': 0.0}
