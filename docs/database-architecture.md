# BMF/SOI Database Architecture Guide

**Version**: 2.0  
**Created**: September 10, 2025  
**Status**: Production Ready  

## Executive Summary

The Catalynx grant research platform utilizes a dual database architecture combining application data management with comprehensive nonprofit financial intelligence. This document details the BMF/SOI Intelligence Database, which provides advanced nonprofit analysis capabilities through IRS Business Master File and Statistics of Income data integration.

## Architecture Overview

### Dual Database Design

```mermaid
graph TB
    A[Application Layer] --> B[Catalynx Application DB]
    A --> C[BMF/SOI Intelligence DB]
    
    B --> D[Profiles & Opportunities]
    B --> E[AI Processing Costs]
    B --> F[Export & Metrics]
    
    C --> G[BMF Organizations Index]
    C --> H[Form 990 Data]
    C --> I[Form 990-PF Data]
    C --> J[Form 990-EZ Data]
    
    G --> K[752K Organizations]
    H --> L[671K Large Nonprofits]
    I --> M[235K Foundations]
    J --> N[411K Small Nonprofits]
```

## Database Schema Design

### 1. BMF Organizations (Master Index)

**Purpose**: Central registry of all tax-exempt organizations with IRS recognition  
**Source**: IRS Business Master File Extract  
**Records**: 752,732 organizations  

#### Core Structure
```sql
CREATE TABLE bmf_organizations (
    -- Primary identification
    ein TEXT PRIMARY KEY,                    -- Employer Identification Number
    name TEXT NOT NULL,                     -- Organization name
    
    -- Location classification
    state TEXT,                             -- State abbreviation
    city TEXT,                              -- City
    ntee_code TEXT,                         -- NTEE classification
    
    -- Organizational classification
    classification TEXT,                    -- Organization type
    foundation_code TEXT,                   -- Foundation status (03/04 = foundations)
    subsection TEXT,                        -- Tax code subsection
    
    -- Financial summary
    asset_amt INTEGER,                      -- Asset amount (BMF data)
    income_amt INTEGER,                     -- Income amount (BMF data)
    revenue_amt INTEGER,                    -- Revenue amount (BMF data)
    
    -- Administrative data
    ruling_date TEXT,                       -- IRS ruling date
    tax_period TEXT,                        -- Tax period
    accounting_period TEXT                  -- Accounting period
);
```

#### Key Relationships
- **Primary Key**: EIN (unique identifier across all IRS systems)
- **Foreign Key Target**: Referenced by all SOI form tables
- **Classification Logic**: Foundation_code determines foundation status

#### Performance Indexes
```sql
CREATE INDEX idx_bmf_ntee_state ON bmf_organizations(ntee_code, state);
CREATE INDEX idx_bmf_state_revenue ON bmf_organizations(state, revenue_amt);
CREATE INDEX idx_bmf_classification ON bmf_organizations(classification, foundation_code);
```

### 2. Form 990 (Large Nonprofit Financial Data)

**Purpose**: Detailed financial and operational data for larger nonprofits  
**Source**: IRS SOI Annual Extract of Tax-Exempt Organization Financial Data  
**Records**: 671,484 filings (2022-2024)  
**Eligibility**: Organizations with gross receipts ≥ $200K or total assets ≥ $500K  

#### Comprehensive Field Coverage

**Core Financial Metrics** (15 primary fields):
- Total Revenue, Contributions, Program Service Revenue
- Total Functional Expenses, Assets, Liabilities, Net Assets
- Investment Income, Fundraising Income, Gaming Income

**Revenue Breakdown** (25+ detailed fields):
- Program Service Revenue (6 categories with NTEE codes)
- Investment Income, Rental Income, Sales Income
- Tax-Exempt Bond Proceeds, Royalties, Net Gains/Losses

**Expense Analysis** (30+ detailed fields):
- Grants to Government, Individuals, Foreign Governments
- Compensation: Officers, Employees, Benefits, Payroll Tax
- Professional Fees: Management, Legal, Accounting, Lobbying
- Operational: Office, IT, Travel, Insurance, Occupancy

