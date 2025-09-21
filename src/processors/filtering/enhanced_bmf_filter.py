"""
Enhanced BMF Filter Processor - Comprehensive Nonprofit Intelligence
Created: September 10, 2025

This processor replaces the original BMF CSV-based filter with a comprehensive
SQL database approach utilizing BMF + SOI data for advanced nonprofit discovery.

Features:
- SQL database queries instead of CSV parsing
- Multi-year financial analysis (2022-2024)
- Foundation intelligence (990-PF data)
- Small nonprofit coverage (990-EZ data)
- Advanced financial filtering and scoring
- Real-time trend analysis
- Geographic and sector intelligence
"""

import sqlite3
import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path

from src.core.base_processor import BaseProcessor, ProcessorMetadata, SyncProcessorMixin, BatchProcessorMixin
from src.core.data_models import ProcessorConfig, ProcessorResult, OrganizationProfile
from src.profiles.models import FormType, FoundationType, ApplicationAcceptanceStatus
from src.utils.decorators import retry_on_failure, cache_result
from src.utils.validators import validate_ein, validate_state_code, validate_ntee_code, normalize_ein

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedBMFFilterProcessor(BaseProcessor, SyncProcessorMixin, BatchProcessorMixin):
    """
    Enhanced BMF Filter Processor using comprehensive SQL database.
    
    This processor provides advanced nonprofit discovery capabilities using
    the integrated BMF/SOI database with multi-year financial intelligence,
    foundation grant-making analysis, and sophisticated filtering options.
    
    Capabilities:
    - Comprehensive organizational discovery across all form types
    - Multi-year financial trend analysis
    - Foundation grant-making intelligence
    - Advanced financial health scoring
    - Geographic and sector-based filtering
    - Real-time query performance with indexed database
    """
    
    def __init__(self):
        metadata = ProcessorMetadata(
            name="enhanced_bmf_filter",
            description="Enhanced nonprofit discovery using comprehensive BMF/SOI database",
            version="2.0.0",
            dependencies=[],  # Self-contained with database
            estimated_duration=5,  # Much faster with SQL queries
            requires_network=False,
            requires_api_key=False,
            can_run_parallel=True,  # SQL queries can run in parallel
            processor_type="discovery"
        )
        super().__init__(metadata)
        
        # Database configuration
        self.database_path = "data/nonprofit_intelligence.db"
        
        # Query templates for different discovery modes
        self.base_query = """
            SELECT DISTINCT
                b.ein,
                b.name,
                b.ntee_code,
                b.state,
                b.city,
                b.classification,
                b.foundation_code,
                b.asset_amt as bmf_assets,
                b.income_amt as bmf_income,
                b.revenue_amt as bmf_revenue,
                -- Latest financial data from any form type
                COALESCE(f990.totrevenue, f990ez.totrevnue, 0) as latest_revenue,
                COALESCE(f990.totassetsend, f990ez.totassetsend, 0) as latest_assets,
                COALESCE(f990.grntstogovt, 0) as grants_to_government,
                COALESCE(f990.grnsttoindiv, 0) as grants_to_individuals,
                COALESCE(f990pf.contrpdpbks, 0) as foundation_grants_paid,
                COALESCE(f990pf.grntapprvfut, 0) as foundation_future_grants,
                COALESCE(f990pf.fairmrktvalamt, 0) as foundation_assets_fmv,
                -- Organization type indicators
                CASE 
                    WHEN f990.ein IS NOT NULL THEN '990'
                    WHEN f990pf.ein IS NOT NULL THEN '990-PF'
                    WHEN f990ez.ein IS NOT NULL THEN '990-EZ'
                    ELSE 'BMF-Only'
                END as form_type,
                -- Latest tax year with data
                COALESCE(f990.tax_year, f990ez.tax_year, f990pf.tax_year) as latest_tax_year,
                -- Operational indicators
                f990.operateschools170cd as operates_schools,
                f990.operatehosptlcd as operates_hospital,
                f990.rptgrntstogovtcd as reports_grants_govt,
                f990.rptgrntstoindvcd as reports_grants_indiv,
                -- Financial health indicators
                CASE 
                    WHEN COALESCE(f990.totrevenue, f990ez.totrevnue, 0) > 0 THEN
                        ROUND(COALESCE(f990.totfuncexpns, f990ez.totexpns, 0) * 100.0 / 
                              COALESCE(f990.totrevenue, f990ez.totrevnue, 1), 2)
                    ELSE NULL
                END as expense_ratio,
                CASE
                    WHEN COALESCE(f990.totrevenue, f990ez.totrevnue, 0) > 0 THEN
                        ROUND(COALESCE(f990.prgmservrevnue, f990ez.prgmservrev, 0) * 100.0 / 
                              COALESCE(f990.totrevenue, f990ez.totrevnue, 1), 2)
                    ELSE NULL
                END as program_revenue_ratio
            FROM bmf_organizations b
            LEFT JOIN (
                SELECT ein, totrevenue, totassetsend, grntstogovt, grnsttoindiv, totfuncexpns, 
                       prgmservrevnue, tax_year, operateschools170cd, operatehosptlcd, 
                       rptgrntstogovtcd, rptgrntstoindvcd,
                       ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
                FROM form_990
            ) f990 ON b.ein = f990.ein AND f990.rn = 1
            LEFT JOIN (
                SELECT ein, contrpdpbks, grntapprvfut, fairmrktvalamt, tax_year,
                       ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
                FROM form_990pf
            ) f990pf ON b.ein = f990pf.ein AND f990pf.rn = 1
            LEFT JOIN (
                SELECT ein, totrevnue, totassetsend, prgmservrev, totexpns, tax_year,
                       ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
                FROM form_990ez
            ) f990ez ON b.ein = f990ez.ein AND f990ez.rn = 1
        """
    
    def _get_database_connection(self) -> sqlite3.Connection:
        """Get database connection with optimizations."""
        conn = sqlite3.connect(self.database_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Performance optimizations
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
        conn.execute("PRAGMA synchronous = NORMAL")  # Balanced performance/safety
        conn.execute("PRAGMA cache_size = 10000")  # Larger cache
        conn.execute("PRAGMA temp_store = MEMORY")  # Use memory for temporary storage
        
        return conn
    
    def _build_where_clause(self, config: ProcessorConfig) -> tuple[str, list]:
        """
        Build dynamic WHERE clause based on workflow configuration.
        
        Returns:
            Tuple of (where_clause, parameters)
        """
        where_conditions = []
        parameters = []
        
        workflow_config = config.workflow_config
        
        # NTEE code filtering
        if workflow_config.ntee_codes:
            ntee_conditions = []
            for ntee_code in workflow_config.ntee_codes:
                ntee_conditions.append("b.ntee_code LIKE ?")
                parameters.append(f"{ntee_code}%")  # Prefix matching
            
            where_conditions.append(f"({' OR '.join(ntee_conditions)})")
        
        # State filtering
        states = workflow_config.get_all_states()
        if states:
            state_placeholders = ', '.join(['?' for _ in states])
            where_conditions.append(f"b.state IN ({state_placeholders})")
            parameters.extend(states)
        
        # Revenue filtering (now for data insights, not exclusion)
        if workflow_config.min_revenue is not None:
            where_conditions.append("""
                (COALESCE(f990.totrevenue, f990ez.totrevnue, b.revenue_amt, 0) >= ? 
                 OR f990pf.contrpdpbks >= ?)
            """)
            parameters.extend([workflow_config.min_revenue, workflow_config.min_revenue])
        
        if workflow_config.max_revenue is not None:
            where_conditions.append("""
                (COALESCE(f990.totrevenue, f990ez.totrevnue, b.revenue_amt, 999999999) <= ? 
                 OR f990pf.contrpdpbks <= ?)
            """)
            parameters.extend([workflow_config.max_revenue, workflow_config.max_revenue])
        
        # Asset filtering (for insights, not exclusion)
        if workflow_config.min_assets is not None:
            where_conditions.append("""
                (COALESCE(f990.totassetsend, f990ez.totassetsend, b.asset_amt, 0) >= ?
                 OR f990pf.fairmrktvalamt >= ?)
            """)
            parameters.extend([workflow_config.min_assets, workflow_config.min_assets])
        
        if workflow_config.max_assets is not None:
            where_conditions.append("""
                (COALESCE(f990.totassetsend, f990ez.totassetsend, b.asset_amt, 999999999) <= ?
                 OR f990pf.fairmrktvalamt <= ?)
            """)
            parameters.extend([workflow_config.max_assets, workflow_config.max_assets])
        
        # Foundation-specific filtering
        if hasattr(workflow_config, 'foundation_only') and workflow_config.foundation_only:
            where_conditions.append("f990pf.ein IS NOT NULL")
        
        # Active grant-making foundations
        if hasattr(workflow_config, 'active_grantmakers_only') and workflow_config.active_grantmakers_only:
            where_conditions.append("f990pf.contrpdpbks > 0")
        
        # Organization type filtering
        if hasattr(workflow_config, 'form_types') and workflow_config.form_types:
            form_type_conditions = []
            for form_type in workflow_config.form_types:
                if form_type == '990':
                    form_type_conditions.append("f990.ein IS NOT NULL")
                elif form_type == '990-PF':
                    form_type_conditions.append("f990pf.ein IS NOT NULL")
                elif form_type == '990-EZ':
                    form_type_conditions.append("f990ez.ein IS NOT NULL")
            
            if form_type_conditions:
                where_conditions.append(f"({' OR '.join(form_type_conditions)})")
        
        # Build final WHERE clause
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        else:
            where_clause = ""
        
        return where_clause, parameters
    
    def _build_order_clause(self, config: ProcessorConfig) -> str:
        """Build ORDER BY clause for result prioritization."""
        # Priority-based ordering for grant research
        return """
            ORDER BY 
                -- Priority 1: Active foundations with substantial grant-making
                CASE WHEN f990pf.contrpdpbks > 1000000 THEN 1 ELSE 2 END,
                -- Priority 2: Large nonprofits with government grant programs
                CASE WHEN f990.grntstogovt > 100000 OR f990.grnsttoindiv > 100000 THEN 1 ELSE 2 END,
                -- Priority 3: Total financial capacity (revenue or assets)
                COALESCE(f990.totrevenue, f990ez.totrevnue, f990pf.fairmrktvalamt, b.revenue_amt, 0) DESC,
                -- Priority 4: Recent data availability
                latest_tax_year DESC NULLS LAST,
                -- Priority 5: Organization name
                b.name ASC
        """
    
    def _create_organization_profile(self, row: sqlite3.Row) -> OrganizationProfile:
        """
        Create comprehensive OrganizationProfile from database row.
        
        Args:
            row: Database row with comprehensive organization data
            
        Returns:
            Enhanced OrganizationProfile with SOI financial intelligence
        """
        try:
            # Determine form type and foundation status
            form_type = FormType.UNKNOWN
            foundation_type = FoundationType.UNKNOWN
            
            if row['form_type'] == '990':
                form_type = FormType.FORM_990
            elif row['form_type'] == '990-PF':
                form_type = FormType.FORM_990_PF
                foundation_type = FoundationType.PRIVATE_FOUNDATION
            elif row['form_type'] == '990-EZ':
                form_type = FormType.FORM_990_EZ
            
            # Create comprehensive profile
            profile = OrganizationProfile(
                ein=row['ein'],
                name=row['name'],
                ntee_code=row['ntee_code'],
                state=row['state'],
                city=row['city'],
                form_type=form_type,
                foundation_type=foundation_type,
                
                # Enhanced financial data
                revenue=row['latest_revenue'] or row['bmf_revenue'],
                assets=row['latest_assets'] or row['bmf_assets'],
                
                # Foundation-specific data
                foundation_grants_paid=row['foundation_grants_paid'],
                foundation_future_grants=row['foundation_future_grants'],
                foundation_assets_fmv=row['foundation_assets_fmv'],
                
                # Grant program indicators
                grants_to_government=row['grants_to_government'],
                grants_to_individuals=row['grants_to_individuals'],
                
                # Operational characteristics
                operates_schools=row['operates_schools'] == 'Y',
                operates_hospital=row['operates_hospital'] == 'Y',
                reports_government_grants=row['reports_grants_govt'] == 'Y',
                reports_individual_grants=row['reports_grants_indiv'] == 'Y',
                
                # Financial health metrics
                expense_ratio=row['expense_ratio'],
                program_revenue_ratio=row['program_revenue_ratio'],
                
                # Data quality indicators
                latest_tax_year=row['latest_tax_year'],
                data_source=row['form_type'],
                
                # Grant research relevance scoring
                grant_relevance_score=self._calculate_grant_relevance_score(row),
                
                # Application acceptance (initialize as unknown)
                application_acceptance_status=ApplicationAcceptanceStatus.UNKNOWN
            )
            
            return profile
            
        except Exception as e:
            logger.warning(f"Error creating organization profile for EIN {row.get('ein', 'unknown')}: {e}")
            return None
    
    def _calculate_grant_relevance_score(self, row: sqlite3.Row) -> float:
        """
        Calculate grant research relevance score based on comprehensive data.
        
        Args:
            row: Database row with organization data
            
        Returns:
            Score from 0.0 to 1.0 indicating grant research relevance
        """
        score = 0.0
        
        try:
            # Foundation grant-making activity (40% weight)
            if row['foundation_grants_paid']:
                if row['foundation_grants_paid'] > 1000000:  # Major foundation
                    score += 0.40
                elif row['foundation_grants_paid'] > 100000:  # Significant foundation
                    score += 0.30
                elif row['foundation_grants_paid'] > 10000:  # Active foundation
                    score += 0.20
                else:  # Small foundation
                    score += 0.10
            
            # Government grant programs (30% weight)
            govt_grants = (row['grants_to_government'] or 0) + (row['grants_to_individuals'] or 0)
            if govt_grants > 0:
                if govt_grants > 500000:  # Major government partner
                    score += 0.30
                elif govt_grants > 100000:  # Significant government partner
                    score += 0.25
                elif govt_grants > 10000:  # Active government partner
                    score += 0.15
                else:  # Small government programs
                    score += 0.10
            
            # Financial capacity (20% weight)
            financial_capacity = max(
                row['latest_revenue'] or 0,
                row['latest_assets'] or 0,
                row['foundation_assets_fmv'] or 0,
                row['bmf_revenue'] or 0
            )
            
            if financial_capacity > 10000000:  # Major organization
                score += 0.20
            elif financial_capacity > 1000000:  # Large organization
                score += 0.15
            elif financial_capacity > 100000:  # Medium organization
                score += 0.10
            elif financial_capacity > 10000:  # Small but viable
                score += 0.05
            
            # Data recency and completeness (10% weight)
            if row['latest_tax_year']:
                if row['latest_tax_year'] >= 2023:  # Very recent data
                    score += 0.10
                elif row['latest_tax_year'] >= 2022:  # Recent data
                    score += 0.08
                elif row['latest_tax_year'] >= 2021:  # Somewhat recent
                    score += 0.05
            
            # Special program indicators (bonus points)
            if row['operates_schools'] == 'Y':
                score += 0.05
            if row['operates_hospital'] == 'Y':
                score += 0.05
            if row['foundation_future_grants'] and row['foundation_future_grants'] > 0:
                score += 0.05
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.warning(f"Error calculating grant relevance score: {e}")
            return 0.0
    
    async def execute(self, config: ProcessorConfig, workflow_state=None) -> ProcessorResult:
        """
        Execute enhanced BMF discovery using SQL database.
        
        Args:
            config: Processor configuration with workflow parameters
            workflow_state: Optional workflow state (unused)
            
        Returns:
            ProcessorResult with discovered organizations and metadata
        """
        start_time = datetime.now()
        result = ProcessorResult(
            processor_name=self.metadata.name,
            success=False,
            start_time=start_time
        )
        
        try:
            logger.info("Starting enhanced BMF discovery with comprehensive database...")
            
            # Validate configuration
            validation_errors = []
            workflow_config = config.workflow_config
            
            if not workflow_config.ntee_codes:
                validation_errors.append("At least one NTEE code is required")
            
            if not workflow_config.get_all_states():
                validation_errors.append("At least one state is required")
            
            if validation_errors:
                result.add_error("Configuration validation failed", {"errors": validation_errors})
                result.end_time = datetime.now()
                return result
            
            # Connect to database
            conn = self._get_database_connection()
            
            try:
                # Build dynamic query
                where_clause, parameters = self._build_where_clause(config)
                order_clause = self._build_order_clause(config)
                
                # Add result limit
                limit_clause = f"LIMIT {workflow_config.max_results}" if workflow_config.max_results else "LIMIT 1000"
                
                # Construct final query
                final_query = f"{self.base_query} {where_clause} {order_clause} {limit_clause}"
                
                logger.info(f"Executing database query with {len(parameters)} parameters...")
                
                # Execute query
                cursor = conn.execute(final_query, parameters)
                rows = cursor.fetchall()
                
                logger.info(f"Database query returned {len(rows)} organizations")
                
                # Process results
                organizations = []
                for row in rows:
                    try:
                        profile = self._create_organization_profile(row)
                        if profile:
                            organizations.append(profile)
                    except Exception as e:
                        logger.warning(f"Error processing organization {row.get('ein', 'unknown')}: {e}")
                        result.add_warning(f"Failed to process organization: {e}")
                        continue
                
                # Sort by grant relevance score
                organizations.sort(key=lambda x: x.grant_relevance_score or 0, reverse=True)
                
                # Populate result
                result.success = True
                result.add_data("organizations", organizations)
                result.add_data("organizations_count", len(organizations))
                result.add_data("database_path", self.database_path)
                result.add_data("query_execution_time", (datetime.now() - start_time).total_seconds())
                
                # Add metadata
                result.add_metadata("discovery_type", "enhanced_sql_database")
                result.add_metadata("ntee_codes", workflow_config.ntee_codes)
                result.add_metadata("states", workflow_config.get_all_states())
                result.add_metadata("financial_filters", {
                    "min_revenue": workflow_config.min_revenue,
                    "max_revenue": workflow_config.max_revenue,
                    "min_assets": workflow_config.min_assets,
                    "max_assets": workflow_config.max_assets
                })
                result.add_metadata("result_limit", workflow_config.max_results)
                
                # Log summary
                logger.info(f"Enhanced BMF discovery successful: {len(organizations)} organizations found")
                logger.info(f"Query executed in {(datetime.now() - start_time).total_seconds():.2f} seconds")
                
                # Data source breakdown
                form_types = {}
                foundation_count = 0
                govt_grant_programs = 0
                
                for org in organizations:
                    form_type = org.data_source or 'BMF-Only'
                    form_types[form_type] = form_types.get(form_type, 0) + 1
                    
                    if org.foundation_grants_paid and org.foundation_grants_paid > 0:
                        foundation_count += 1
                    
                    if (org.grants_to_government and org.grants_to_government > 0) or \
                       (org.grants_to_individuals and org.grants_to_individuals > 0):
                        govt_grant_programs += 1
                
                result.add_metadata("data_source_breakdown", form_types)
                result.add_metadata("active_foundations", foundation_count)
                result.add_metadata("government_grant_programs", govt_grant_programs)
                
            finally:
                conn.close()
            
        except Exception as e:
            logger.error(f"Enhanced BMF discovery failed: {e}")
            result.add_error("Discovery execution failed", {"error": str(e)})
        
        result.end_time = datetime.now()
        return result


def main():
    """Test the enhanced BMF filter processor."""
    import sys
    sys.path.append('src')
    from src.core.data_models import WorkflowConfig, ProcessorConfig
    
    async def test_enhanced_bmf():
        # Create processor
        processor = EnhancedBMFFilterProcessor()
        
        # Create test configuration (Heroes Bridge L-codes)
        workflow_config = WorkflowConfig(
            workflow_id='test_enhanced_bmf',
            states=['VA'],
            ntee_codes=['L11', 'L20', 'L99', 'L82', 'L81', 'L80', 'L41', 'L24', 'F40'],
            max_results=50
        )
        
        config = ProcessorConfig(
            workflow_id='test_enhanced_bmf',
            processor_name='enhanced_bmf_filter',
            workflow_config=workflow_config
        )
        
        # Execute discovery
        try:
            result = await processor.execute(config)
            
            if result.success:
                orgs = result.data.get('organizations', [])
                print(f"✅ Enhanced BMF Discovery Success: {len(orgs)} organizations found")
                print(f"⚡ Query time: {result.data.get('query_execution_time', 0):.2f} seconds")
                print(f"📊 Data sources: {result.metadata.get('data_source_breakdown', {})}")
                print(f"🏛️ Active foundations: {result.metadata.get('active_foundations', 0)}")
                print(f"🏢 Government programs: {result.metadata.get('government_grant_programs', 0)}")
                
                print("\n🎯 Top 5 Organizations by Grant Relevance:")
                for i, org in enumerate(orgs[:5]):
                    relevance = org.grant_relevance_score or 0
                    revenue = org.revenue or 0
                    grants = org.foundation_grants_paid or 0
                    print(f"  {i+1}. {org.name} (Score: {relevance:.2f}, Revenue: ${revenue:,}, Grants: ${grants:,})")
            
            else:
                print("❌ Enhanced BMF Discovery failed")
                print(f"Errors: {result.errors}")
        
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Run test
    asyncio.run(test_enhanced_bmf())


if __name__ == "__main__":
    main()