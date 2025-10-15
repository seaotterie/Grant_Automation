"""
Database service for foundation grants
Handles reading/writing grant data to foundation_grants table
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class FoundationGrantsDatabaseService:
    """Database service for foundation grant operations."""

    def __init__(self, db_path: str = "data/catalynx.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def fetch_foundation_grants(
        self,
        foundation_ein: str,
        tax_years: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch grants for a specific foundation."""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if tax_years:
                placeholders = ','.join('?' * len(tax_years))
                query = f"""
                    SELECT * FROM foundation_grants
                    WHERE foundation_ein = ?
                    AND grant_year IN ({placeholders})
                    ORDER BY grant_year DESC, grant_amount DESC
                """
                cursor.execute(query, [foundation_ein] + tax_years)
            else:
                query = """
                    SELECT * FROM foundation_grants
                    WHERE foundation_ein = ?
                    ORDER BY grant_year DESC, grant_amount DESC
                """
                cursor.execute(query, [foundation_ein])

            rows = cursor.fetchall()
            grants = [dict(row) for row in rows]

            logger.debug(f"Fetched {len(grants)} grants for foundation {foundation_ein}")
            return grants

        except Exception as e:
            logger.error(f"Error fetching grants for {foundation_ein}: {e}")
            return []

        finally:
            conn.close()

    def fetch_multiple_foundations_grants(
        self,
        foundation_eins: List[str],
        tax_years: Optional[List[int]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch grants for multiple foundations efficiently."""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = {}

        try:
            # Build query
            ein_placeholders = ','.join('?' * len(foundation_eins))

            if tax_years:
                year_placeholders = ','.join('?' * len(tax_years))
                query = f"""
                    SELECT * FROM foundation_grants
                    WHERE foundation_ein IN ({ein_placeholders})
                    AND grant_year IN ({year_placeholders})
                    ORDER BY foundation_ein, grant_year DESC, grant_amount DESC
                """
                params = foundation_eins + tax_years
            else:
                query = f"""
                    SELECT * FROM foundation_grants
                    WHERE foundation_ein IN ({ein_placeholders})
                    ORDER BY foundation_ein, grant_year DESC, grant_amount DESC
                """
                params = foundation_eins

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Group by foundation
            for row in rows:
                grant = dict(row)
                foundation_ein = grant['foundation_ein']

                if foundation_ein not in results:
                    results[foundation_ein] = []

                results[foundation_ein].append(grant)

            logger.info(f"Fetched grants from {len(results)} foundations")
            return results

        except Exception as e:
            logger.error(f"Error fetching grants for multiple foundations: {e}")
            return {}

        finally:
            conn.close()

    def insert_grant(
        self,
        foundation_ein: str,
        foundation_name: str,
        grantee_ein: Optional[str],
        grantee_name: str,
        normalized_grantee_name: str,
        grant_amount: float,
        grant_year: int,
        grant_purpose: Optional[str] = None,
        grant_tier: Optional[str] = None,
        **kwargs
    ) -> Optional[int]:
        """Insert a single grant record."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO foundation_grants (
                    foundation_ein, foundation_name,
                    grantee_ein, grantee_name, normalized_grantee_name,
                    grant_amount, grant_year, grant_purpose, grant_tier,
                    grantee_city, grantee_state, grantee_country,
                    recipient_type, relationship_to_foundation,
                    source_form, source_object_id, data_quality_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                foundation_ein, foundation_name,
                grantee_ein, grantee_name, normalized_grantee_name,
                grant_amount, grant_year, grant_purpose, grant_tier,
                kwargs.get('grantee_city'),
                kwargs.get('grantee_state'),
                kwargs.get('grantee_country'),
                kwargs.get('recipient_type'),
                kwargs.get('relationship_to_foundation'),
                kwargs.get('source_form', '990-PF'),
                kwargs.get('source_object_id'),
                kwargs.get('data_quality_score')
            ))

            conn.commit()
            row_id = cursor.lastrowid

            if row_id > 0:
                logger.debug(f"Inserted grant: {foundation_ein} -> {grantee_name} (${grant_amount})")
            else:
                logger.debug(f"Grant already exists (skipped): {foundation_ein} -> {grantee_name}")

            return row_id

        except Exception as e:
            logger.error(f"Error inserting grant: {e}")
            conn.rollback()
            return None

        finally:
            conn.close()

    def bulk_insert_grants(self, grants: List[Dict[str, Any]]) -> int:
        """Bulk insert multiple grants efficiently."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        inserted_count = 0

        try:
            for grant in grants:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO foundation_grants (
                            foundation_ein, foundation_name,
                            grantee_ein, grantee_name, normalized_grantee_name,
                            grant_amount, grant_year, grant_purpose, grant_tier,
                            grantee_city, grantee_state, grantee_country,
                            recipient_type, relationship_to_foundation,
                            source_form, source_object_id, data_quality_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        grant.get('foundation_ein'),
                        grant.get('foundation_name'),
                        grant.get('grantee_ein'),
                        grant.get('grantee_name'),
                        grant.get('normalized_grantee_name'),
                        grant.get('grant_amount'),
                        grant.get('grant_year'),
                        grant.get('grant_purpose'),
                        grant.get('grant_tier'),
                        grant.get('grantee_city'),
                        grant.get('grantee_state'),
                        grant.get('grantee_country'),
                        grant.get('recipient_type'),
                        grant.get('relationship_to_foundation'),
                        grant.get('source_form', '990-PF'),
                        grant.get('source_object_id'),
                        grant.get('data_quality_score')
                    ))

                    if cursor.lastrowid > 0:
                        inserted_count += 1

                except Exception as e:
                    logger.warning(f"Failed to insert grant: {e}")
                    continue

            conn.commit()
            logger.info(f"Bulk inserted {inserted_count} grants")
            return inserted_count

        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            conn.rollback()
            return 0

        finally:
            conn.close()

    def get_grant_statistics(self) -> Dict[str, Any]:
        """Get overall grant database statistics."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Total grants
            cursor.execute("SELECT COUNT(*) FROM foundation_grants")
            total_grants = cursor.fetchone()[0]

            # Unique foundations
            cursor.execute("SELECT COUNT(DISTINCT foundation_ein) FROM foundation_grants")
            unique_foundations = cursor.fetchone()[0]

            # Unique grantees
            cursor.execute("SELECT COUNT(DISTINCT normalized_grantee_name) FROM foundation_grants")
            unique_grantees = cursor.fetchone()[0]

            # Total funding
            cursor.execute("SELECT SUM(grant_amount) FROM foundation_grants")
            total_funding = cursor.fetchone()[0] or 0

            # Year range
            cursor.execute("SELECT MIN(grant_year), MAX(grant_year) FROM foundation_grants")
            min_year, max_year = cursor.fetchone()

            # Grants with EIN
            cursor.execute("SELECT COUNT(*) FROM foundation_grants WHERE grantee_ein IS NOT NULL")
            grants_with_ein = cursor.fetchone()[0]

            stats = {
                'total_grants': total_grants,
                'unique_foundations': unique_foundations,
                'unique_grantees': unique_grantees,
                'total_funding': total_funding,
                'year_range': f"{min_year}-{max_year}" if min_year and max_year else "N/A",
                'grants_with_ein': grants_with_ein,
                'ein_coverage_percent': (grants_with_ein / total_grants * 100) if total_grants > 0 else 0
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting grant statistics: {e}")
            return {}

        finally:
            conn.close()

    def search_grantees(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for grantees by name."""

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = """
                SELECT DISTINCT
                    grantee_ein,
                    grantee_name,
                    COUNT(*) as grant_count,
                    COUNT(DISTINCT foundation_ein) as funder_count,
                    SUM(grant_amount) as total_funding,
                    MIN(grant_year) as first_year,
                    MAX(grant_year) as last_year
                FROM foundation_grants
                WHERE normalized_grantee_name LIKE ?
                GROUP BY grantee_ein, grantee_name
                ORDER BY funder_count DESC, total_funding DESC
                LIMIT ?
            """

            cursor.execute(query, [f"%{search_term.lower()}%", limit])
            rows = cursor.fetchall()

            results = [dict(row) for row in rows]
            return results

        except Exception as e:
            logger.error(f"Error searching grantees: {e}")
            return []

        finally:
            conn.close()
