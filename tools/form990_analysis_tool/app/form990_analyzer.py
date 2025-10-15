"""
Form 990 Analysis Tool - Deep Financial Analysis
==============================================

12-Factor Factor 4: Structured input/output with comprehensive Form 990 analysis
Second tool in the two-tool architecture for nonprofit grant research

Key Features:
- Deep financial analysis of Form 990/990-PF/990-EZ data
- Multi-year trend analysis and financial health assessment
- Grant capacity analysis for foundations and grant recipients
- Risk assessment and peer comparison capabilities
- Integration with BMF Filter Tool results
"""

import os
import time
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# For now, using simple dataclasses instead of BAML-generated classes
@dataclass
class Form990AnalysisCriteria:
    target_eins: List[str]
    years_to_analyze: int = 3
    include_990pf: bool = True
    include_990ez: bool = True
    financial_health_analysis: bool = True
    grant_capacity_analysis: bool = True
    trend_analysis: bool = True
    risk_assessment: bool = True
    max_organizations: int = 50

@dataclass
class Form990FinancialYear:
    year: int
    form_type: str
    total_revenue: Optional[int] = None
    total_expenses: Optional[int] = None
    total_assets: Optional[int] = None
    total_liabilities: Optional[int] = None
    net_assets: Optional[int] = None
    contributions: Optional[int] = None
    program_expenses: Optional[int] = None
    administrative_expenses: Optional[int] = None
    program_expense_ratio: Optional[float] = None

@dataclass
class Form990FinancialHealth:
    overall_score: float
    liquidity_score: float
    efficiency_score: float
    program_ratio: Optional[float] = None
    operating_margin: Optional[float] = None
    months_of_reserves: Optional[float] = None
    health_category: str = "fair"
    warning_flags: List[str] = None

    def __post_init__(self):
        if self.warning_flags is None:
            self.warning_flags = []

@dataclass
class Form990OrganizationAnalysis:
    ein: str
    name: str
    organization_type: str
    financial_years: List[Form990FinancialYear]
    latest_year: int
    financial_health: Form990FinancialHealth
    key_insights: List[str]
    data_quality_score: float

@dataclass
class Form990AnalysisResult:
    organizations: List[Form990OrganizationAnalysis]
    execution_time_ms: float
    total_organizations_analyzed: int
    analysis_period: str


