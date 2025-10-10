#!/usr/bin/env python3
"""
Data Transformation Service for Catalynx Normalized Analytics
Handles migration from JSON fields to normalized database structure
"""

import sqlite3
import json
import re
import hashlib
import logging
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TransformationResult:
    """Result of a data transformation operation"""
    success: bool
    records_processed: int
    records_created: int
    records_updated: int
    errors: List[str]
    warnings: List[str]
    execution_time: float


class NameNormalizer:
    """Advanced name normalization for board member deduplication"""

    @staticmethod
    def normalize_name(name: str) -> Tuple[str, Dict[str, str]]:
        """
        Normalize a person's name for better matching and return parsed components

        Returns:
            Tuple of (normalized_name, components_dict)
        """
        if not name or not name.strip():
            return "", {}

        # Initialize components
        components = {
            'prefix': '',
            'first_name': '',
            'middle_name': '',
            'last_name': '',
            'suffix': ''
        }

        original = name.strip()

        # Common prefixes and suffixes
        prefixes = r'\b(Dr|Mr|Mrs|Ms|Miss|Prof|Rev|Hon|Esq|Sir|Dame)\b\.?'
        suffixes = r'\b(Jr|Sr|II|III|IV|V|PhD|MD|DDS|JD|Esq)\b\.?'

        # Extract prefix
        prefix_match = re.search(prefixes, original, re.IGNORECASE)
        if prefix_match:
            components['prefix'] = prefix_match.group(1)
            original = re.sub(prefixes, '', original, flags=re.IGNORECASE)

        # Extract suffix
        suffix_match = re.search(suffixes + r'$', original, re.IGNORECASE)
        if suffix_match:
            components['suffix'] = suffix_match.group(1)
            original = re.sub(suffixes + r'$', '', original, flags=re.IGNORECASE)

        # Clean up punctuation and extra spaces
        original = re.sub(r'[^\w\s]', ' ', original)
        original = ' '.join(original.split())

        # Split remaining name parts
        name_parts = [part.strip().title() for part in original.split() if part.strip()]

        if len(name_parts) == 1:
            components['last_name'] = name_parts[0]
        elif len(name_parts) == 2:
            components['first_name'] = name_parts[0]
            components['last_name'] = name_parts[1]
        elif len(name_parts) >= 3:
            components['first_name'] = name_parts[0]
            components['middle_name'] = ' '.join(name_parts[1:-1])
            components['last_name'] = name_parts[-1]

        # Create normalized name
        normalized_parts = []
        if components['first_name']:
            normalized_parts.append(components['first_name'])
        if components['middle_name']:
            normalized_parts.append(components['middle_name'])
        if components['last_name']:
            normalized_parts.append(components['last_name'])

        normalized_name = ' '.join(normalized_parts)

        return normalized_name, components

    @staticmethod
    def generate_name_hash(normalized_name: str) -> str:
        """Generate a consistent hash for name deduplication"""
        # Use a combination of normalized name and random component for uniqueness
        base_string = normalized_name.lower().replace(' ', '')
        return hashlib.md5(base_string.encode()).hexdigest()[:16]


