#!/usr/bin/env python3
"""
Data Migration Service - Phase 4
Migrates existing JSON data from profiles to normalized database structure
"""

import sqlite3
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DataMigrationService:
    """Service to migrate existing JSON data to normalized structure"""

    def __init__(self, database_path: str = "data/catalynx.db"):
        self.database_path = database_path

    def migrate_all_profiles(self) -> Dict[str, Any]:
        """Migrate all profiles with existing JSON data"""
        migration_stats = {
            "profiles_processed": 0,
            "total_people_created": 0,
            "total_roles_created": 0,
            "total_programs_created": 0,
            "total_contacts_created": 0,
            "errors": [],
            "migration_time": 0
        }

        start_time = datetime.now()

        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get all profiles with JSON data to migrate
                cursor.execute("""
                    SELECT id, name, board_members, web_enhanced_data
                    FROM profiles
                    WHERE (board_members IS NOT NULL AND board_members != '')
                       OR (web_enhanced_data IS NOT NULL AND web_enhanced_data != '')
                """)

                profiles = cursor.fetchall()
                logger.info(f"Found {len(profiles)} profiles with data to migrate")

                for profile in profiles:
                    try:
                        result = self._migrate_profile(cursor, profile)
                        migration_stats["profiles_processed"] += 1
                        migration_stats["total_people_created"] += result["people_created"]
                        migration_stats["total_roles_created"] += result["roles_created"]
                        migration_stats["total_programs_created"] += result["programs_created"]
                        migration_stats["total_contacts_created"] += result["contacts_created"]

                        logger.info(f"Migrated {profile['name']}: {result['people_created']} people, {result['roles_created']} roles")

                    except Exception as e:
                        error_msg = f"Failed to migrate {profile['name']}: {e}"
                        logger.error(error_msg)
                        migration_stats["errors"].append(error_msg)

                conn.commit()

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            migration_stats["errors"].append(f"Database error: {e}")

        migration_stats["migration_time"] = (datetime.now() - start_time).total_seconds()
        return migration_stats

    def _migrate_profile(self, cursor: sqlite3.Cursor, profile: sqlite3.Row) -> Dict[str, int]:
        """Migrate a single profile's JSON data"""
        profile_id = profile['id']
        profile_name = profile['name']

        stats = {"people_created": 0, "roles_created": 0, "programs_created": 0, "contacts_created": 0}

        # Extract EIN for organization linking
        cursor.execute("SELECT ein FROM profiles WHERE id = ?", (profile_id,))
        ein_row = cursor.fetchone()
        organization_ein = ein_row['ein'] if ein_row and ein_row['ein'] else profile_id

        # Migrate board_members JSON
        if profile['board_members']:
            board_stats = self._migrate_board_members(cursor, profile_id, profile_name, organization_ein, profile['board_members'])
            stats["people_created"] += board_stats["people_created"]
            stats["roles_created"] += board_stats["roles_created"]

        # Migrate web_enhanced_data JSON
        if profile['web_enhanced_data']:
            web_stats = self._migrate_web_enhanced_data(cursor, profile_id, profile_name, organization_ein, profile['web_enhanced_data'])
            stats["people_created"] += web_stats["people_created"]
            stats["roles_created"] += web_stats["roles_created"]
            stats["programs_created"] += web_stats["programs_created"]
            stats["contacts_created"] += web_stats["contacts_created"]

        return stats

    def _migrate_board_members(self, cursor: sqlite3.Cursor, profile_id: str, profile_name: str,
                              organization_ein: str, board_members_json: str) -> Dict[str, int]:
        """Migrate board_members JSON data"""
        stats = {"people_created": 0, "roles_created": 0}

        try:
            board_data = json.loads(board_members_json)
            if not isinstance(board_data, list):
                return stats

            for member in board_data:
                if isinstance(member, dict):
                    person_name = member.get("name", "Unknown")
                    position = member.get("position", member.get("title", "Board Member"))
                elif isinstance(member, str):
                    person_name = member
                    position = "Board Member"
                else:
                    continue

                # Create or find person
                person_id = self._create_or_find_person(cursor, person_name, "board_members_json")
                if person_id:
                    stats["people_created"] += 1

                    # Create organization role
                    self._create_organization_role(cursor, person_id, organization_ein, profile_name,
                                                 position, True, "board_members_json")
                    stats["roles_created"] += 1

        except Exception as e:
            logger.warning(f"Failed to migrate board members for {profile_name}: {e}")

        return stats

    def _migrate_web_enhanced_data(self, cursor: sqlite3.Cursor, profile_id: str, profile_name: str,
                                  organization_ein: str, web_enhanced_json: str) -> Dict[str, int]:
        """Migrate web_enhanced_data JSON"""
        stats = {"people_created": 0, "roles_created": 0, "programs_created": 0, "contacts_created": 0}

        try:
            web_data = json.loads(web_enhanced_json)
            extracted_info = web_data.get("extracted_info", {})

            # Migrate leadership
            leadership = extracted_info.get("leadership", [])
            for person in leadership:
                person_name = person.get("name", "Unknown")
                title = person.get("title", "Leadership")
                source = person.get("source", "web_enhanced_data")

                person_id = self._create_or_find_person(cursor, person_name, source)
                if person_id:
                    stats["people_created"] += 1

                    # Determine if this is a board role
                    is_board = any(keyword in title.lower() for keyword in
                                  ["board", "chair", "director", "trustee", "president", "vice", "secretary", "treasurer"])

                    self._create_organization_role(cursor, person_id, organization_ein, profile_name,
                                                 title, is_board, source)
                    stats["roles_created"] += 1

            # Migrate programs
            programs = extracted_info.get("programs", [])
            for program in programs:
                self._create_organization_program(cursor, organization_ein, profile_name, program)
                stats["programs_created"] += 1

            # Migrate contact info
            contacts = extracted_info.get("contact_info", [])
            for contact in contacts:
                self._create_organization_contact(cursor, organization_ein, profile_name, contact)
                stats["contacts_created"] += 1

        except Exception as e:
            logger.warning(f"Failed to migrate web enhanced data for {profile_name}: {e}")

        return stats

    def _create_or_find_person(self, cursor: sqlite3.Cursor, name: str, source: str) -> Optional[int]:
        """Create or find a person record"""
        normalized_name = self._normalize_name(name)
        name_hash = hashlib.md5(normalized_name.encode()).hexdigest()

        # Check if person already exists
        cursor.execute("SELECT id FROM people WHERE name_hash = ?", (name_hash,))
        existing = cursor.fetchone()
        if existing:
            return existing[0]

        # Parse name into components
        first_name, last_name = self._parse_name(normalized_name)

        # Create new person - using only required fields and letting defaults handle the rest
        cursor.execute("""
            INSERT INTO people (
                normalized_name, original_name, name_hash, first_name, last_name,
                data_quality_score, confidence_level, source_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            normalized_name, name, name_hash, first_name, last_name,
            85, 0.8, 1
        ))

        return cursor.lastrowid

    def _create_organization_role(self, cursor: sqlite3.Cursor, person_id: int, organization_ein: str,
                                 organization_name: str, role_title: str, is_board_member: bool, source: str):
        """Create organization role record"""
        # Determine position type and category based on title
        position_type = "board" if is_board_member else "staff"
        position_category = self._categorize_position(role_title)

        cursor.execute("""
            INSERT INTO organization_roles (
                person_id, organization_ein, organization_name, title,
                position_type, position_category, is_current, data_source,
                quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            person_id, organization_ein, organization_name, role_title,
            position_type, position_category, True, source, 85
        ))

    def _create_organization_program(self, cursor: sqlite3.Cursor, organization_ein: str,
                                   organization_name: str, program_data: Dict[str, Any]):
        """Create organization program record"""
        cursor.execute("""
            INSERT INTO organization_programs (
                organization_ein, organization_name, program_name, program_description,
                program_type, data_source, quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            organization_ein, organization_name,
            program_data.get("name", "Unknown Program"),
            program_data.get("description", ""),
            program_data.get("type", "direct_service"),
            program_data.get("source", "web_enhanced_data"),
            program_data.get("quality_score", 80)
        ))

    def _create_organization_contact(self, cursor: sqlite3.Cursor, organization_ein: str,
                                   organization_name: str, contact_data: Dict[str, Any]):
        """Create organization contact record"""
        cursor.execute("""
            INSERT INTO organization_contacts (
                organization_ein, organization_name, contact_type, contact_value,
                contact_label, is_public, data_source, quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            organization_ein, organization_name,
            contact_data.get("type", "unknown"),
            contact_data.get("value", ""),
            contact_data.get("label", ""),
            True,  # Default to public
            contact_data.get("source", "web_enhanced_data"),
            contact_data.get("quality_score", 75)
        ))

    def _normalize_name(self, name: str) -> str:
        """Normalize name for consistent matching"""
        if not name:
            return ""

        # Convert to title case and clean
        normalized = name.strip().title()

        # Remove common titles and suffixes
        import re
        normalized = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Rev|Hon|Esq)\.?\b', '', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\b(Jr|Sr|II|III|IV)\.?\b', '', normalized, flags=re.IGNORECASE)

        # Clean up whitespace
        normalized = ' '.join(normalized.split())

        return normalized.strip()

    def _parse_name(self, normalized_name: str) -> tuple[str, str]:
        """Parse normalized name into first and last name"""
        if not normalized_name:
            return "", ""

        parts = normalized_name.split()
        if len(parts) == 1:
            return parts[0], ""
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            # For 3+ parts, first name is first part, last name is last part
            return parts[0], parts[-1]

    def _categorize_position(self, title: str) -> str:
        """Categorize position title for better organization"""
        if not title:
            return "other"

        title_lower = title.lower()

        # Executive positions
        if any(keyword in title_lower for keyword in ["president", "ceo", "executive director", "director"]):
            return "executive"

        # Board positions
        if any(keyword in title_lower for keyword in ["chair", "board", "trustee", "vice"]):
            return "board"

        # Officer positions
        if any(keyword in title_lower for keyword in ["secretary", "treasurer", "officer"]):
            return "officer"

        # Committee positions
        if any(keyword in title_lower for keyword in ["committee", "member"]):
            return "committee"

        return "other"

    def generate_migration_report(self) -> str:
        """Generate a comprehensive migration report"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()

                # Count migrated records
                cursor.execute("SELECT COUNT(*) FROM people")
                people_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM organization_roles")
                roles_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM organization_programs")
                programs_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM organization_contacts")
                contacts_count = cursor.fetchone()[0]

                # Get top organizations by network size
                cursor.execute("""
                    SELECT organization_name, COUNT(*) as role_count
                    FROM organization_roles
                    GROUP BY organization_name
                    ORDER BY role_count DESC
                    LIMIT 5
                """)
                top_orgs = cursor.fetchall()

                report = f"""
=== DATA MIGRATION REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

NORMALIZED DATABASE RECORDS:
- People: {people_count}
- Organization Roles: {roles_count}
- Programs: {programs_count}
- Contacts: {contacts_count}

TOP ORGANIZATIONS BY NETWORK SIZE:
"""
                for org_name, role_count in top_orgs:
                    report += f"- {org_name}: {role_count} roles\n"

                return report

        except Exception as e:
            return f"Failed to generate migration report: {e}"