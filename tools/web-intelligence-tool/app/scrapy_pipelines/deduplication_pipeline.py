"""
Deduplication Pipeline

Removes duplicate entries from scraped data based on content similarity.

Common deduplication scenarios:
- Same person listed multiple times with slight name variations
- Same program described on multiple pages
- Contact information repeated across pages

Uses content-based hashing and similarity matching to identify duplicates.
"""

import logging
import hashlib
from typing import List, Dict, Any, Set
from dataclasses import dataclass
import difflib

logger = logging.getLogger(__name__)


@dataclass
class DuplicationStats:
    """Statistics about deduplication process"""
    original_count: int = 0
    duplicate_count: int = 0
    final_count: int = 0
    deduplication_rate: float = 0.0


class DeduplicationPipeline:
    """
    Pipeline to remove duplicate entries from scraped items.

    Processes:
    - Leadership entries (dedupe by name + title)
    - Program areas (dedupe by name + description)
    - Contact information (dedupe by email/phone)
    """

    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.dedup_stats: Dict[str, DuplicationStats] = {}

    async def process_item(self, item, spider):
        """
        Process item and remove duplicates.

        Args:
            item: Scrapy item with potentially duplicate data
            spider: Scrapy spider instance

        Returns:
            item: With deduplicated data
        """
        try:
            # Deduplicate leadership
            if 'leadership' in item and item['leadership']:
                original_count = len(item['leadership'])
                item['leadership'] = self._deduplicate_leadership(item['leadership'])
                final_count = len(item['leadership'])

                logger.debug(
                    f"Leadership deduplication: {original_count} → {final_count} "
                    f"({original_count - final_count} duplicates removed)"
                )

            # Deduplicate programs
            if 'programs' in item and item['programs']:
                original_count = len(item['programs'])
                item['programs'] = self._deduplicate_programs(item['programs'])
                final_count = len(item['programs'])

                logger.debug(
                    f"Program deduplication: {original_count} → {final_count} "
                    f"({original_count - final_count} duplicates removed)"
                )

            # Deduplicate grants (for competitor/foundation research)
            if 'grants_received' in item and item['grants_received']:
                original_count = len(item['grants_received'])
                item['grants_received'] = self._deduplicate_grants(item['grants_received'])
                final_count = len(item['grants_received'])

                logger.debug(
                    f"Grant deduplication: {original_count} → {final_count} "
                    f"({original_count - final_count} duplicates removed)"
                )

            return item

        except Exception as e:
            logger.error(f"Error in deduplication pipeline: {e}", exc_info=True)
            return item

    def _deduplicate_leadership(self, leadership: List[Dict]) -> List[Dict]:
        """
        Deduplicate leadership entries based on name and title similarity.

        Args:
            leadership: List of leader dicts

        Returns:
            List of unique leaders
        """
        if not leadership:
            return []

        unique_leaders = []
        seen_signatures = set()

        for leader in leadership:
            # Create content-based signature
            name = leader.get('name', '').strip().lower()
            title = leader.get('title', '').strip().lower()

            if not name:  # Skip empty entries
                continue

            signature = self._create_signature(f"{name}_{title}")

            # Check if we've seen this before
            if signature in seen_signatures:
                logger.debug(f"Duplicate leader found: {leader.get('name')} ({leader.get('title')})")
                continue

            # Check for fuzzy duplicates (same person, slightly different name/title)
            is_fuzzy_duplicate = self._is_fuzzy_duplicate_leader(leader, unique_leaders)

            if not is_fuzzy_duplicate:
                unique_leaders.append(leader)
                seen_signatures.add(signature)

        return unique_leaders

    def _is_fuzzy_duplicate_leader(self, leader: Dict, existing_leaders: List[Dict]) -> bool:
        """
        Check if leader is a fuzzy duplicate of existing leaders.

        Uses similarity matching to catch variations like:
        - "John Smith" vs "John W. Smith"
        - "CEO" vs "Chief Executive Officer"

        Args:
            leader: Leader to check
            existing_leaders: List of already-added leaders

        Returns:
            bool: True if this is likely a duplicate
        """
        name = leader.get('name', '').strip().lower()
        title = leader.get('title', '').strip().lower()

        for existing in existing_leaders:
            existing_name = existing.get('name', '').strip().lower()
            existing_title = existing.get('title', '').strip().lower()

            # Calculate name similarity
            name_similarity = difflib.SequenceMatcher(None, name, existing_name).ratio()

            # Calculate title similarity
            title_similarity = difflib.SequenceMatcher(None, title, existing_title).ratio()

            # If both name and title are very similar, it's likely a duplicate
            if name_similarity >= 0.90 and title_similarity >= 0.75:
                logger.debug(
                    f"Fuzzy duplicate: '{name}' ({title}) vs '{existing_name}' ({existing_title})"
                )
                return True

        return False

    def _deduplicate_programs(self, programs: List[Dict]) -> List[Dict]:
        """
        Deduplicate program areas based on name and description.

        Args:
            programs: List of program dicts

        Returns:
            List of unique programs
        """
        if not programs:
            return []

        unique_programs = []
        seen_signatures = set()

        for program in programs:
            name = program.get('name', '').strip().lower()
            description = program.get('description', '').strip().lower()

            if not name:  # Skip empty entries
                continue

            # Create signature from name + description
            content = f"{name}_{description[:100]}"  # First 100 chars of description
            signature = self._create_signature(content)

            if signature in seen_signatures:
                logger.debug(f"Duplicate program found: {program.get('name')}")
                continue

            # Check for fuzzy duplicates
            is_fuzzy_duplicate = self._is_fuzzy_duplicate_program(program, unique_programs)

            if not is_fuzzy_duplicate:
                unique_programs.append(program)
                seen_signatures.add(signature)

        return unique_programs

    def _is_fuzzy_duplicate_program(self, program: Dict, existing_programs: List[Dict]) -> bool:
        """
        Check if program is a fuzzy duplicate of existing programs.

        Args:
            program: Program to check
            existing_programs: List of already-added programs

        Returns:
            bool: True if this is likely a duplicate
        """
        name = program.get('name', '').strip().lower()
        description = program.get('description', '').strip().lower()[:200]  # First 200 chars

        for existing in existing_programs:
            existing_name = existing.get('name', '').strip().lower()
            existing_desc = existing.get('description', '').strip().lower()[:200]

            # Calculate name similarity
            name_similarity = difflib.SequenceMatcher(None, name, existing_name).ratio()

            # Calculate description similarity
            desc_similarity = difflib.SequenceMatcher(None, description, existing_desc).ratio()

            # If both are very similar, it's likely a duplicate
            if name_similarity >= 0.85 and desc_similarity >= 0.70:
                return True

        return False

    def _deduplicate_grants(self, grants: List[Dict]) -> List[Dict]:
        """
        Deduplicate grant entries based on funder, amount, and year.

        Args:
            grants: List of grant dicts

        Returns:
            List of unique grants
        """
        if not grants:
            return []

        unique_grants = []
        seen_signatures = set()

        for grant in grants:
            funder = grant.get('funder_name', '').strip().lower()
            amount = grant.get('grant_amount', 0)
            year = grant.get('grant_year', 0)

            if not funder:  # Skip empty entries
                continue

            # Create signature from funder + amount + year
            signature = self._create_signature(f"{funder}_{amount}_{year}")

            if signature in seen_signatures:
                logger.debug(
                    f"Duplicate grant found: {funder} ${amount} ({year})"
                )
                continue

            unique_grants.append(grant)
            seen_signatures.add(signature)

        return unique_grants

    def _create_signature(self, content: str) -> str:
        """
        Create a content-based hash signature.

        Args:
            content: String content to hash

        Returns:
            str: SHA256 hash of content
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
