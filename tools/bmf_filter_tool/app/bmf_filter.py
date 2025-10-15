"""
BMF Filter Tool - Core Implementation
====================================

12-Factor Tool demonstrating Factor 4: "Tools are structured outputs that trigger deterministic code"

This tool:
1. Takes structured input (BMFFilterIntent)
2. Executes deterministic CSV filtering logic
3. Returns structured output (BMFFilterResult)
4. Processes local BMF CSV files (aligned with existing Catalynx patterns)

Key 12-Factor Principles:
- Factor 3: All configuration from environment
- Factor 6: Stateless processes (no memory between calls)
- Factor 4: Structured input/output contracts
"""

import os
import time
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import psutil
from pathlib import Path
import pandas as pd

# Import our generated types
from .generated import (
    BMFFilterIntent, BMFFilterCriteria, BMFFilterResult,
    BMFOrganization, BMFSearchSummary, BMFExecutionData,
    BMFQualityAssessment, BMFRecommendations,
    BMFQueryComplexity, BMFSortOption, BMFFoundationType,
    BMFDataQuality, BMFSearchPriority
)

# Set up logging
logger = logging.getLogger(__name__)

class BMFFilterTool:
    """
    12-Factor BMF Data Filtering Tool

    This tool implements Factor 4: "Tools are structured outputs that trigger deterministic code"

    Architecture:
    - Takes structured input (BMFFilterIntent) from LLM
    - Executes deterministic database filtering
    - Returns structured output (BMFFilterResult)
    - Completely stateless between calls
    - All configuration from environment
    """

    def __init__(self):
        """Initialize tool with environment-based configuration (Factor 3)"""

        # Factor 3: Config from environment
        self.database_path = os.getenv("BMF_DATABASE_PATH", "data/nonprofit_intelligence.db")
        self.cache_enabled = os.getenv("BMF_CACHE_ENABLED", "true").lower() == "true"
        self.max_results = int(os.getenv("BMF_MAX_RESULTS", "1000"))
        self.timeout_seconds = int(os.getenv("BMF_TIMEOUT_SECONDS", "30"))
        self.memory_limit_mb = int(os.getenv("BMF_MEMORY_LIMIT_MB", "512"))

        # Performance monitoring
        self.log_performance = os.getenv("BMF_LOG_PERFORMANCE", "true").lower() == "true"
        self.benchmark_existing = os.getenv("BENCHMARK_AGAINST_EXISTING", "false").lower() == "true"

        # Simple in-memory cache (Factor 6: Stateless - external cache in production)
        self._cache: Dict[str, BMFFilterResult] = {}

        # Validate database exists
        if not Path(self.database_path).exists():
            raise FileNotFoundError(f"BMF database not found at {self.database_path}")

        # Test database connection
        self._test_database_connection()

        logger.info(f"BMF Filter Tool initialized - Database: {self.database_path}")

    def _test_database_connection(self) -> None:
        """Test database connection and verify schema"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # Check that bmf_organizations table exists with new fields
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bmf_organizations'")
            if not cursor.fetchone():
                raise ValueError("bmf_organizations table not found")

            # Verify new enhanced fields exist
            cursor.execute("PRAGMA table_info(bmf_organizations)")
            columns = [col[1] for col in cursor.fetchall()]

            required_fields = ['status', 'filing_req_cd', 'deductibility', 'activity', 'ruling_date']
            missing_fields = [field for field in required_fields if field not in columns]
            if missing_fields:
                raise ValueError(f"Required enhanced fields missing: {missing_fields}")

            # Get record count for validation
            cursor.execute("SELECT COUNT(*) FROM bmf_organizations")
            count = cursor.fetchone()[0]
            logger.info(f"Database connection verified: {count:,} organizations available")

            conn.close()

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise

    def _load_filter_config(self) -> List[str]:
        """Load NTEE filter configuration (similar to existing script)"""
        default_ntee = ['E31', 'P81', 'W70']  # Fallback values

        try:
            if Path(self.filter_config_path).exists():
                with open(self.filter_config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    ntee_codes = config.get("ntee_codes", config.get("ntee_minor", default_ntee))
                    if ntee_codes:
                        logger.info(f"Loaded filter config with NTEE codes: {ntee_codes}")
                        return ntee_codes
        except Exception as e:
            logger.warning(f"Could not load filter config: {e}")

        logger.info(f"Using default NTEE codes: {default_ntee}")
        return default_ntee

    async def execute(self, intent: BMFFilterIntent) -> BMFFilterResult:
        """
        Execute BMF filtering based on structured intent

        This is the core of Factor 4 implementation:
        1. LLM produces structured BMFFilterIntent
        2. This deterministic code executes the filtering
        3. Returns structured BMFFilterResult

        Args:
            intent: Structured filtering intent from LLM

        Returns:
            BMFFilterResult: Structured results with organizations and metadata
        """
        start_time = time.time()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        logger.info(f"Executing BMF filter: {intent.what_youre_looking_for}")

        try:
            # Validate intent
            self._validate_intent(intent)

            # Check cache first (Factor 6: Stateless caching)
            cache_key = self._make_cache_key(intent.criteria)
            if self.cache_enabled and cache_key in self._cache:
                cached_result = self._cache[cache_key]
                # Update timing but keep cached data
                cached_result.execution_metadata.cache_hit = True
                cached_result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000
                logger.info(f"Cache hit for query: {intent.what_youre_looking_for}")
                return cached_result

            # Execute CSV processing
            csv_start = time.time()
            organizations, processing_stats = self._process_database_query(intent.criteria)
            csv_time = (time.time() - csv_start) * 1000

            # Process results
            processing_start = time.time()
            processed_orgs = self._process_organizations(organizations, intent.criteria)
            processing_time = (time.time() - processing_start) * 1000

            # Apply limits and sorting
            results_truncated = len(processed_orgs) > (intent.criteria.limit or 100)
            if intent.criteria.limit:
                processed_orgs = processed_orgs[:intent.criteria.limit]

            # Generate summary
            summary = self._generate_summary(processed_orgs, intent.criteria, processing_stats)

            # Create execution metadata
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            execution_data = BMFExecutionData(
                execution_time_ms=(time.time() - start_time) * 1000,
                database_query_time_ms=csv_time,  # CSV processing time
                processing_time_ms=processing_time,
                cache_hit=False,
                cache_key=cache_key,
                results_truncated=results_truncated,
                query_complexity=self._assess_query_complexity(intent.criteria),
                memory_used_mb=final_memory - initial_memory,
                database_rows_scanned=processing_stats.get("rows_processed", 0),
                compared_to_existing=self.benchmark_existing,
                performance_vs_existing=None  # Would be calculated in benchmarking
            )

            # Generate quality assessment
            quality_assessment = self._assess_data_quality(processed_orgs, intent.criteria)

            # Generate recommendations
            recommendations = self._generate_recommendations(processed_orgs, intent.criteria, summary)

            # Create result
            result = BMFFilterResult(
                organizations=processed_orgs,
                summary=summary,
                execution_metadata=execution_data,
                quality_assessment=quality_assessment,
                recommendations=recommendations
            )

            # Cache result (Factor 6: Stateless caching)
            if self.cache_enabled:
                self._cache[cache_key] = result

            # Performance logging (Factor 11: Logs as event streams)
            if self.log_performance:
                logger.info(
                    f"BMF Filter completed - "
                    f"Results: {len(processed_orgs)}, "
                    f"Time: {execution_data.execution_time_ms:.1f}ms, "
                    f"Memory: {execution_data.memory_used_mb:.1f}MB"
                )

            return result

        except Exception as e:
            logger.error(f"BMF Filter execution failed: {str(e)}")
            # Return error result with metadata
            error_result = self._create_error_result(intent, str(e), time.time() - start_time)
            return error_result

    def _validate_intent(self, intent: BMFFilterIntent) -> None:
        """Validate the incoming intent for basic requirements"""
        if not intent.criteria:
            raise ValueError("Search criteria are required")

        if intent.criteria.limit and intent.criteria.limit > self.max_results:
            raise ValueError(f"Limit cannot exceed {self.max_results}")

        # Validate state codes
        if intent.criteria.states:
            valid_states = {
                "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
            }
            invalid_states = set(intent.criteria.states) - valid_states
            if invalid_states:
                raise ValueError(f"Invalid state codes: {invalid_states}")

        # Validate financial ranges
        if (intent.criteria.revenue_min and intent.criteria.revenue_max and
            intent.criteria.revenue_min > intent.criteria.revenue_max):
            raise ValueError("revenue_min cannot be greater than revenue_max")

    def _make_cache_key(self, criteria: BMFFilterCriteria) -> str:
        """Create cache key from search criteria"""
        key_parts = [
            f"states:{','.join(sorted(criteria.states or []))}",
            f"cities:{','.join(sorted(criteria.cities or []))}",
            f"revenue:{criteria.revenue_min}-{criteria.revenue_max}",
            f"assets:{criteria.asset_min}-{criteria.asset_max}",
            f"ntee:{','.join(sorted(criteria.ntee_codes or []))}",
            f"name:{criteria.organization_name or ''}",
            f"limit:{criteria.limit}",
            f"sort:{criteria.sort_by}",
            f"foundation:{criteria.foundation_type}",
            f"active_only:{getattr(criteria, 'active_orgs_only', True)}",
            f"recent990:{getattr(criteria, 'has_recent_990', False)}",
            f"status:{','.join(sorted(getattr(criteria, 'status_codes', []) or []))}",
            f"filing_req:{','.join(sorted(getattr(criteria, 'filing_req_codes', []) or []))}",
            f"deductibility:{','.join(sorted(getattr(criteria, 'deductibility_codes', []) or []))}",
            f"activity:{','.join(sorted(getattr(criteria, 'activity_codes', []) or []))}",
            f"group:{','.join(sorted(getattr(criteria, 'group_codes', []) or []))}",
            f"ruling_after:{getattr(criteria, 'ruling_date_after', '') or ''}",
            f"ruling_before:{getattr(criteria, 'ruling_date_before', '') or ''}"
        ]
        return "|".join(key_parts)

    def _process_database_query(self, criteria: BMFFilterCriteria) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Process BMF database based on criteria using SQL queries with enhanced filtering

        Returns:
            Tuple of (results, processing_statistics)
        """
        import sqlite3

        try:
            # Connect to database
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row  # Access columns by name

            # Count total organizations for statistics
            total_count = conn.execute("SELECT COUNT(*) FROM bmf_organizations").fetchone()[0]
            logger.info(f"Total organizations in database: {total_count}")

            # Build dynamic SQL query based on criteria
            query_parts = []
            params = []

            # Base query with enhanced fields
            base_query = """
                SELECT
                    ein, name, ico, street, city, state, zip,
                    ntee_code, foundation_code, organization_code, subsection, classification,
                    status, filing_req_cd, pf_filing_req_cd, deductibility, activity,
                    group_code, ruling_date, affiliation, acct_pd,
                    asset_amt, income_amt, revenue_amt
                FROM bmf_organizations
                WHERE 1=1
            """

            # Enhanced status filtering with new status field
            if hasattr(criteria, 'status_codes') and criteria.status_codes:
                placeholders = ','.join(['?' for _ in criteria.status_codes])
                query_parts.append(f"AND status IN ({placeholders})")
                params.extend(criteria.status_codes)
            elif hasattr(criteria, 'active_orgs_only') and criteria.active_orgs_only:
                query_parts.append("AND status = ?")
                params.append('01')  # Active status
            else:
                # Default to active organizations only
                query_parts.append("AND status = ?")
                params.append('01')

            # 501(c)(3) filter (subsection 03)
            query_parts.append("AND subsection = ?")
            params.append('03')

            # Geographic filters
            if criteria.states:
                placeholders = ','.join(['?' for _ in criteria.states])
                query_parts.append(f"AND state IN ({placeholders})")
                params.extend(criteria.states)

            if criteria.cities:
                placeholders = ','.join(['?' for _ in criteria.cities])
                query_parts.append(f"AND UPPER(city) IN ({placeholders})")
                params.extend([city.upper() for city in criteria.cities])

            # NTEE code filters
            ntee_codes_to_use = criteria.ntee_codes or self.default_ntee_codes
            if ntee_codes_to_use:
                placeholders = ','.join(['?' for _ in ntee_codes_to_use])
                query_parts.append(f"AND ntee_code IN ({placeholders})")
                params.extend(ntee_codes_to_use)

            # Enhanced filing requirement filters
            if hasattr(criteria, 'filing_req_codes') and criteria.filing_req_codes:
                placeholders = ','.join(['?' for _ in criteria.filing_req_codes])
                query_parts.append(f"AND filing_req_cd IN ({placeholders})")
                params.extend(criteria.filing_req_codes)

            # Deductibility filters
            if hasattr(criteria, 'deductibility_codes') and criteria.deductibility_codes:
                placeholders = ','.join(['?' for _ in criteria.deductibility_codes])
                query_parts.append(f"AND deductibility IN ({placeholders})")
                params.extend(criteria.deductibility_codes)

            # Activity code filters
            if hasattr(criteria, 'activity_codes') and criteria.activity_codes:
                placeholders = ','.join(['?' for _ in criteria.activity_codes])
                query_parts.append(f"AND activity IN ({placeholders})")
                params.extend(criteria.activity_codes)

            # Group code filters
            if hasattr(criteria, 'group_codes') and criteria.group_codes:
                placeholders = ','.join(['?' for _ in criteria.group_codes])
                query_parts.append(f"AND group_code IN ({placeholders})")
                params.extend(criteria.group_codes)

            # Ruling date filters (YYYYMM format)
            if hasattr(criteria, 'ruling_date_after') and criteria.ruling_date_after:
                query_parts.append("AND ruling_date >= ?")
                params.append(criteria.ruling_date_after)

            if hasattr(criteria, 'ruling_date_before') and criteria.ruling_date_before:
                query_parts.append("AND ruling_date <= ?")
                params.append(criteria.ruling_date_before)

            # Organization name filter
            if criteria.organization_name:
                query_parts.append("AND UPPER(name) LIKE ?")
                params.append(f"%{criteria.organization_name.upper()}%")

            # Financial filters
            if criteria.revenue_min is not None:
                query_parts.append("AND (CAST(income_amt AS INTEGER) >= ? OR CAST(revenue_amt AS INTEGER) >= ?)")
                params.extend([criteria.revenue_min, criteria.revenue_min])

            if criteria.revenue_max is not None:
                query_parts.append("AND (CAST(income_amt AS INTEGER) <= ? OR CAST(revenue_amt AS INTEGER) <= ?)")
                params.extend([criteria.revenue_max, criteria.revenue_max])

            if criteria.asset_min is not None:
                query_parts.append("AND CAST(asset_amt AS INTEGER) >= ?")
                params.append(criteria.asset_min)

            if criteria.asset_max is not None:
                query_parts.append("AND CAST(asset_amt AS INTEGER) <= ?")
                params.append(criteria.asset_max)

            # Foundation type filter
            if criteria.foundation_type and criteria.foundation_type != 'any':
                if criteria.foundation_type == 'private_foundation':
                    query_parts.append("AND foundation_code IN ('10', '11', '12', '13', '15', '16', '17')")
                elif criteria.foundation_type == 'public_charity':
                    query_parts.append("AND (foundation_code IS NULL OR foundation_code = '' OR foundation_code NOT IN ('10', '11', '12', '13', '15', '16', '17'))")

            # Build complete query
            complete_query = base_query + " " + " ".join(query_parts)

            # Add sorting
            if criteria.sort_by:
                sort_clause = self._get_sql_sort_clause(criteria.sort_by)
                complete_query += f" ORDER BY {sort_clause}"

            # Add limit
            if criteria.limit:
                complete_query += " LIMIT ?"
                params.append(criteria.limit)

            logger.info(f"Executing SQL query with {len(params)} parameters")
            logger.debug(f"SQL: {complete_query}")

            # Execute query
            cursor = conn.execute(complete_query, params)
            rows = cursor.fetchall()

            # Convert to list of dictionaries with enhanced data
            organizations = []
            for row in rows:
                org_data = {
                    'ein': row['ein'] or '',
                    'name': row['name'] or '',
                    'ico': row['ico'] or '',
                    'street': row['street'] or '',
                    'city': row['city'] or '',
                    'state': row['state'] or '',
                    'zip_code': row['zip'] or '',
                    'ntee_code': row['ntee_code'] or '',
                    'foundation_code': row['foundation_code'] or '',
                    'organization_code': row['organization_code'] or '',
                    'subsection': row['subsection'] or '',
                    'classification': row['classification'] or '',
                    'status': row['status'] or '',
                    'filing_req_cd': row['filing_req_cd'] or '',
                    'pf_filing_req_cd': row['pf_filing_req_cd'] or '',
                    'deductibility': row['deductibility'] or '',
                    'activity': row['activity'] or '',
                    'group_code': row['group_code'] or '',
                    'ruling_date': row['ruling_date'] or '',
                    'affiliation': row['affiliation'] or '',
                    'acct_pd': row['acct_pd'] or '',
                    'bmf_revenue': self._safe_int_convert(row['income_amt']) or self._safe_int_convert(row['revenue_amt']),
                    'bmf_assets': self._safe_int_convert(row['asset_amt']),
                    'f990_revenue': None,  # Would come from form_990 table join
                    'f990_assets': None,   # Would come from form_990 table join
                    'f990_expenses': None,
                    'grants_paid': None,
                    'latest_year': None
                }
                organizations.append(org_data)

            conn.close()

            processing_stats = {
                'rows_processed': total_count,
                'rows_after_filters': len(organizations),
                'final_results': len(organizations),
                'filter_efficiency': len(organizations) / total_count if total_count > 0 else 0
            }

            logger.info(f"Database query complete: {len(organizations)} results from {total_count} total records")
            return organizations, processing_stats

        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            raise

    def _safe_int_convert(self, value) -> Optional[int]:
        """Safely convert string to int, return None if conversion fails"""
        if pd.isna(value) or value == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _safe_str_convert(self, value) -> str:
        """Safely convert value to string, return empty string for NaN/None"""
        if pd.isna(value) or value is None:
            return ''
        return str(value)

    def _get_sql_sort_clause(self, sort_by: BMFSortOption) -> str:
        """Convert sort option to SQL ORDER BY clause"""
        if sort_by == BMFSortOption.name_asc:
            return "name ASC"
        elif sort_by == BMFSortOption.revenue_desc:
            return "CAST(COALESCE(income_amt, revenue_amt, '0') AS INTEGER) DESC"
        elif sort_by == BMFSortOption.revenue_asc:
            return "CAST(COALESCE(income_amt, revenue_amt, '0') AS INTEGER) ASC"
        elif sort_by == BMFSortOption.assets_desc:
            return "CAST(COALESCE(asset_amt, '0') AS INTEGER) DESC"
        elif sort_by == BMFSortOption.assets_asc:
            return "CAST(COALESCE(asset_amt, '0') AS INTEGER) ASC"
        elif sort_by == BMFSortOption.recent_filing:
            return "ruling_date DESC"
        else:
            return "name ASC"  # Default sorting

    def _sort_organizations(self, orgs: List[Dict[str, Any]], sort_by: BMFSortOption) -> List[Dict[str, Any]]:
        """Sort organizations based on sort criteria (legacy method for non-SQL sorting)"""
        if sort_by == BMFSortOption.name_asc:
            return sorted(orgs, key=lambda x: x.get('name', ''))
        elif sort_by == BMFSortOption.revenue_desc:
            return sorted(orgs, key=lambda x: x.get('bmf_revenue') or 0, reverse=True)
        elif sort_by == BMFSortOption.revenue_asc:
            return sorted(orgs, key=lambda x: x.get('bmf_revenue') or 0)
        elif sort_by == BMFSortOption.assets_desc:
            return sorted(orgs, key=lambda x: x.get('bmf_assets') or 0, reverse=True)
        elif sort_by == BMFSortOption.assets_asc:
            return sorted(orgs, key=lambda x: x.get('bmf_assets') or 0)
        else:
            return orgs  # Default: no sorting

    def _process_organizations(self, raw_orgs: List[Dict[str, Any]], criteria: BMFFilterCriteria) -> List[BMFOrganization]:
        """Process raw database results into BMFOrganization objects"""
        processed = []

        for org_data in raw_orgs:
            # Determine best revenue/asset values
            revenue = org_data['f990_revenue'] or org_data['bmf_revenue']
            assets = org_data['f990_assets'] or org_data['bmf_assets']

            # Generate match reasons
            match_reasons = self._generate_match_reasons(org_data, criteria)

            # Calculate match score (simple scoring based on criteria matches)
            match_score = len(match_reasons) / self._count_active_criteria(criteria)

            # Data completeness score
            data_fields = [
                org_data['name'], org_data['city'], org_data['state'],
                org_data['ntee_code'], revenue, assets
            ]
            completeness = sum(1 for field in data_fields if field is not None) / len(data_fields)

            org = BMFOrganization(
                ein=org_data['ein'],
                name=org_data['name'],
                ico=org_data.get('ico'),
                street=org_data.get('street'),
                city=org_data['city'],
                state=org_data['state'],
                zip_code=org_data.get('zip_code'),
                ntee_code=org_data['ntee_code'],
                ntee_description=self._get_ntee_description(org_data['ntee_code']),
                foundation_code=org_data['foundation_code'],
                organization_code=org_data.get('organization_code'),
                subsection=org_data.get('subsection'),
                classification=org_data.get('classification'),
                status=org_data.get('status'),
                filing_req_cd=org_data.get('filing_req_cd'),
                pf_filing_req_cd=org_data.get('pf_filing_req_cd'),
                deductibility=org_data.get('deductibility'),
                activity=org_data.get('activity'),
                group_code=org_data.get('group_code'),
                ruling_date=org_data.get('ruling_date'),
                affiliation=org_data.get('affiliation'),
                acct_pd=org_data.get('acct_pd'),
                asset_amt=org_data['bmf_assets'],
                income_amt=org_data['bmf_revenue'],
                revenue_amt=org_data['bmf_revenue'],
                revenue=revenue,
                assets=assets,
                expenses=org_data['f990_expenses'],
                grants_paid=org_data['grants_paid'],
                latest_990_year=org_data['latest_year'],
                data_completeness=completeness,
                match_reasons=match_reasons,
                match_score=match_score,
                catalynx_analyzed=False,  # Would check against existing data
                existing_opportunities=0   # Would check against existing data
            )

            processed.append(org)

        return processed

    def _generate_match_reasons(self, org_data: Dict[str, Any], criteria: BMFFilterCriteria) -> List[str]:
        """Generate human-readable reasons why this organization matched"""
        reasons = []

        if criteria.states and org_data['state'] in criteria.states:
            reasons.append(f"Located in {org_data['state']}")

        if criteria.ntee_codes and org_data['ntee_code'] in criteria.ntee_codes:
            ntee_desc = self._get_ntee_description(org_data['ntee_code'])
            reasons.append(f"Focus area: {ntee_desc}")

        revenue = org_data['f990_revenue'] or org_data['bmf_revenue']
        if revenue:
            if criteria.revenue_min and revenue >= criteria.revenue_min:
                reasons.append(f"Revenue ${revenue:,} meets minimum requirement")
            if criteria.revenue_max and revenue <= criteria.revenue_max:
                reasons.append(f"Revenue ${revenue:,} within maximum limit")

        assets = org_data['f990_assets'] or org_data['bmf_assets']
        if assets:
            if criteria.asset_min and assets >= criteria.asset_min:
                reasons.append(f"Assets ${assets:,} meets minimum requirement")

        if criteria.organization_name and criteria.organization_name.lower() in org_data['name'].lower():
            reasons.append(f"Name contains '{criteria.organization_name}'")

        if criteria.has_recent_990 and org_data['latest_year'] and org_data['latest_year'] >= 2020:
            reasons.append(f"Recent 990 filing ({org_data['latest_year']})")

        # Enhanced criteria matches
        if criteria.status_codes and org_data.get('status') in criteria.status_codes:
            status_desc = {"01": "Active", "02": "Inactive", "12": "Merged", "25": "Terminated"}.get(org_data['status'], org_data['status'])
            reasons.append(f"Organization status: {status_desc}")

        if criteria.filing_req_codes and org_data.get('filing_req_cd') in criteria.filing_req_codes:
            filing_desc = {"01": "990 Required", "02": "990-EZ Eligible", "06": "990-N Required"}.get(org_data['filing_req_cd'], org_data['filing_req_cd'])
            reasons.append(f"Filing requirement: {filing_desc}")

        if criteria.deductibility_codes and org_data.get('deductibility') in criteria.deductibility_codes:
            deduct_desc = {"1": "Tax-deductible donations accepted", "2": "Non-deductible", "0": "Unknown deductibility"}.get(org_data['deductibility'], org_data['deductibility'])
            reasons.append(f"Deductibility: {deduct_desc}")

        if criteria.ruling_date_after and org_data.get('ruling_date') and org_data['ruling_date'] >= criteria.ruling_date_after:
            reasons.append(f"Established after {criteria.ruling_date_after}")

        if criteria.ruling_date_before and org_data.get('ruling_date') and org_data['ruling_date'] <= criteria.ruling_date_before:
            reasons.append(f"Established before {criteria.ruling_date_before}")

        return reasons

    def _count_active_criteria(self, criteria: BMFFilterCriteria) -> int:
        """Count how many filter criteria are actually being used"""
        count = 0
        if criteria.states: count += 1
        if criteria.cities: count += 1
        if criteria.revenue_min is not None: count += 1
        if criteria.revenue_max is not None: count += 1
        if criteria.asset_min is not None: count += 1
        if criteria.asset_max is not None: count += 1
        if criteria.ntee_codes: count += 1
        if criteria.organization_name: count += 1
        if criteria.foundation_type and criteria.foundation_type != "any": count += 1
        if getattr(criteria, 'has_recent_990', False): count += 1
        # Enhanced criteria
        if getattr(criteria, 'status_codes', []): count += 1
        if getattr(criteria, 'filing_req_codes', []): count += 1
        if getattr(criteria, 'deductibility_codes', []): count += 1
        if getattr(criteria, 'activity_codes', []): count += 1
        if getattr(criteria, 'group_codes', []): count += 1
        if getattr(criteria, 'ruling_date_after', ''): count += 1
        if getattr(criteria, 'ruling_date_before', ''): count += 1
        return max(count, 1)  # Avoid division by zero

    def _get_ntee_description(self, ntee_code: str) -> str:
        """Get human-readable description for NTEE code"""
        ntee_map = {
            'P20': 'Elementary and Secondary Education',
            'P30': 'Higher Education',
            'B25': 'Health Care',
            'P99': 'Human Services',
            'A20': 'Arts and Culture',
            'C20': 'Environment',
            'X20': 'Religion',
            'S20': 'Community Development',
            'O20': 'Youth Development',
            # Add more as needed
        }
        return ntee_map.get(ntee_code, ntee_code)

    def _assess_query_complexity(self, criteria: BMFFilterCriteria) -> BMFQueryComplexity:
        """Assess the complexity of the query for performance tracking"""
        active_criteria = self._count_active_criteria(criteria)

        if active_criteria <= 2:
            return BMFQueryComplexity.simple
        elif active_criteria <= 4:
            return BMFQueryComplexity.moderate
        elif active_criteria <= 6:
            return BMFQueryComplexity.complex
        else:
            return BMFQueryComplexity.very_complex

    def _generate_summary(self, orgs: List[BMFOrganization], criteria: BMFFilterCriteria, processing_stats: Dict[str, Any]) -> BMFSearchSummary:
        """Generate search summary and insights"""

        # Geographic distribution
        state_counts = {}
        for org in orgs:
            state_counts[org.state] = state_counts.get(org.state, 0) + 1
        geo_dist = f"Found across {len(state_counts)} states: " + ", ".join(f"{state}({count})" for state, count in sorted(state_counts.items())[:5])

        # Financial summary
        revenues = [org.revenue for org in orgs if org.revenue]
        if revenues:
            avg_revenue = sum(revenues) / len(revenues)
            financial_summary = f"Revenue range: ${min(revenues):,} - ${max(revenues):,}, Average: ${avg_revenue:,.0f}"
        else:
            financial_summary = "Financial data limited"

        # Criteria summary
        criteria_parts = []
        if criteria.states:
            criteria_parts.append(f"in {', '.join(criteria.states)}")
        if criteria.ntee_codes:
            criteria_parts.append(f"focus areas: {', '.join(criteria.ntee_codes)}")
        if criteria.revenue_min or criteria.revenue_max:
            if criteria.revenue_min and criteria.revenue_max:
                criteria_parts.append(f"revenue ${criteria.revenue_min:,} - ${criteria.revenue_max:,}")
            elif criteria.revenue_min:
                criteria_parts.append(f"revenue over ${criteria.revenue_min:,}")
            else:
                criteria_parts.append(f"revenue under ${criteria.revenue_max:,}")

        criteria_summary = f"Organizations {' '.join(criteria_parts)}" if criteria_parts else "All organizations"

        # Top matches description
        if not orgs:
            top_description = "No matching organizations found"
        elif len(orgs) == 1:
            top_description = f"Found: {orgs[0].name} in {orgs[0].state}"
        else:
            top_3 = orgs[:3]
            names = [org.name for org in top_3]
            if len(orgs) <= 3:
                top_description = f"Found: {', '.join(names)}"
            else:
                top_description = f"Top matches: {', '.join(names)} and {len(orgs)-3} others"

        return BMFSearchSummary(
            total_found=len(orgs),
            total_in_database=processing_stats.get('rows_processed', 0),
            criteria_summary=criteria_summary,
            top_matches_description=top_description,
            geographic_distribution=geo_dist,
            financial_summary=financial_summary,
            recommendations=[]  # Will be filled by _generate_recommendations
        )

    def _assess_data_quality(self, orgs: List[BMFOrganization], criteria: BMFFilterCriteria) -> BMFQualityAssessment:
        """Assess the quality of the returned data"""
        if not orgs:
            return BMFQualityAssessment(
                overall_quality=0.0,
                completeness_rate=0.0,
                recent_data_rate=0.0,
                geographic_coverage="No data",
                recommendations=["Broaden search criteria"]
            )

        # Calculate completeness
        total_completeness = sum(org.data_completeness or 0 for org in orgs)
        completeness_rate = total_completeness / len(orgs)

        # Calculate recent data rate
        recent_count = sum(1 for org in orgs if org.latest_990_year and org.latest_990_year >= 2020)
        recent_data_rate = recent_count / len(orgs)

        # Geographic coverage
        unique_states = len(set(org.state for org in orgs))
        if unique_states == 1:
            geo_coverage = "Single state"
        elif unique_states <= 5:
            geo_coverage = f"Regional ({unique_states} states)"
        else:
            geo_coverage = f"Multi-regional ({unique_states} states)"

        # Overall quality score
        overall_quality = (completeness_rate + recent_data_rate) / 2

        # Quality recommendations
        recommendations = []
        if completeness_rate < 0.7:
            recommendations.append("Consider requesting additional data sources")
        if recent_data_rate < 0.5:
            recommendations.append("Many organizations lack recent 990 filings")
        if len(orgs) < 5:
            recommendations.append("Consider broadening search criteria")

        return BMFQualityAssessment(
            overall_quality=overall_quality,
            completeness_rate=completeness_rate,
            recent_data_rate=recent_data_rate,
            geographic_coverage=geo_coverage,
            recommendations=recommendations
        )

    def _generate_recommendations(self, orgs: List[BMFOrganization], criteria: BMFFilterCriteria, summary: BMFSearchSummary) -> BMFRecommendations:
        """Generate recommendations for search refinement and next steps"""

        refinement_suggestions = []
        expansion_suggestions = []
        next_steps = []
        related_searches = []

        # Refinement suggestions based on results
        if len(orgs) > 100:
            refinement_suggestions.append("Consider adding revenue or asset filters to narrow results")
            refinement_suggestions.append("Add geographic restrictions to focus on specific regions")

        if len(orgs) == 0:
            expansion_suggestions.append("Remove or relax financial criteria")
            expansion_suggestions.append("Expand geographic scope to neighboring states")
            expansion_suggestions.append("Try broader NTEE codes or categories")

        # Next steps based on results
        if orgs:
            next_steps.append("Review top matches for partnership potential")
            next_steps.append("Research organizational leadership and board composition")
            next_steps.append("Analyze funding patterns and grant history")

            if len(orgs) > 20:
                next_steps.append("Apply additional scoring criteria to prioritize contacts")

        # Related searches
        if criteria.ntee_codes:
            related_searches.append("Similar organizations in different states")
            related_searches.append("Organizations with complementary focus areas")

        if criteria.states:
            related_searches.append("Similar organizations in neighboring states")

        return BMFRecommendations(
            refinement_suggestions=refinement_suggestions,
            expansion_suggestions=expansion_suggestions,
            next_steps=next_steps,
            related_searches=related_searches
        )

    def _create_error_result(self, intent: BMFFilterIntent, error_msg: str, execution_time: float) -> BMFFilterResult:
        """Create an error result when execution fails"""
        return BMFFilterResult(
            organizations=[],
            summary=BMFSearchSummary(
                total_found=0,
                total_in_database=0,
                criteria_summary=f"Error: {error_msg}",
                top_matches_description="Execution failed",
                geographic_distribution="N/A",
                financial_summary="N/A",
                recommendations=[f"Fix error: {error_msg}"]
            ),
            execution_metadata=BMFExecutionData(
                execution_time_ms=execution_time * 1000,
                database_query_time_ms=0,
                processing_time_ms=0,
                cache_hit=False,
                cache_key=None,
                results_truncated=False,
                query_complexity=BMFQueryComplexity.simple,
                memory_used_mb=0,
                database_rows_scanned=0
            ),
            quality_assessment=BMFQualityAssessment(
                overall_quality=0.0,
                completeness_rate=0.0,
                recent_data_rate=0.0,
                geographic_coverage="Error",
                recommendations=["Fix execution error and retry"]
            ),
            recommendations=BMFRecommendations(
                refinement_suggestions=[],
                expansion_suggestions=[],
                next_steps=["Resolve error and retry search"],
                related_searches=[]
            )
        )