**Asset Portfolio** (20+ detailed fields):
- Cash and Equivalents, Savings, Temporary Investments
- Receivables: Pledges, Accounts, Notes, Officers
- Fixed Assets: Land, Buildings, Equipment
- Investments: Public, Private, Program-Related

**Governance & Compliance** (25+ operational flags):
- Political Activities, Lobbying Activities
- School/Hospital Operations, Foreign Activities
- Schedule Requirements, Filing Indicators
- Public Support Tests, Private Foundation Status

#### Data Structure Example
```sql
-- Revenue analysis for large nonprofit
SELECT 
    ein,
    totrevenue as total_revenue,
    totcntrbgfts as contributions,
    prgmservrevnue as program_revenue,
    (totrevenue - totfuncexpns) as operating_margin,
    (prgmservrevnue / totrevenue * 100) as program_revenue_ratio
FROM form_990 
WHERE tax_year = 2024 AND totrevenue > 1000000;
```

### 3. Form 990-PF (Foundation Intelligence)

**Purpose**: Private foundation financial data with grant-making intelligence  
**Source**: IRS SOI Annual Extract (990-PF)  
**Records**: 235,374 foundation filings (2022-2024)  
**Coverage**: All private foundations filing Form 990-PF  

#### Grant-Making Intelligence

**Distribution Requirements**:
```sql
-- Foundation grant capacity analysis
distribamt INTEGER,                     -- Required annual distribution (5% rule)
contrpdpbks INTEGER,                   -- Actual grants paid (book value)
qlfydistribtot INTEGER,                -- Total qualifying distributions
grntapprvfut INTEGER,                  -- Future grants already approved
```

**Investment Analysis**:
```sql
-- Investment portfolio composition
fairmrktvalamt INTEGER,                -- Fair market value of assets
totinvstsec INTEGER,                   -- Total investments in securities
invstcorpstk INTEGER,                  -- Corporate stock investments
invstcorpbnd INTEGER,                  -- Corporate bond investments
netinvstinc INTEGER,                   -- Net investment income
```

**Financial Health Indicators**:
```sql
-- Foundation sustainability metrics
adjnetinc INTEGER,                     -- Adjusted net income
cmpmininvstret INTEGER,                -- Minimum investment return required
tfundnworth INTEGER,                   -- Total fund net worth
totexpnsexempt INTEGER                 -- Total expenses for exempt purposes
```

#### Grant Research Queries
```sql
-- Active grant-making foundations by capacity
SELECT 
    b.ein,
    b.name,
    b.state,
    pf.contrpdpbks as grants_paid,
    pf.fairmrktvalamt as assets_fmv,
    (pf.contrpdpbks / pf.fairmrktvalamt * 100) as payout_ratio,
    CASE 
        WHEN pf.contrpdpbks > 1000000 THEN 'Major Funder'
        WHEN pf.contrpdpbks > 100000 THEN 'Significant Funder'
        WHEN pf.contrpdpbks > 10000 THEN 'Moderate Funder'
        ELSE 'Small Funder'
    END as capacity_tier
FROM bmf_organizations b
JOIN form_990pf pf ON b.ein = pf.ein
WHERE pf.tax_year = 2024 
  AND pf.contrpdpbks > 0
  AND b.state IN ('VA', 'MD', 'DC')
ORDER BY pf.contrpdpbks DESC;
```

### 4. Form 990-EZ (Smaller Nonprofit Data)

**Purpose**: Simplified financial data for smaller tax-exempt organizations  
**Source**: IRS SOI Annual Extract (990-EZ)  
**Records**: 411,235 filings (2022-2024)  
**Eligibility**: Organizations with gross receipts < $200K and total assets < $500K  