class Form990AnalysisTool:
    """
    Form 990 Analysis Tool implementing 12-factor principles

    Provides deep financial analysis of nonprofit organizations using Form 990 data
    """

    def __init__(self):
        """Initialize Form 990 Analysis Tool with 12-factor configuration"""

        # Factor 3: Config from environment
        default_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "nonprofit_intelligence.db"))
        self.database_path = os.getenv("FORM990_DATABASE_PATH", default_db_path)
        self.cache_enabled = os.getenv("FORM990_CACHE_ENABLED", "true").lower() == "true"
        self.max_organizations = int(os.getenv("FORM990_MAX_ORGANIZATIONS", "50"))
        self.default_years = int(os.getenv("FORM990_DEFAULT_YEARS", "3"))
        self.timeout_seconds = int(os.getenv("FORM990_TIMEOUT_SECONDS", "300"))
        self.memory_limit_mb = int(os.getenv("FORM990_MEMORY_LIMIT_MB", "1024"))
        self.log_performance = os.getenv("FORM990_LOG_PERFORMANCE", "true").lower() == "true"

        # Validate database exists
        if not Path(self.database_path).exists():
            raise FileNotFoundError(f"Form 990 database not found at {self.database_path}")

        # Factor 6: Stateless caching
        self._cache = {} if self.cache_enabled else None

        # Test database connection and schema
        self._test_database_connection()

        logger.info("Form 990 Analysis Tool initialized successfully")

    def _test_database_connection(self) -> None:
        """Test database connection and verify required tables exist"""
        try:
            conn = sqlite3.connect(self.database_path)

            # Check for required tables
            required_tables = ['form_990', 'form_990pf', 'form_990ez', 'bmf_organizations']
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing_tables = set(required_tables) - existing_tables
            if missing_tables:
                raise ValueError(f"Missing required tables: {missing_tables}")

            # Test data availability
            cursor = conn.execute("SELECT COUNT(*) FROM form_990")
            form_990_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM form_990pf")
            form_990pf_count = cursor.fetchone()[0]

            logger.info(f"Database connection verified - 990: {form_990_count:,}, 990-PF: {form_990pf_count:,}")

            conn.close()

        except Exception as e:
            raise RuntimeError(f"Database connection test failed: {str(e)}")

    async def execute(self, criteria: Form990AnalysisCriteria) -> Form990AnalysisResult:
        """
        Execute Form 990 analysis with structured criteria

        Args:
            criteria: Structured analysis criteria

        Returns:
            Form990AnalysisResult: Comprehensive analysis results
        """
        start_time = time.time()

        try:
            # Validate input criteria
            self._validate_criteria(criteria)

            # Check cache (Factor 6: Stateless caching)
            cache_key = self._make_cache_key(criteria)
            if self.cache_enabled and cache_key in self._cache:
                logger.info("Returning cached Form 990 analysis result")
                return self._cache[cache_key]

            # Process organizations
            logger.info(f"Analyzing Form 990 data for {len(criteria.target_eins)} organizations")

            organizations = []
            for ein in criteria.target_eins[:criteria.max_organizations]:
                org_analysis = await self._analyze_organization(ein, criteria)
                if org_analysis:
                    organizations.append(org_analysis)

            # Create result
            execution_time = (time.time() - start_time) * 1000
            result = Form990AnalysisResult(
                organizations=organizations,
                execution_time_ms=execution_time,
                total_organizations_analyzed=len(organizations),
                analysis_period=f"{2024 - criteria.years_to_analyze + 1}-2024"
            )

            # Cache result (Factor 6: Stateless caching)
            if self.cache_enabled:
                self._cache[cache_key] = result

            # Performance logging (Factor 11: Logs as event streams)
            if self.log_performance:
                logger.info(
                    f"Form 990 Analysis completed - "
                    f"Organizations: {len(organizations)}, "
                    f"Time: {execution_time:.1f}ms"
                )

            return result

        except Exception as e:
            logger.error(f"Form 990 Analysis execution failed: {str(e)}")
            raise

    def _validate_criteria(self, criteria: Form990AnalysisCriteria) -> None:
        """Validate the incoming criteria"""
        if not criteria.target_eins:
            raise ValueError("Target EINs are required")

        if len(criteria.target_eins) > self.max_organizations:
            raise ValueError(f"Too many organizations requested. Max: {self.max_organizations}")

        # Validate EIN formats
        for ein in criteria.target_eins:
            if not ein.isdigit() or len(ein) != 9:
                raise ValueError(f"Invalid EIN format: {ein}")

    def _make_cache_key(self, criteria: Form990AnalysisCriteria) -> str:
        """Create cache key from analysis criteria"""
        key_parts = [
            f"eins:{','.join(sorted(criteria.target_eins))}",
            f"years:{criteria.years_to_analyze}",
            f"health:{criteria.financial_health_analysis}",
            f"grants:{criteria.grant_capacity_analysis}",
            f"trends:{criteria.trend_analysis}",
            f"risk:{criteria.risk_assessment}"
        ]
        return "|".join(key_parts)

    async def _analyze_organization(self, ein: str, criteria: Form990AnalysisCriteria) -> Optional[Form990OrganizationAnalysis]:
        """Analyze a single organization's Form 990 data"""
        try:
            # Get organization basic info from BMF
            org_info = self._get_organization_info(ein)
            if not org_info:
                logger.warning(f"Organization {ein} not found in BMF data")
                return None

            # Get multi-year financial data
            financial_years = self._get_financial_data(ein, criteria.years_to_analyze)
            if not financial_years:
                logger.warning(f"No financial data found for organization {ein}")
                return None

            # Perform financial health analysis
            financial_health = self._analyze_financial_health(financial_years)

            # Generate key insights
            key_insights = self._generate_insights(ein, financial_years, financial_health)

            # Calculate data quality score
            data_quality_score = self._calculate_data_quality(financial_years)

            return Form990OrganizationAnalysis(
                ein=ein,
                name=org_info['name'],
                organization_type=self._determine_org_type(financial_years),
                financial_years=financial_years,
                latest_year=max(year.year for year in financial_years) if financial_years else 0,
                financial_health=financial_health,
                key_insights=key_insights,
                data_quality_score=data_quality_score
            )

        except Exception as e:
            logger.error(f"Failed to analyze organization {ein}: {str(e)}")
            return None

    def _get_organization_info(self, ein: str) -> Optional[Dict[str, Any]]:
        """Get basic organization information from BMF data"""
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                "SELECT name, ntee_code, state FROM bmf_organizations WHERE ein = ?",
                (ein,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'name': row['name'],
                    'ntee_code': row['ntee_code'],
                    'state': row['state']
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get organization info for {ein}: {str(e)}")
            return None

    def _get_financial_data(self, ein: str, years: int) -> List[Form990FinancialYear]:
        """Get multi-year financial data for an organization"""
        financial_years = []

        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row

            # Get most recent years from form_990
            cursor = conn.execute("""
                SELECT tax_year, totrevenue, totfuncexpns, totassetsend, totliabend,
                       totcntrbgfts, prgmservrevnue
                FROM form_990
                WHERE ein = ?
                ORDER BY tax_year DESC
                LIMIT ?
            """, (ein, years))

            for row in cursor.fetchall():
                # Calculate derived metrics
                program_ratio = None
                if row['totfuncexpns'] and row['totfuncexpns'] > 0:
                    # Estimate program expenses (this would need more detailed calculation)
                    estimated_program = row['totfuncexpns'] * 0.8  # Rough estimate
                    program_ratio = estimated_program / row['totfuncexpns']

                financial_year = Form990FinancialYear(
                    year=row['tax_year'],
                    form_type="990",
                    total_revenue=row['totrevenue'],
                    total_expenses=row['totfuncexpns'],
                    total_assets=row['totassetsend'],
                    total_liabilities=row['totliabend'],
                    net_assets=(row['totassetsend'] or 0) - (row['totliabend'] or 0),
                    contributions=row['totcntrbgfts'],
                    program_expense_ratio=program_ratio
                )
                financial_years.append(financial_year)

            # Also check form_990pf for foundation data
            cursor = conn.execute("""
                SELECT tax_year, totassetsend, fairmrktvalamt, distribamt
                FROM form_990pf
                WHERE ein = ?
                ORDER BY tax_year DESC
                LIMIT ?
            """, (ein, years))

            pf_years = {}
            for row in cursor.fetchall():
                pf_years[row['tax_year']] = {
                    'form_type': '990-PF',
                    'total_assets': row['totassetsend'],
                    'fair_market_value': row['fairmrktvalamt'],
                    'distributions': row['distribamt']
                }

            # Merge 990-PF data with existing years or create new entries
            for year, pf_data in pf_years.items():
                existing_year = next((fy for fy in financial_years if fy.year == year), None)
                if existing_year:
                    existing_year.form_type = "990/990-PF"
                else:
                    financial_year = Form990FinancialYear(
                        year=year,
                        form_type="990-PF",
                        total_assets=pf_data['total_assets']
                    )
                    financial_years.append(financial_year)

            conn.close()

            # Sort by year (most recent first)
            financial_years.sort(key=lambda x: x.year, reverse=True)

        except Exception as e:
            logger.error(f"Failed to get financial data for {ein}: {str(e)}")

        return financial_years

    def _analyze_financial_health(self, financial_years: List[Form990FinancialYear]) -> Form990FinancialHealth:
        """Analyze financial health based on multi-year data"""
        if not financial_years:
            return Form990FinancialHealth(
                overall_score=0,
                liquidity_score=0,
                efficiency_score=0,
                health_category="unknown"
            )

        latest_year = financial_years[0]
        warning_flags = []

        # Calculate key ratios
        program_ratio = latest_year.program_expense_ratio
        operating_margin = None
        months_of_reserves = None

        if latest_year.total_revenue and latest_year.total_expenses:
            operating_margin = (latest_year.total_revenue - latest_year.total_expenses) / latest_year.total_revenue

        if latest_year.net_assets and latest_year.total_expenses:
            months_of_reserves = (latest_year.net_assets / latest_year.total_expenses) * 12

        # Assess financial health
        liquidity_score = 50  # Default
        if months_of_reserves is not None:
            if months_of_reserves > 12:
                liquidity_score = 90
            elif months_of_reserves > 6:
                liquidity_score = 75
            elif months_of_reserves > 3:
                liquidity_score = 60
            else:
                liquidity_score = 30
                warning_flags.append("Low operating reserves")

        efficiency_score = 50  # Default
        if program_ratio is not None:
            if program_ratio > 0.8:
                efficiency_score = 90
            elif program_ratio > 0.7:
                efficiency_score = 75
            elif program_ratio > 0.6:
                efficiency_score = 60
            else:
                efficiency_score = 40
                warning_flags.append("Low program expense ratio")

        # Overall score (simple average for now)
        overall_score = (liquidity_score + efficiency_score) / 2

        # Determine health category
        health_category = "fair"
        if overall_score >= 80:
            health_category = "excellent"
        elif overall_score >= 70:
            health_category = "good"
        elif overall_score >= 50:
            health_category = "fair"
        else:
            health_category = "poor"

        return Form990FinancialHealth(
            overall_score=overall_score,
            liquidity_score=liquidity_score,
            efficiency_score=efficiency_score,
            program_ratio=program_ratio,
            operating_margin=operating_margin,
            months_of_reserves=months_of_reserves,
            health_category=health_category,
            warning_flags=warning_flags
        )

    def _determine_org_type(self, financial_years: List[Form990FinancialYear]) -> str:
        """Determine organization type based on form types filed"""
        form_types = {year.form_type for year in financial_years}

        if "990-PF" in form_types:
            return "Private Foundation"
        elif "990" in form_types:
            return "Public Charity"
        elif "990-EZ" in form_types:
            return "Small Organization"
        else:
            return "Unknown"

    def _generate_insights(self, ein: str, financial_years: List[Form990FinancialYear],
                          health: Form990FinancialHealth) -> List[str]:
        """Generate key insights about the organization"""
        insights = []

        if len(financial_years) >= 2:
            latest = financial_years[0]
            previous = financial_years[1]

            # Revenue growth
            if latest.total_revenue and previous.total_revenue:
                growth = (latest.total_revenue - previous.total_revenue) / previous.total_revenue
                if growth > 0.1:
                    insights.append(f"Strong revenue growth of {growth:.1%} year-over-year")
                elif growth < -0.1:
                    insights.append(f"Revenue declined {abs(growth):.1%} year-over-year")

        # Financial health insights
        if health.health_category == "excellent":
            insights.append("Excellent financial health with strong reserves and efficiency")
        elif health.health_category == "poor":
            insights.append("Financial health concerns requiring attention")

        # Program efficiency insights
        if health.program_ratio and health.program_ratio > 0.85:
            insights.append("Highly efficient with excellent program expense ratio")

        # Add warning insights
        for warning in health.warning_flags:
            insights.append(f"Caution: {warning}")

        return insights[:5]  # Return top 5 insights

    def _calculate_data_quality(self, financial_years: List[Form990FinancialYear]) -> float:
        """Calculate data quality score based on completeness"""
        if not financial_years:
            return 0.0

        total_fields = 0
        completed_fields = 0

        for year in financial_years:
            year_fields = [
                year.total_revenue, year.total_expenses, year.total_assets,
                year.total_liabilities, year.contributions
            ]
            total_fields += len(year_fields)
            completed_fields += sum(1 for field in year_fields if field is not None)

        return completed_fields / total_fields if total_fields > 0 else 0.0