class DataTransformationService:
    """Service for transforming JSON data to normalized database structure"""

    def __init__(self, database_path: str):
        self.database_path = database_path
        self.name_normalizer = NameNormalizer()

    def transform_all_data(self) -> TransformationResult:
        """Transform all JSON data to normalized structure"""
        start_time = datetime.now()
        total_processed = 0
        total_created = 0
        total_updated = 0
        errors = []
        warnings = []

        try:
            with sqlite3.connect(self.database_path) as conn:
                # Transform board members and leadership
                board_result = self._transform_board_members(conn)
                total_processed += board_result.records_processed
                total_created += board_result.records_created
                total_updated += board_result.records_updated
                errors.extend(board_result.errors)
                warnings.extend(board_result.warnings)

                # Transform programs
                program_result = self._transform_programs(conn)
                total_processed += program_result.records_processed
                total_created += program_result.records_created
                errors.extend(program_result.errors)
                warnings.extend(program_result.warnings)

                # Transform contacts
                contact_result = self._transform_contacts(conn)
                total_processed += contact_result.records_processed
                total_created += contact_result.records_created
                errors.extend(contact_result.errors)
                warnings.extend(contact_result.warnings)

                # Calculate network connections
                network_result = self._calculate_network_connections(conn)
                total_created += network_result.records_created
                errors.extend(network_result.errors)
                warnings.extend(network_result.warnings)

        except Exception as e:
            errors.append(f"Database transformation failed: {str(e)}")
            logger.error(f"Data transformation error: {e}", exc_info=True)

        execution_time = (datetime.now() - start_time).total_seconds()

        return TransformationResult(
            success=len(errors) == 0,
            records_processed=total_processed,
            records_created=total_created,
            records_updated=total_updated,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time
        )

    def _transform_board_members(self, conn: sqlite3.Connection) -> TransformationResult:
        """Transform board member JSON data to normalized tables"""
        start_time = datetime.now()
        processed = 0
        created = 0
        updated = 0
        errors = []
        warnings = []

        try:
            # Get profiles with board member data
            cursor = conn.execute("""
                SELECT id, ein, name, board_members, web_enhanced_data
                FROM profiles
                WHERE (board_members IS NOT NULL AND board_members != '[]')
                   OR (web_enhanced_data IS NOT NULL AND web_enhanced_data != '{}')
            """)

            profiles = cursor.fetchall()
            logger.info(f"Processing {len(profiles)} profiles for board member data")

            for profile_id, ein, org_name, board_members_json, web_enhanced_json in profiles:
                processed += 1

                # Parse board members from JSON
                board_members = []

                # From board_members field
                if board_members_json:
                    try:
                        board_data = json.loads(board_members_json)
                        if isinstance(board_data, list):
                            for member in board_data:
                                if isinstance(member, str) and member.strip():
                                    board_members.append({
                                        'name': member.strip(),
                                        'title': 'Board Member',
                                        'source': '990_filing'
                                    })
                                elif isinstance(member, dict):
                                    board_members.append({
                                        'name': member.get('name', ''),
                                        'title': member.get('title', 'Board Member'),
                                        'source': member.get('source', '990_filing')
                                    })
                    except json.JSONDecodeError as e:
                        warnings.append(f"Failed to parse board_members JSON for {org_name}: {e}")

                # From web_enhanced_data
                if web_enhanced_json:
                    try:
                        web_data = json.loads(web_enhanced_json)
                        leadership = web_data.get('leadership', [])
                        for leader in leadership:
                            if isinstance(leader, dict):
                                board_members.append({
                                    'name': leader.get('name', ''),
                                    'title': leader.get('title', 'Leadership'),
                                    'source': 'web_scraping',
                                    'biography': leader.get('biography', ''),
                                    'quality_score': leader.get('quality_score', 70)
                                })
                    except json.JSONDecodeError as e:
                        warnings.append(f"Failed to parse web_enhanced_data JSON for {org_name}: {e}")

                # Process each board member
                for member_data in board_members:
                    if not member_data.get('name'):
                        continue

                    # Normalize name
                    normalized_name, name_components = self.name_normalizer.normalize_name(member_data['name'])
                    if not normalized_name:
                        continue

                    name_hash = self.name_normalizer.generate_name_hash(normalized_name)

                    # Insert or get person
                    person_id = self._insert_or_get_person(
                        conn, normalized_name, member_data['name'], name_hash,
                        name_components, member_data.get('biography', ''),
                        member_data.get('quality_score', 50)
                    )

                    if person_id:
                        # Insert organization role
                        role_created = self._insert_organization_role(
                            conn, person_id, ein, org_name, member_data['title'],
                            member_data['source'], member_data.get('quality_score', 50)
                        )
                        if role_created:
                            created += 1

        except Exception as e:
            errors.append(f"Board member transformation failed: {str(e)}")
            logger.error(f"Board member transformation error: {e}", exc_info=True)

        execution_time = (datetime.now() - start_time).total_seconds()

        return TransformationResult(
            success=len(errors) == 0,
            records_processed=processed,
            records_created=created,
            records_updated=updated,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time
        )

    def _transform_programs(self, conn: sqlite3.Connection) -> TransformationResult:
        """Transform program JSON data to normalized table"""
        start_time = datetime.now()
        processed = 0
        created = 0
        errors = []
        warnings = []

        try:
            # Get profiles with program data
            cursor = conn.execute("""
                SELECT id, ein, name, web_enhanced_data, focus_areas, program_areas
                FROM profiles
                WHERE (web_enhanced_data IS NOT NULL AND web_enhanced_data != '{}')
                   OR (focus_areas IS NOT NULL AND focus_areas != '[]')
                   OR (program_areas IS NOT NULL AND program_areas != '[]')
            """)

            profiles = cursor.fetchall()
            logger.info(f"Processing {len(profiles)} profiles for program data")

            for profile_id, ein, org_name, web_enhanced_json, focus_areas_json, program_areas_json in profiles:
                processed += 1

                programs = []

                # From web_enhanced_data programs
                if web_enhanced_json:
                    try:
                        web_data = json.loads(web_enhanced_json)
                        web_programs = web_data.get('programs', [])
                        for program in web_programs:
                            if isinstance(program, dict):
                                programs.append({
                                    'name': program.get('name', ''),
                                    'description': program.get('description', ''),
                                    'type': program.get('type', 'service'),
                                    'source': 'web_scraping',
                                    'quality_score': program.get('quality_score', 70)
                                })
                            elif isinstance(program, str) and program.strip():
                                programs.append({
                                    'name': program.strip(),
                                    'description': '',
                                    'type': 'service',
                                    'source': 'web_scraping',
                                    'quality_score': 60
                                })
                    except json.JSONDecodeError as e:
                        warnings.append(f"Failed to parse web_enhanced_data programs for {org_name}: {e}")

                # From focus_areas
                if focus_areas_json:
                    try:
                        focus_areas = json.loads(focus_areas_json)
                        for area in focus_areas:
                            programs.append({
                                'name': f"{area} Focus Area",
                                'description': f"Organizational focus on {area}",
                                'type': 'focus_area',
                                'source': 'profile_config',
                                'quality_score': 80
                            })
                    except json.JSONDecodeError as e:
                        warnings.append(f"Failed to parse focus_areas for {org_name}: {e}")

                # From program_areas
                if program_areas_json:
                    try:
                        program_areas = json.loads(program_areas_json)
                        for area in program_areas:
                            programs.append({
                                'name': f"{area} Program",
                                'description': f"Program area: {area}",
                                'type': 'program_area',
                                'source': 'profile_config',
                                'quality_score': 80
                            })
                    except json.JSONDecodeError as e:
                        warnings.append(f"Failed to parse program_areas for {org_name}: {e}")

                # Insert programs
                for program_data in programs:
                    if not program_data.get('name'):
                        continue

                    program_created = self._insert_organization_program(
                        conn, ein, org_name, program_data
                    )
                    if program_created:
                        created += 1

        except Exception as e:
            errors.append(f"Program transformation failed: {str(e)}")
            logger.error(f"Program transformation error: {e}", exc_info=True)

        execution_time = (datetime.now() - start_time).total_seconds()

        return TransformationResult(
            success=len(errors) == 0,
            records_processed=processed,
            records_created=created,
            records_updated=0,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time
        )

    def _transform_contacts(self, conn: sqlite3.Connection) -> TransformationResult:
        """Transform contact JSON data to normalized table"""
        start_time = datetime.now()
        processed = 0
        created = 0
        errors = []
        warnings = []

        try:
            # Get profiles with contact data
            cursor = conn.execute("""
                SELECT id, ein, name, web_enhanced_data, website_url, location
                FROM profiles
                WHERE (web_enhanced_data IS NOT NULL AND web_enhanced_data != '{}')
                   OR website_url IS NOT NULL
                   OR location IS NOT NULL
            """)

            profiles = cursor.fetchall()
            logger.info(f"Processing {len(profiles)} profiles for contact data")

            for profile_id, ein, org_name, web_enhanced_json, website_url, location in profiles:
                processed += 1

                contacts = []

                # From web_enhanced_data
                if web_enhanced_json:
                    try:
                        web_data = json.loads(web_enhanced_json)
                        contact_info = web_data.get('contact_info', [])
                        for contact in contact_info:
                            if isinstance(contact, dict):
                                contacts.append({
                                    'type': contact.get('type', 'unknown'),
                                    'value': contact.get('value', ''),
                                    'label': contact.get('label', ''),
                                    'source': 'web_scraping',
                                    'quality_score': contact.get('quality_score', 70)
                                })
                    except json.JSONDecodeError as e:
                        warnings.append(f"Failed to parse contact_info for {org_name}: {e}")

                # From profile fields
                if website_url:
                    contacts.append({
                        'type': 'website',
                        'value': website_url,
                        'label': 'main',
                        'source': 'profile_config',
                        'quality_score': 90
                    })

                if location:
                    contacts.append({
                        'type': 'address',
                        'value': location,
                        'label': 'main',
                        'source': 'profile_config',
                        'quality_score': 85
                    })

                # Insert contacts
                for contact_data in contacts:
                    if not contact_data.get('value'):
                        continue

                    contact_created = self._insert_organization_contact(
                        conn, ein, org_name, contact_data
                    )
                    if contact_created:
                        created += 1

        except Exception as e:
            errors.append(f"Contact transformation failed: {str(e)}")
            logger.error(f"Contact transformation error: {e}", exc_info=True)

        execution_time = (datetime.now() - start_time).total_seconds()

        return TransformationResult(
            success=len(errors) == 0,
            records_processed=processed,
            records_created=created,
            records_updated=0,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time
        )

    def _calculate_network_connections(self, conn: sqlite3.Connection) -> TransformationResult:
        """Calculate and store network connections between organizations"""
        start_time = datetime.now()
        created = 0
        errors = []
        warnings = []

        try:
            # Find shared board members between organizations
            cursor = conn.execute("""
                SELECT DISTINCT
                    r1.person_id,
                    r1.organization_ein as org1_ein,
                    r1.organization_name as org1_name,
                    r2.organization_ein as org2_ein,
                    r2.organization_name as org2_name
                FROM organization_roles r1
                JOIN organization_roles r2 ON r1.person_id = r2.person_id
                WHERE r1.organization_ein < r2.organization_ein
                  AND r1.is_current = TRUE
                  AND r2.is_current = TRUE
                  AND r1.position_type = 'board'
                  AND r2.position_type = 'board'
            """)

            connections = cursor.fetchall()
            logger.info(f"Found {len(connections)} potential board connections")

            # Group by organization pairs
            org_connections = defaultdict(list)
            for person_id, org1_ein, org1_name, org2_ein, org2_name in connections:
                key = (org1_ein, org1_name, org2_ein, org2_name)
                org_connections[key].append(person_id)

            # Insert board connections
            for (org1_ein, org1_name, org2_ein, org2_name), person_ids in org_connections.items():
                for person_id in person_ids:
                    conn.execute("""
                        INSERT OR REPLACE INTO board_connections
                        (person_id, org1_ein, org1_name, org2_ein, org2_name,
                         connection_strength, shared_positions, is_current_connection)
                        VALUES (?, ?, ?, ?, ?, 1.0, 1, TRUE)
                    """, (person_id, org1_ein, org1_name, org2_ein, org2_name))
                    created += 1

            conn.commit()

        except Exception as e:
            errors.append(f"Network calculation failed: {str(e)}")
            logger.error(f"Network calculation error: {e}", exc_info=True)

        execution_time = (datetime.now() - start_time).total_seconds()

        return TransformationResult(
            success=len(errors) == 0,
            records_processed=0,
            records_created=created,
            records_updated=0,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time
        )

    def _insert_or_get_person(self, conn: sqlite3.Connection, normalized_name: str,
                             original_name: str, name_hash: str, components: Dict[str, str],
                             biography: str, quality_score: int) -> Optional[int]:
        """Insert or get existing person record"""
        try:
            # Try to find existing person by normalized name
            cursor = conn.execute(
                "SELECT id FROM people WHERE normalized_name = ?",
                (normalized_name,)
            )
            result = cursor.fetchone()

            if result:
                return result[0]

            # Insert new person
            cursor = conn.execute("""
                INSERT INTO people
                (normalized_name, original_name, name_hash, first_name, last_name,
                 middle_name, prefix, suffix, biography, data_quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                normalized_name, original_name, name_hash,
                components.get('first_name', ''), components.get('last_name', ''),
                components.get('middle_name', ''), components.get('prefix', ''),
                components.get('suffix', ''), biography, quality_score
            ))

            return cursor.lastrowid

        except sqlite3.Error as e:
            logger.error(f"Failed to insert/get person {normalized_name}: {e}")
            return None

    def _insert_organization_role(self, conn: sqlite3.Connection, person_id: int,
                                 organization_ein: str, organization_name: str,
                                 title: str, data_source: str, quality_score: int) -> bool:
        """Insert organization role record"""
        try:
            # Determine position type
            position_type = 'board'
            if any(word in title.lower() for word in ['ceo', 'president', 'director', 'officer']):
                position_type = 'executive'
            elif 'staff' in title.lower():
                position_type = 'staff'
            elif 'advisor' in title.lower():
                position_type = 'advisory'

            conn.execute("""
                INSERT OR REPLACE INTO organization_roles
                (person_id, organization_ein, organization_name, title, position_type,
                 data_source, quality_score, is_current)
                VALUES (?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (person_id, organization_ein, organization_name, title,
                  position_type, data_source, quality_score))

            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to insert organization role: {e}")
            return False

    def _insert_organization_program(self, conn: sqlite3.Connection,
                                   organization_ein: str, organization_name: str,
                                   program_data: Dict[str, Any]) -> bool:
        """Insert organization program record"""
        try:
            conn.execute("""
                INSERT OR REPLACE INTO organization_programs
                (organization_ein, organization_name, program_name, program_description,
                 program_type, data_source, quality_score, program_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                organization_ein, organization_name,
                program_data['name'], program_data.get('description', ''),
                program_data.get('type', 'service'), program_data['source'],
                program_data.get('quality_score', 50)
            ))

            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to insert program: {e}")
            return False

    def _insert_organization_contact(self, conn: sqlite3.Connection,
                                   organization_ein: str, organization_name: str,
                                   contact_data: Dict[str, Any]) -> bool:
        """Insert organization contact record"""
        try:
            conn.execute("""
                INSERT OR REPLACE INTO organization_contacts
                (organization_ein, organization_name, contact_type, contact_value,
                 contact_label, data_source, quality_score, is_primary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                organization_ein, organization_name,
                contact_data['type'], contact_data['value'],
                contact_data.get('label', ''), contact_data['source'],
                contact_data.get('quality_score', 50),
                contact_data.get('label') == 'main'
            ))

            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to insert contact: {e}")
            return False


# Usage example
if __name__ == "__main__":
    transformer = DataTransformationService("data/catalynx.db")
    result = transformer.transform_all_data()

    print(f"Transformation {'succeeded' if result.success else 'failed'}")
    print(f"Processed: {result.records_processed}")
    print(f"Created: {result.records_created}")
    print(f"Time: {result.execution_time:.2f}s")

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")