#### Streamlined Data Model
- **Core Financials**: Revenue, expenses, net position (simplified)
- **Asset/Liability Summary**: Basic balance sheet information
- **Public Support Calculations**: Community foundation analysis
- **Operational Indicators**: Unrelated business income, public support ratios

## Data Quality & Validation

### ETL Pipeline Validation

```python
class BMFSOIDataQuality:
    """
    Data quality monitoring for BMF/SOI database.
    """
    
    def validate_ein_format(self, ein: str) -> bool:
        """Validate EIN format: XX-XXXXXXX"""
        return re.match(r'^\d{2}-?\d{7}$', ein) is not None
    
    def check_financial_consistency(self, record: dict) -> List[str]:
        """Check financial data consistency"""
        errors = []
        
        # Revenue consistency
        if record.get('totrevenue', 0) < 0:
            errors.append("Negative total revenue")
        
        # Asset/liability balance
        assets = record.get('totassetsend', 0)
        liabilities = record.get('totliabend', 0)
        net_assets = record.get('totnetassetend', 0)
        
        if abs((assets - liabilities) - net_assets) > 1000:
            errors.append("Balance sheet equation mismatch")
            
        return errors
    
    def generate_completeness_report(self) -> dict:
        """Generate data completeness report"""
        with sqlite3.connect(self.db_path) as conn:
            report = {}
            
            # BMF completeness
            bmf_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(ntee_code) as with_ntee,
                    COUNT(revenue_amt) as with_revenue,
                    COUNT(state) as with_state
                FROM bmf_organizations
            """).fetchone()
            
            report['bmf_completeness'] = {
                'total_records': bmf_stats[0],
                'ntee_coverage': bmf_stats[1] / bmf_stats[0] * 100,
                'revenue_coverage': bmf_stats[2] / bmf_stats[0] * 100,
                'state_coverage': bmf_stats[3] / bmf_stats[0] * 100
            }
            
            return report
```

## Performance Optimization

### Strategic Indexing Strategy

```sql
-- Discovery performance indexes
CREATE INDEX idx_bmf_discovery ON bmf_organizations(ntee_code, state, foundation_code);
CREATE INDEX idx_990_financial ON form_990(totrevenue, totassetsend, tax_year);
CREATE INDEX idx_990pf_grants ON form_990pf(contrpdpbks, fairmrktvalamt, tax_year);

-- Multi-table join optimization
CREATE INDEX idx_990_ein_year ON form_990(ein, tax_year);
CREATE INDEX idx_990pf_ein_year ON form_990pf(ein, tax_year);
CREATE INDEX idx_990ez_ein_year ON form_990ez(ein, tax_year);

-- Specialized discovery indexes
CREATE INDEX idx_foundation_active ON form_990pf(contrpdpbks) WHERE contrpdpbks > 0;
CREATE INDEX idx_large_nonprofits ON form_990(totrevenue) WHERE totrevenue > 1000000;
```

### Query Performance Guidelines

**Optimal Query Patterns**:
```sql
-- ✅ GOOD: Use indexes effectively
SELECT * FROM bmf_organizations 
WHERE ntee_code LIKE 'P2%' AND state = 'VA';

-- ✅ GOOD: Join with proper index usage
SELECT b.name, f.totrevenue
FROM bmf_organizations b
JOIN form_990 f ON b.ein = f.ein AND f.tax_year = 2024
WHERE b.state = 'VA' AND f.totrevenue > 500000;

-- ❌ AVOID: Full table scans
SELECT * FROM form_990 WHERE name LIKE '%cancer%';

-- ❌ AVOID: Complex calculations in WHERE clause
SELECT * FROM form_990 
WHERE (totrevenue - totfuncexpns) / totrevenue > 0.1;
```

## Advanced Views for Common Patterns

### 1. Organization Intelligence View

