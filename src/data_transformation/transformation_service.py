#!/usr/bin/env python3
"""
Data Transformation Service for Catalynx Grant Research Platform
Transforms scraped JSON data into normalized database records

Features:
- Name parsing and normalization
- Cross-source deduplication
- Data validation and quality scoring
- Conflict resolution
- Source attribution tracking
"""

import logging
import hashlib
import uuid
import time
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict

from .models import (
    # Input models
    WebScrapingResults, DatabaseJSONFields, BoardMemberData, ScrapedLeadership,
    ScrapedProgram, ScrapedContact, ScrapedExtractedInfo,
    
    # Output models
    Person, ParsedName, OrganizationRole, Program, Contact, BoardConnection,
    
    # Result models
    TransformationResult, TransformationStats, ValidationError, DuplicationMatch,
    
    # Configuration
    TransformationConfig, NameParsingConfig, DeduplicationConfig, ValidationConfig,
    
    # Enums
    DataSource, ContactType, ProgramType, ValidationStatus
)

logger = logging.getLogger(__name__)


class NameParser:
    """Advanced name parsing and normalization utility"""
    
    # Common titles and suffixes for parsing
    TITLES = {
        'dr', 'doctor', 'prof', 'professor', 'mr', 'mrs', 'ms', 'miss',
        'rev', 'reverend', 'father', 'fr', 'sister', 'sr', 'brother', 'br',
        'judge', 'hon', 'honorable', 'senator', 'sen', 'congressman', 'congresswoman',
        'representative', 'rep', 'governor', 'gov', 'mayor', 'president', 'pres',
        'ceo', 'cfo', 'coo', 'cto', 'executive', 'director', 'chairman', 'chair'
    }
    
    SUFFIXES = {
        'jr', 'junior', 'sr', 'senior', 'ii', 'iii', 'iv', 'v', 'vi',
        'phd', 'md', 'jd', 'esq', 'esquire', 'dds', 'dvm', 'rn', 'cpa',
        'mba', 'ma', 'ms', 'bs', 'ba', 'mph', 'mph', 'mfa', 'msc'
    }
    
    # Common nickname mappings
    NICKNAME_MAP = {
        'bill': 'william', 'bob': 'robert', 'dick': 'richard', 'jim': 'james',
        'mike': 'michael', 'steve': 'stephen', 'dave': 'david', 'tom': 'thomas',
        'joe': 'joseph', 'pete': 'peter', 'dan': 'daniel', 'matt': 'matthew',
        'chris': 'christopher', 'andy': 'andrew', 'tony': 'anthony', 'rick': 'richard',
        'nick': 'nicholas', 'alex': 'alexander', 'kate': 'katherine', 'katie': 'katherine',
        'liz': 'elizabeth', 'beth': 'elizabeth', 'sue': 'susan', 'nan': 'nancy',
        'pat': 'patricia', 'peg': 'margaret', 'peggy': 'margaret', 'meg': 'margaret'
    }
    
    def __init__(self, config: NameParsingConfig):
        self.config = config
        
    def parse_name(self, full_name: str) -> ParsedName:
        """Parse a full name into components"""
        if not full_name or len(full_name.strip()) < self.config.min_name_length:
            raise ValueError(f"Name too short: {full_name}")
            
        original_name = full_name.strip()
        name_parts = self._clean_and_split_name(original_name)
        
        if not name_parts:
            raise ValueError(f"Could not parse name: {full_name}")
            
        # Extract components
        prefix, name_parts = self._extract_prefix(name_parts)
        name_parts, suffix = self._extract_suffix(name_parts)
        
        # Parse remaining parts into first, middle, last
        first_name, middle_name, last_name = self._parse_name_components(name_parts)
        
        # Generate normalized name
        normalized_name = self._normalize_name(first_name, middle_name, last_name, prefix, suffix)
        
        return ParsedName(
            full_name=original_name,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            prefix=prefix,
            suffix=suffix,
            normalized_name=normalized_name
        )
    
    def _clean_and_split_name(self, name: str) -> List[str]:
        """Clean name and split into parts"""
        # Remove extra punctuation and normalize spaces
        name = re.sub(r'[,;]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        
        # Split on spaces
        parts = [part.strip() for part in name.split() if part.strip()]
        
        # Remove empty parts and clean each part
        cleaned_parts = []
        for part in parts:
            # Remove periods from abbreviations but keep them in initials
            if len(part) == 2 and part.endswith('.'):
                cleaned_parts.append(part[0])  # Convert "J." to "J"
            elif part.lower() in self.TITLES or part.lower() in self.SUFFIXES:
                cleaned_parts.append(part.replace('.', ''))
            else:
                cleaned_parts.append(part.replace('.', ''))
                
        return cleaned_parts
    
    def _extract_prefix(self, name_parts: List[str]) -> Tuple[Optional[str], List[str]]:
        """Extract title/prefix from name parts"""
        if not name_parts:
            return None, name_parts
            
        first_part = name_parts[0].lower()
        if first_part in self.TITLES:
            return name_parts[0], name_parts[1:]
        
        # Check for compound titles like "Dr." "Mrs."
        if len(name_parts) >= 2:
            compound = f"{first_part} {name_parts[1].lower()}"
            if compound in self.TITLES:
                return f"{name_parts[0]} {name_parts[1]}", name_parts[2:]
                
        return None, name_parts
    
    def _extract_suffix(self, name_parts: List[str]) -> Tuple[List[str], Optional[str]]:
        """Extract suffix from name parts"""
        if not name_parts:
            return name_parts, None
            
        last_part = name_parts[-1].lower()
        if last_part in self.SUFFIXES:
            return name_parts[:-1], name_parts[-1]
            
        # Check for compound suffixes
        if len(name_parts) >= 2:
            compound = f"{name_parts[-2].lower()} {last_part}"
            if compound in self.SUFFIXES:
                return name_parts[:-2], f"{name_parts[-2]} {name_parts[-1]}"
                
        return name_parts, None
    
    def _parse_name_components(self, name_parts: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse remaining parts into first, middle, last names"""
        if not name_parts:
            return None, None, None
            
        if len(name_parts) == 1:
            # Single name - assume it's the first name
            return name_parts[0], None, None
        elif len(name_parts) == 2:
            # Two names - first and last
            return name_parts[0], None, name_parts[1]
        elif len(name_parts) == 3:
            # Three names - first, middle, last
            return name_parts[0], name_parts[1], name_parts[2]
        else:
            # More than three - first, middle (combine middle parts), last
            middle_parts = name_parts[1:-1]
            middle_name = ' '.join(middle_parts) if middle_parts else None
            return name_parts[0], middle_name, name_parts[-1]
    
    def _normalize_name(self, first: Optional[str], middle: Optional[str], 
                       last: Optional[str], prefix: Optional[str], 
                       suffix: Optional[str]) -> str:
        """Generate normalized name for matching"""
        parts = []
        
        # Add prefix if configured to keep it
        if prefix and not self.config.strip_titles:
            parts.append(prefix)
            
        # Add name components
        if first:
            # Handle nicknames if configured
            if self.config.handle_nicknames:
                normalized_first = self.NICKNAME_MAP.get(first.lower(), first)
            else:
                normalized_first = first
            parts.append(normalized_first)
            
        if middle:
            # For middle names, just use first initial if it's a full name
            if len(middle) > 2:
                parts.append(middle[0])
            else:
                parts.append(middle)
                
        if last:
            parts.append(last)
            
        # Add suffix if configured to keep it
        if suffix and not self.config.strip_suffixes:
            parts.append(suffix)
            
        return ' '.join(parts)
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two normalized names"""
        # Basic string similarity
        similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
        
        # Boost similarity for matching name components
        name1_parts = set(name1.lower().split())
        name2_parts = set(name2.lower().split())
        
        if name1_parts and name2_parts:
            common_parts = len(name1_parts.intersection(name2_parts))
            total_parts = len(name1_parts.union(name2_parts))
            component_similarity = common_parts / total_parts
            
            # Weighted average
            similarity = (similarity * 0.7) + (component_similarity * 0.3)
            
        return similarity


class DataDeduplicator:
    """Handles deduplication of people, programs, and contacts"""
    
    def __init__(self, config: DeduplicationConfig, name_parser: NameParser):
        self.config = config
        self.name_parser = name_parser
        
    def find_person_duplicates(self, people: List[Person]) -> List[DuplicationMatch]:
        """Find duplicate person records"""
        duplicates = []
        processed = set()
        
        for i, person1 in enumerate(people):
            if i in processed:
                continue
                
            for j, person2 in enumerate(people[i+1:], i+1):
                if j in processed:
                    continue
                    
                match = self._compare_people(person1, person2)
                if match:
                    duplicates.append(match)
                    processed.add(j)  # Mark the duplicate as processed
                    
        return duplicates
    
    def _compare_people(self, person1: Person, person2: Person) -> Optional[DuplicationMatch]:
        """Compare two people for duplication"""
        # Check exact match on required fields
        exact_match = True
        for field in self.config.exact_match_required_fields:
            if field == "normalized_name":
                if person1.parsed_name.normalized_name.lower() != person2.parsed_name.normalized_name.lower():
                    exact_match = False
                    break
                    
        if exact_match:
            return DuplicationMatch(
                match_type="exact",
                confidence=1.0,
                matched_record=person2.match_key,
                conflicting_fields=[]
            )
            
        # Check fuzzy match if enabled
        if self.config.fuzzy_match_threshold > 0:
            similarity = self.name_parser.calculate_name_similarity(
                person1.parsed_name.normalized_name,
                person2.parsed_name.normalized_name
            )
            
            if similarity >= self.config.fuzzy_match_threshold:
                # Check for conflicting fields
                conflicts = self._find_person_conflicts(person1, person2)
                
                return DuplicationMatch(
                    match_type="fuzzy",
                    confidence=similarity,
                    matched_record=person2.match_key,
                    conflicting_fields=conflicts
                )
                
        return None
    
    def _find_person_conflicts(self, person1: Person, person2: Person) -> List[str]:
        """Find conflicting fields between two people"""
        conflicts = []
        
        # Check title conflicts
        if (person1.primary_title and person2.primary_title and 
            person1.primary_title.lower() != person2.primary_title.lower()):
            conflicts.append("primary_title")
            
        # Check biography conflicts
        if (person1.biography and person2.biography and 
            person1.biography != person2.biography):
            conflicts.append("biography")
            
        return conflicts
    
    def merge_people(self, person1: Person, person2: Person) -> Person:
        """Merge two duplicate person records"""
        # Determine which record to use as base
        if self.config.merge_strategy == "highest_quality":
            base = person1 if person1.confidence_score >= person2.confidence_score else person2
            other = person2 if base == person1 else person1
        elif self.config.merge_strategy == "newest":
            # For now, use highest quality as proxy for newest
            base = person1 if person1.confidence_score >= person2.confidence_score else person2
            other = person2 if base == person1 else person1
        else:
            # Manual merge - return first person with combined data
            base = person1
            other = person2
            
        # Merge data
        merged_titles = list(set(base.all_titles + other.all_titles))
        merged_sources = list(set(base.data_sources + other.data_sources))
        merged_quality_flags = list(set(base.quality_flags + other.quality_flags))
        
        # Choose best biography
        best_biography = base.biography
        if not best_biography and other.biography:
            best_biography = other.biography
        elif base.biography and other.biography and len(other.biography) > len(base.biography):
            best_biography = other.biography
            
        # Average confidence scores
        avg_confidence = (base.confidence_score + other.confidence_score) / 2
        
        return Person(
            parsed_name=base.parsed_name,
            primary_title=base.primary_title or other.primary_title,
            all_titles=merged_titles,
            biography=best_biography,
            confidence_score=avg_confidence,
            data_sources=merged_sources,
            quality_flags=merged_quality_flags,
            match_key=base.match_key
        )


class DataTransformationService:
    """Main service for transforming scraped data into normalized records"""
    
    def __init__(self, config: Optional[TransformationConfig] = None):
        self.config = config or TransformationConfig()
        self.name_parser = NameParser(self.config.name_parsing)
        self.deduplicator = DataDeduplicator(self.config.deduplication, self.name_parser)
        
    def transform_profile_data(self, profile_id: str, ein: str, 
                             json_data: DatabaseJSONFields) -> TransformationResult:
        """Transform all data for a profile"""
        start_time = time.time()
        transformation_id = str(uuid.uuid4())
        
        logger.info(f"Starting data transformation for profile {profile_id}")
        
        try:
            # Initialize result
            result = TransformationResult(
                success=False,
                transformation_id=transformation_id,
                profile_id=profile_id
            )
            
            # Transform each data type
            people, person_errors = self._transform_people(ein, json_data)
            roles, role_errors = self._transform_roles(ein, people, json_data)
            programs, program_errors = self._transform_programs(ein, json_data)
            contacts, contact_errors = self._transform_contacts(ein, json_data)
            connections = self._discover_board_connections(ein, people, roles)
            
            # Deduplicate data
            if self.config.enable_fuzzy_matching:
                duplicate_matches = self.deduplicator.find_person_duplicates(people)
                if self.config.auto_merge_duplicates:
                    people = self._merge_duplicates(people, duplicate_matches)
            else:
                duplicate_matches = []
                
            # Compile all validation errors
            all_errors = person_errors + role_errors + program_errors + contact_errors
            
            # Calculate statistics
            processing_time = time.time() - start_time
            stats = TransformationStats(
                total_records_processed=len(people) + len(roles) + len(programs) + len(contacts),
                successful_transformations=len(people) + len(roles) + len(programs) + len(contacts) - len(all_errors),
                validation_errors=len(all_errors),
                duplicates_found=len(duplicate_matches),
                duplicates_merged=len(duplicate_matches) if self.config.auto_merge_duplicates else 0,
                processing_time_seconds=processing_time,
                people_processed=len(people),
                roles_created=len(roles),
                programs_processed=len(programs),
                contacts_processed=len(contacts),
                connections_discovered=len(connections)
            )
            
            # Calculate data quality score
            if stats.total_records_processed > 0:
                stats.data_quality_score = (
                    stats.successful_transformations / stats.total_records_processed
                ) * 100
            
            # Generate source data hash
            source_hash = self._generate_source_hash(json_data)
            
            # Update result
            result.success = len(all_errors) == 0 or len(all_errors) < stats.total_records_processed * 0.1  # Allow 10% error rate
            result.people = people
            result.roles = roles
            result.programs = programs
            result.contacts = contacts
            result.connections = connections
            result.validation_errors = all_errors
            result.duplicate_matches = duplicate_matches
            result.statistics = stats
            result.source_data_hash = source_hash
            
            logger.info(f"Transformation completed for profile {profile_id}: "
                       f"{stats.successful_transformations}/{stats.total_records_processed} successful, "
                       f"{stats.duplicates_found} duplicates found")
            
            return result
            
        except Exception as e:
            logger.error(f"Transformation failed for profile {profile_id}: {e}")
            processing_time = time.time() - start_time
            
            return TransformationResult(
                success=False,
                transformation_id=transformation_id,
                profile_id=profile_id,
                validation_errors=[ValidationError(
                    field="transformation",
                    error_type="system_error",
                    message=str(e),
                    severity="critical"
                )],
                statistics=TransformationStats(
                    processing_time_seconds=processing_time
                )
            )
    
    def _transform_people(self, ein: str, json_data: DatabaseJSONFields) -> Tuple[List[Person], List[ValidationError]]:
        """Transform board members and leadership into person records"""
        people = []
        errors = []
        
        # Process board members from JSON field
        if json_data.board_members:
            for board_member in json_data.board_members:
                try:
                    person = self._create_person_from_board_member(board_member)
                    people.append(person)
                except Exception as e:
                    errors.append(ValidationError(
                        field="board_members",
                        error_type="parsing_error",
                        message=f"Failed to parse board member {board_member.name}: {e}",
                        severity="error"
                    ))
        
        # Process web scraped leadership
        if json_data.web_enhanced_data and json_data.web_enhanced_data.extracted_info.leadership:
            for leadership in json_data.web_enhanced_data.extracted_info.leadership:
                try:
                    person = self._create_person_from_scraped_leadership(leadership)
                    people.append(person)
                except Exception as e:
                    errors.append(ValidationError(
                        field="web_leadership",
                        error_type="parsing_error",
                        message=f"Failed to parse leadership {leadership.name}: {e}",
                        severity="error"
                    ))
        
        return people, errors
    
    def _create_person_from_board_member(self, board_member: BoardMemberData) -> Person:
        """Create person record from board member data"""
        parsed_name = self.name_parser.parse_name(board_member.name)
        
        # Collect all titles
        titles = []
        if board_member.title:
            titles.append(board_member.title)
            
        return Person(
            parsed_name=parsed_name,
            primary_title=board_member.title,
            all_titles=titles,
            biography=board_member.background,
            confidence_score=0.9,  # High confidence for board member data
            data_sources=[DataSource.BOARD_MEMBERS],
            quality_flags=[],
            match_key=""  # Will be generated by validator
        )
    
    def _create_person_from_scraped_leadership(self, leadership: ScrapedLeadership) -> Person:
        """Create person record from scraped leadership data"""
        parsed_name = self.name_parser.parse_name(leadership.name)
        
        # Collect titles
        titles = []
        if leadership.title:
            titles.append(leadership.title)
            
        # Quality flags based on scraping quality
        quality_flags = []
        if leadership.quality_score < 50:
            quality_flags.append("low_quality_scraping")
            
        # Confidence based on quality score
        confidence = min(leadership.quality_score / 100.0, 1.0)
        
        return Person(
            parsed_name=parsed_name,
            primary_title=leadership.title,
            all_titles=titles,
            biography=leadership.biography,
            confidence_score=confidence,
            data_sources=[DataSource.WEB_SCRAPING],
            quality_flags=quality_flags,
            match_key=""  # Will be generated by validator
        )
    
    def _transform_roles(self, ein: str, people: List[Person], 
                        json_data: DatabaseJSONFields) -> Tuple[List[OrganizationRole], List[ValidationError]]:
        """Transform people into organization roles"""
        roles = []
        errors = []
        
        # Create person lookup by match key
        person_lookup = {person.match_key: person for person in people}
        
        # Process board member roles
        if json_data.board_members:
            for board_member in json_data.board_members:
                try:
                    # Find corresponding person
                    parsed_name = self.name_parser.parse_name(board_member.name)
                    match_key = self._generate_match_key(parsed_name.normalized_name)
                    
                    if match_key in person_lookup:
                        role = self._create_role_from_board_member(match_key, ein, board_member)
                        roles.append(role)
                    else:
                        errors.append(ValidationError(
                            field="board_member_role",
                            error_type="missing_person",
                            message=f"No person found for board member {board_member.name}",
                            severity="warning"
                        ))
                except Exception as e:
                    errors.append(ValidationError(
                        field="board_member_role",
                        error_type="creation_error",
                        message=f"Failed to create role for {board_member.name}: {e}",
                        severity="error"
                    ))
        
        # Process web scraped leadership roles
        if json_data.web_enhanced_data and json_data.web_enhanced_data.extracted_info.leadership:
            for leadership in json_data.web_enhanced_data.extracted_info.leadership:
                try:
                    parsed_name = self.name_parser.parse_name(leadership.name)
                    match_key = self._generate_match_key(parsed_name.normalized_name)
                    
                    if match_key in person_lookup:
                        role = self._create_role_from_scraped_leadership(match_key, ein, leadership)
                        roles.append(role)
                except Exception as e:
                    errors.append(ValidationError(
                        field="leadership_role",
                        error_type="creation_error",
                        message=f"Failed to create role for {leadership.name}: {e}",
                        severity="error"
                    ))
        
        return roles, errors
    
    def _create_role_from_board_member(self, person_match_key: str, ein: str, 
                                     board_member: BoardMemberData) -> OrganizationRole:
        """Create organization role from board member data"""
        return OrganizationRole(
            person_match_key=person_match_key,
            organization_ein=ein,
            position_title=board_member.title or "Board Member",
            is_current=True,
            is_board_member=True,
            is_executive=self._is_executive_position(board_member.title),
            compensation=board_member.compensation,
            data_source=DataSource.BOARD_MEMBERS,
            confidence_score=0.9,
            committees=board_member.committees or []
        )
    
    def _create_role_from_scraped_leadership(self, person_match_key: str, ein: str, 
                                           leadership: ScrapedLeadership) -> OrganizationRole:
        """Create organization role from scraped leadership data"""
        confidence = min(leadership.quality_score / 100.0, 1.0)
        
        return OrganizationRole(
            person_match_key=person_match_key,
            organization_ein=ein,
            position_title=leadership.title or "Leadership",
            is_current=True,
            is_board_member=self._is_board_position(leadership.title),
            is_executive=self._is_executive_position(leadership.title),
            data_source=DataSource.WEB_SCRAPING,
            confidence_score=confidence
        )
    
    def _transform_programs(self, ein: str, json_data: DatabaseJSONFields) -> Tuple[List[Program], List[ValidationError]]:
        """Transform scraped programs into program records"""
        programs = []
        errors = []
        
        if not (json_data.web_enhanced_data and json_data.web_enhanced_data.extracted_info.programs):
            return programs, errors
            
        for scraped_program in json_data.web_enhanced_data.extracted_info.programs:
            try:
                program = self._create_program_from_scraped(scraped_program)
                programs.append(program)
            except Exception as e:
                errors.append(ValidationError(
                    field="programs",
                    error_type="creation_error",
                    message=f"Failed to create program {scraped_program.name}: {e}",
                    severity="error"
                ))
        
        return programs, errors
    
    def _create_program_from_scraped(self, scraped_program: ScrapedProgram) -> Program:
        """Create program record from scraped program data"""
        # Determine program type from name/description
        program_type = self._classify_program_type(scraped_program.name, scraped_program.description)
        
        # Extract keywords from description
        keywords = self._extract_program_keywords(scraped_program.description)
        
        confidence = min(scraped_program.quality_score / 100.0, 1.0)
        
        return Program(
            name=scraped_program.name,
            description=scraped_program.description,
            program_type=program_type,
            keywords=keywords,
            data_source=DataSource.WEB_SCRAPING,
            confidence_score=confidence,
            match_key=""  # Will be generated by validator
        )
    
    def _transform_contacts(self, ein: str, json_data: DatabaseJSONFields) -> Tuple[List[Contact], List[ValidationError]]:
        """Transform scraped contacts into contact records"""
        contacts = []
        errors = []
        
        if not (json_data.web_enhanced_data and json_data.web_enhanced_data.extracted_info.contact_info):
            return contacts, errors
            
        for scraped_contact in json_data.web_enhanced_data.extracted_info.contact_info:
            try:
                contact = self._create_contact_from_scraped(scraped_contact)
                contacts.append(contact)
            except Exception as e:
                errors.append(ValidationError(
                    field="contacts",
                    error_type="creation_error",
                    message=f"Failed to create contact {scraped_contact.value}: {e}",
                    severity="error"
                ))
        
        return contacts, errors
    
    def _create_contact_from_scraped(self, scraped_contact: ScrapedContact) -> Contact:
        """Create contact record from scraped contact data"""
        confidence = min(scraped_contact.quality_score / 100.0, 1.0)
        
        return Contact(
            contact_type=scraped_contact.type,
            value=scraped_contact.value,
            label=scraped_contact.label,
            validation_status=ValidationStatus.PENDING,
            data_source=DataSource.WEB_SCRAPING,
            confidence_score=confidence
        )
    
    def _discover_board_connections(self, ein: str, people: List[Person], 
                                  roles: List[OrganizationRole]) -> List[BoardConnection]:
        """Discover board connections between organizations"""
        # For now, return empty list - this would require access to other organizations' data
        # In a full implementation, this would query the database for other organizations
        # that share board members with this organization
        return []
    
    def _merge_duplicates(self, people: List[Person], 
                         duplicate_matches: List[DuplicationMatch]) -> List[Person]:
        """Merge duplicate people records"""
        if not duplicate_matches:
            return people
            
        # Create person lookup
        person_lookup = {person.match_key: person for person in people}
        merged_keys = set()
        
        for match in duplicate_matches:
            if match.matched_record in merged_keys:
                continue
                
            # Find the original person (this is simplified - in practice you'd need better matching)
            original_person = None
            duplicate_person = person_lookup.get(match.matched_record)
            
            if original_person and duplicate_person:
                merged_person = self.deduplicator.merge_people(original_person, duplicate_person)
                person_lookup[original_person.match_key] = merged_person
                merged_keys.add(match.matched_record)
        
        # Return people with duplicates removed
        return [person for key, person in person_lookup.items() if key not in merged_keys]
    
    # Utility methods
    
    def _generate_match_key(self, normalized_name: str) -> str:
        """Generate match key for deduplication"""
        name = normalized_name.lower()
        key = re.sub(r'[^a-z0-9\s]', '', name)
        key = re.sub(r'\s+', ' ', key).strip()
        return key
    
    def _is_board_position(self, title: Optional[str]) -> bool:
        """Check if position title indicates board membership"""
        if not title:
            return False
            
        title_lower = title.lower()
        board_keywords = ['board', 'director', 'trustee', 'chairman', 'chair', 'vice chair']
        return any(keyword in title_lower for keyword in board_keywords)
    
    def _is_executive_position(self, title: Optional[str]) -> bool:
        """Check if position title indicates executive role"""
        if not title:
            return False
            
        title_lower = title.lower()
        exec_keywords = ['ceo', 'president', 'executive director', 'cfo', 'coo', 'cto', 'chairman']
        return any(keyword in title_lower for keyword in exec_keywords)
    
    def _classify_program_type(self, name: Optional[str], description: Optional[str]) -> Optional[ProgramType]:
        """Classify program type based on name and description"""
        text = f"{name or ''} {description or ''}".lower()
        
        if any(word in text for word in ['advocacy', 'policy', 'lobbying']):
            return ProgramType.ADVOCACY
        elif any(word in text for word in ['research', 'study', 'analysis']):
            return ProgramType.RESEARCH
        elif any(word in text for word in ['education', 'training', 'workshop']):
            return ProgramType.EDUCATION
        elif any(word in text for word in ['grant', 'funding', 'award']):
            return ProgramType.GRANTMAKING
        elif any(word in text for word in ['service', 'support', 'assistance']):
            return ProgramType.DIRECT_SERVICE
        else:
            return ProgramType.OTHER
    
    def _extract_program_keywords(self, description: Optional[str]) -> List[str]:
        """Extract keywords from program description"""
        if not description:
            return []
            
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\b\w{3,}\b', description.lower())
        
        # Filter out common words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'men', 'put', 'say', 'she', 'too', 'use'}
        keywords = [word for word in words if word not in stop_words]
        
        return list(set(keywords))[:10]  # Return up to 10 unique keywords
    
    def _generate_source_hash(self, json_data: DatabaseJSONFields) -> str:
        """Generate hash of source data for change detection"""
        data_str = json.dumps(json_data.dict(), sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()