```sql
CREATE VIEW v_organization_intelligence AS
SELECT 
    b.ein,
    b.name,
    b.ntee_code,
    b.state,
    b.city,
    b.foundation_code,
    
    -- Latest financial data (any form)
    COALESCE(f990.totrevenue, f990ez.totrevnue, 0) as latest_revenue,
    COALESCE(f990.totassetsend, f990ez.totassetsend, 0) as latest_assets,
    COALESCE(f990.totfuncexpns, f990ez.totexpns, 0) as latest_expenses,
    
    -- Grant intelligence
    COALESCE(f990.grntstogovt, 0) as grants_to_government,
    COALESCE(f990.grnsttoindiv, 0) as grants_to_individuals,
    COALESCE(f990pf.contrpdpbks, 0) as foundation_grants_paid,
    
    -- Financial efficiency
    CASE 
        WHEN COALESCE(f990.totrevenue, f990ez.totrevnue, 0) > 0 
        THEN ((COALESCE(f990.totrevenue, f990ez.totrevnue, 0) - 
               COALESCE(f990.totfuncexpns, f990ez.totexpns, 0)) / 
               COALESCE(f990.totrevenue, f990ez.totrevnue, 0) * 100)
        ELSE 0 
    END as operating_margin_pct,
    
    -- Program revenue ratio
    CASE 
        WHEN COALESCE(f990.totrevenue, f990ez.totrevnue, 0) > 0 
        THEN (COALESCE(f990.prgmservrevnue, f990ez.prgmservrev, 0) / 
              COALESCE(f990.totrevenue, f990ez.totrevnue, 0) * 100)
        ELSE 0 
    END as program_revenue_ratio_pct,
    
    -- Latest filing information
    COALESCE(f990.tax_year, f990ez.tax_year, f990pf.tax_year) as latest_tax_year,
    CASE 
        WHEN f990.ein IS NOT NULL THEN '990'
        WHEN f990pf.ein IS NOT NULL THEN '990-PF' 
        WHEN f990ez.ein IS NOT NULL THEN '990-EZ'
        ELSE 'BMF-Only'
    END as form_type,
    
    -- Foundation-specific intelligence
    CASE 
        WHEN b.foundation_code IN ('03', '04') THEN 'Foundation'
        WHEN b.foundation_code = '15' THEN 'Church'
        WHEN b.foundation_code = '16' THEN 'Church Auxiliary'
        ELSE 'Public Charity'
    END as organization_type_detailed
    
FROM bmf_organizations b
LEFT JOIN (
    SELECT ein, totrevenue, totassetsend, totfuncexpns, prgmservrevnue, 
           grntstogovt, grnsttoindiv, tax_year,
           ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
    FROM form_990
) f990 ON b.ein = f990.ein AND f990.rn = 1
LEFT JOIN (
    SELECT ein, contrpdpbks, fairmrktvalamt, tax_year,
           ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
    FROM form_990pf
) f990pf ON b.ein = f990pf.ein AND f990pf.rn = 1
LEFT JOIN (
    SELECT ein, totrevnue, totassetsend, totexpns, prgmservrev, tax_year,
           ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
    FROM form_990ez
) f990ez ON b.ein = f990ez.ein AND f990ez.rn = 1;
```

### 2. Foundation Grant Intelligence View

```sql
CREATE VIEW v_foundation_grant_intelligence AS
SELECT 
    b.ein,
    b.name,
    b.state,
    b.city,
    b.ntee_code,
    
    -- Grant-making capacity
    pf.contrpdpbks as grants_paid_current_year,
    pf.fairmrktvalamt as fair_market_value_assets,
    pf.grntapprvfut as future_grants_approved,
    pf.distribamt as required_distribution,
    pf.adjnetinc as adjusted_net_income,
    
    -- Payout analysis
    CASE 
        WHEN pf.fairmrktvalamt > 0 
        THEN ROUND(pf.contrpdpbks / pf.fairmrktvalamt * 100, 2)
        ELSE 0 
    END as actual_payout_ratio,
    
    CASE 
        WHEN pf.fairmrktvalamt > 0 
        THEN ROUND(pf.distribamt / pf.fairmrktvalamt * 100, 2)
        ELSE 0 
    END as required_payout_ratio,
    
    -- Investment efficiency
    CASE 
        WHEN pf.fairmrktvalamt > 0 
        THEN ROUND(pf.netinvstinc / pf.fairmrktvalamt * 100, 2)
        ELSE 0 
    END as investment_return_ratio,
    
    -- Grant capacity tier
    CASE 
        WHEN pf.contrpdpbks > 10000000 THEN 'Mega Funder (>$10M)'
        WHEN pf.contrpdpbks > 1000000 THEN 'Major Funder ($1M-$10M)'
        WHEN pf.contrpdpbks > 100000 THEN 'Significant Funder ($100K-$1M)'
        WHEN pf.contrpdpbks > 10000 THEN 'Moderate Funder ($10K-$100K)'
        WHEN pf.contrpdpbks > 0 THEN 'Small Funder (<$10K)'
        ELSE 'No Recent Grants'
    END as grant_capacity_tier,
    
    -- Asset sustainability
    CASE 
        WHEN pf.fairmrktvalamt > 100000000 THEN 'Major Foundation (>$100M assets)'
        WHEN pf.fairmrktvalamt > 10000000 THEN 'Large Foundation ($10M-$100M assets)'
        WHEN pf.fairmrktvalamt > 1000000 THEN 'Mid-Size Foundation ($1M-$10M assets)'
        ELSE 'Small Foundation (<$1M assets)'
    END as asset_tier,
    
    -- Research priority
    CASE 
        WHEN pf.contrpdpbks > 100000 AND pf.fairmrktvalamt > 5000000 THEN 'HIGH'
        WHEN pf.contrpdpbks > 10000 AND pf.fairmrktvalamt > 1000000 THEN 'MEDIUM'
        WHEN pf.contrpdpbks > 0 THEN 'LOW'
        ELSE 'MINIMAL'
    END as research_priority,
    
    pf.tax_year
    
FROM bmf_organizations b
INNER JOIN (
    SELECT ein, contrpdpbks, fairmrktvalamt, grntapprvfut, distribamt, 
           adjnetinc, netinvstinc, tax_year,
           ROW_NUMBER() OVER (PARTITION BY ein ORDER BY tax_year DESC) as rn
    FROM form_990pf
) pf ON b.ein = pf.ein AND pf.rn = 1
WHERE b.foundation_code IN ('03', '04')  -- Only foundations
ORDER BY pf.contrpdpbks DESC;
```

## Integration Patterns

### 1. Discovery Enhancement

```python
class EnhancedBMFProcessor:
    """
    BMF processor with financial intelligence integration.
    """
    
    def discover_with_financial_intelligence(self, criteria: dict) -> List[dict]:
        """
        Enhanced discovery combining BMF data with SOI financial intelligence.
        """
        query = """
        SELECT 
            b.ein,
            b.name,
            b.ntee_code,
            b.state,
            b.city,
            oi.latest_revenue,
            oi.latest_assets,
            oi.operating_margin_pct,
            oi.program_revenue_ratio_pct,
            oi.foundation_grants_paid,
            oi.form_type,
            
            -- Foundation-specific data
            CASE WHEN b.foundation_code IN ('03', '04') THEN
                (SELECT actual_payout_ratio FROM v_foundation_grant_intelligence 
                 WHERE ein = b.ein LIMIT 1)
            END as foundation_payout_ratio
            
        FROM bmf_organizations b
        JOIN v_organization_intelligence oi ON b.ein = oi.ein
        WHERE 1=1
        """
        
        params = []
        
        # Apply criteria filters
        if criteria.get('ntee_codes'):
            ntee_conditions = ' OR '.join([f"b.ntee_code LIKE ?" 
                                         for _ in criteria['ntee_codes']])
            query += f" AND ({ntee_conditions})"
            params.extend([f"{code}%" for code in criteria['ntee_codes']])
        
        if criteria.get('states'):
            state_placeholders = ','.join(['?' for _ in criteria['states']])
            query += f" AND b.state IN ({state_placeholders})"
            params.extend(criteria['states'])
        
        if criteria.get('revenue_range'):
            min_rev, max_rev = criteria['revenue_range']
            query += " AND oi.latest_revenue BETWEEN ? AND ?"
            params.extend([min_rev, max_rev])
        
        if criteria.get('financial_filters'):
            filters = criteria['financial_filters']
            
            if filters.get('foundation_grants_paid'):
                query += " AND oi.foundation_grants_paid > 0"
            
            if filters.get('min_assets'):
                query += " AND oi.latest_assets >= ?"
                params.append(filters['min_assets'])
            
            if filters.get('grant_capacity'):
                capacity_map = {
                    'Major': 1000000,
                    'Significant': 100000,
                    'Moderate': 10000
                }
                min_grants = capacity_map.get(filters['grant_capacity'], 0)
                query += " AND oi.foundation_grants_paid >= ?"
                params.append(min_grants)
        
        query += " ORDER BY oi.latest_revenue DESC"
        
        with sqlite3.connect(self.intelligence_db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = conn.execute(query, params).fetchall()
            return [dict(row) for row in results]
```

### 2. Financial Analysis Service

```python
class FinancialIntelligenceService:
    """
    Advanced financial analysis using BMF/SOI data.
    """
    
    def analyze_organization_financial_health(self, ein: str) -> dict:
        """
        Comprehensive financial health analysis for an organization.
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get multi-year financial data
            financial_data = conn.execute("""
                SELECT tax_year, totrevenue, totfuncexpns, totassetsend,
                       totliabend, totnetassetend, prgmservrevnue,
                       grntstogovt, grnsttoindiv
                FROM form_990
                WHERE ein = ? 
                ORDER BY tax_year DESC 
                LIMIT 3
            """, (ein,)).fetchall()
            
            if not financial_data:
                return {'error': 'No financial data available'}
            
            analysis = {
                'ein': ein,
                'years_analyzed': len(financial_data),
                'latest_year': financial_data[0]['tax_year'],
                'financial_trends': {},
                'health_indicators': {},
                'grant_activity': {}
            }
            
            # Calculate trends
            if len(financial_data) >= 2:
                latest = financial_data[0]
                previous = financial_data[1]
                
                analysis['financial_trends'] = {
                    'revenue_growth': self._calculate_growth_rate(
                        previous['totrevenue'], latest['totrevenue']),
                    'asset_growth': self._calculate_growth_rate(
                        previous['totassetsend'], latest['totassetsend']),
                    'expense_growth': self._calculate_growth_rate(
                        previous['totfuncexpns'], latest['totfuncexpns'])
                }
            
            # Health indicators
            latest = financial_data[0]
            if latest['totrevenue'] > 0:
                analysis['health_indicators'] = {
                    'operating_margin': (latest['totrevenue'] - latest['totfuncexpns']) / latest['totrevenue'] * 100,
                    'program_ratio': (latest['prgmservrevnue'] or 0) / latest['totrevenue'] * 100,
                    'debt_to_assets': (latest['totliabend'] or 0) / (latest['totassetsend'] or 1) * 100
                }
            
            # Grant activity analysis
            total_grants = (latest['grntstogovt'] or 0) + (latest['grnsttoindiv'] or 0)
            analysis['grant_activity'] = {
                'total_grants_distributed': total_grants,
                'grants_to_government': latest['grntstogovt'] or 0,
                'grants_to_individuals': latest['grnsttoindiv'] or 0,
                'grant_intensity': total_grants / (latest['totrevenue'] or 1) * 100
            }
            
            return analysis
    
    def _calculate_growth_rate(self, old_value: float, new_value: float) -> float:
        """Calculate percentage growth rate."""
        if not old_value or old_value == 0:
            return 0
        return ((new_value - old_value) / old_value) * 100
```

## Security and Compliance

### Data Protection Measures

```python
class BMFSOISecurityManager:
    """
    Security and compliance management for BMF/SOI database.
    """
    
    def anonymize_sensitive_data(self, data: dict, access_level: str) -> dict:
        """
        Apply data anonymization based on access level.
        """
        if access_level == 'public':
            # Remove detailed financial data
            sensitive_fields = [
                'compnsatncurrofcr', 'compnsatnandothr', 
                'totreprtabled', 'totcomprelatede'
            ]
            for field in sensitive_fields:
                if field in data:
                    del data[field]
        
        elif access_level == 'researcher':
            # Aggregate compensation data
            if 'compnsatncurrofcr' in data:
                data['officer_compensation_range'] = self._categorize_compensation(
                    data['compnsatncurrofcr'])
                del data['compnsatncurrofcr']
        
        return data
    
    def audit_data_access(self, user_id: str, ein: str, data_type: str):
        """
        Log data access for compliance monitoring.
        """
        with sqlite3.connect(self.audit_db_path) as conn:
            conn.execute("""
                INSERT INTO data_access_log (
                    user_id, ein, data_type, access_timestamp, ip_address
                ) VALUES (?, ?, ?, ?, ?)
            """, (user_id, ein, data_type, datetime.now(), 
                  request.remote_addr if request else 'system'))
```

## Migration and Maintenance

### Database Maintenance Scripts

```python
class BMFSOIDatabaseMaintenance:
    """
    Database maintenance and optimization utilities.
    """
    
    def update_indexes_for_performance(self):
        """
        Update database indexes based on query patterns.
        """
        maintenance_sql = [
            "REINDEX;",
            "ANALYZE;",
            "PRAGMA optimize;",
            
            # Update statistics
            "UPDATE bmf_organizations SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;",
            
            # Cleanup orphaned records
            """DELETE FROM form_990 
               WHERE ein NOT IN (SELECT ein FROM bmf_organizations);""",
            
            # Update derived fields
            """UPDATE form_990 SET 
               operating_margin = (totrevenue - totfuncexpns) / totrevenue * 100
               WHERE totrevenue > 0;"""
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            for sql in maintenance_sql:
                conn.execute(sql)
            conn.commit()
    
    def generate_health_check_report(self) -> dict:
        """
        Generate comprehensive database health report.
        """
        with sqlite3.connect(self.db_path) as conn:
            report = {
                'database_size': os.path.getsize(self.db_path) / (1024**3),  # GB
                'table_counts': {},
                'index_usage': {},
                'data_quality_metrics': {}
            }
            
            # Table counts
            tables = ['bmf_organizations', 'form_990', 'form_990pf', 'form_990ez']
            for table in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                report['table_counts'][table] = count
            
            # Data quality metrics
            quality_checks = [
                ("BMF EIN format", "SELECT COUNT(*) FROM bmf_organizations WHERE ein NOT LIKE '__-_______'"),
                ("Missing NTEE codes", "SELECT COUNT(*) FROM bmf_organizations WHERE ntee_code IS NULL"),
                ("Negative revenues", "SELECT COUNT(*) FROM form_990 WHERE totrevenue < 0"),
                ("Balance sheet errors", """
                    SELECT COUNT(*) FROM form_990 
                    WHERE ABS((totassetsend - totliabend) - totnetassetend) > 1000
                """)
            ]
            
            for check_name, sql in quality_checks:
                count = conn.execute(sql).fetchone()[0]
                report['data_quality_metrics'][check_name] = count
            
            return report
```

## Conclusion

The BMF/SOI database architecture provides a robust foundation for advanced nonprofit financial intelligence and grant research capabilities. Key achievements include:

- **Comprehensive Coverage**: 2M+ organizations with detailed financial data
- **Performance Optimization**: Strategic indexing for sub-second queries
- **Intelligence Views**: Pre-built analysis patterns for common use cases
- **Data Quality**: Robust validation and monitoring systems
- **Security**: Access controls and compliance monitoring

This architecture enables the Catalynx platform to deliver sophisticated grant research intelligence while maintaining high performance and data integrity.