"""
Comprehensive Database Audit - All SOI Files vs Current Database Schema
Evaluates ALL 9 SOI files + BMF file against database schema
"""

import pandas as pd
import sqlite3
from typing import Dict, List, Set

# File mappings
FILES = {
    '990': {
        '2022': 'SOI_Files/22eoextract990.csv',
        '2023': 'SOI_Files/23eoextract990.csv',
        '2024': 'SOI_Files/24eoextract990.csv'
    },
    '990PF': {
        '2022': 'SOI_Files/22eoextract990pf.csv',
        '2023': 'SOI_Files/23eoextract990pf.csv',
        '2024': 'SOI_Files/24eoextract990pf.csv'
    },
    '990EZ': {
        '2022': 'SOI_Files/22eoextractez.csv',
        '2023': 'SOI_Files/23eoextractez.csv',
        '2024': 'SOI_Files/24eoextract990EZ.csv'
    },
    'BMF': {
        'current': 'SOI_Files/eo2.csv'
    }
}

def get_csv_columns(filepath: str) -> Set[str]:
    """Get column names from CSV file"""
    try:
        df = pd.read_csv(filepath, nrows=0)
        return set([col.lower() for col in df.columns])
    except Exception as e:
        print(f"ERROR reading {filepath}: {e}")
        return set()

def get_db_columns(table_name: str) -> Set[str]:
    """Get column names from database table"""
    conn = sqlite3.connect('data/nonprofit_intelligence.db')
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info({table_name})')
    cols = set([row[1].lower() for row in cursor.fetchall() if row[1] not in ['created_at', 'updated_at']])
    conn.close()
    return cols

def get_db_records() -> Dict[str, Dict[int, int]]:
    """Get current record counts by table and year"""
    conn = sqlite3.connect('data/nonprofit_intelligence.db')
    cursor = conn.cursor()

    records = {}
    for table in ['form_990', 'form_990pf', 'form_990ez']:
        cursor.execute(f'SELECT tax_year, COUNT(*) FROM {table} GROUP BY tax_year ORDER BY tax_year')
        records[table] = {year: count for year, count in cursor.fetchall()}

    cursor.execute('SELECT COUNT(*) FROM bmf_organizations')
    records['bmf_organizations'] = {'total': cursor.fetchone()[0]}

    conn.close()
    return records

def categorize_missing_columns(missing: Set[str], form_type: str) -> Dict[str, List[str]]:
    """Categorize missing columns by importance for grant research"""

    # Critical keywords by form type
    critical_keywords = {
        '990': ['grant', 'revenue', 'asset', 'expense', 'compen', 'public'],
        '990PF': ['adjnetinc', 'endwmnt', 'qlfyasset', 'progsrvc', 'excessrcpts', 'excptrans', 's4960', 'distribamt', 'contrpd'],
        '990EZ': ['revenue', 'asset', 'expense', 'support', 'grant'],
        'BMF': ['ntee', 'classification', 'foundation', 'revenue', 'asset']
    }

    important_keywords = {
        '990': ['compensation', 'investment', 'functional', 'netasset'],
        '990PF': ['investment', 'qualifying', 'foundation', 'payout'],
        '990EZ': ['contribution', 'netasset', 'public'],
        'BMF': ['subsection', 'organization', 'status']
    }

    critical = []
    important = []
    minor = []

    for col in sorted(missing):
        col_lower = col.lower()

        # Check critical
        if any(keyword in col_lower for keyword in critical_keywords.get(form_type, [])):
            critical.append(col.upper())
        # Check important
        elif any(keyword in col_lower for keyword in important_keywords.get(form_type, [])):
            important.append(col.upper())
        else:
            minor.append(col.upper())

    return {
        'critical': critical,
        'important': important,
        'minor': minor
    }

def main():
    print("="*100)
    print("COMPREHENSIVE DATABASE AUDIT - ALL SOI FILES vs CURRENT DATABASE")
    print("="*100)

    # Get current database state
    db_records = get_db_records()

    print("\nCURRENT DATABASE STATE:")
    print("-"*100)
    for table, years in db_records.items():
        if table == 'bmf_organizations':
            print(f"{table:25} Total: {years['total']:,} organizations")
        else:
            for year, count in years.items():
                print(f"{table:25} {year}: {count:,} records")

    # Audit each form type
    all_findings = {}

    for form_type, years in FILES.items():
        if form_type == 'BMF':
            table_name = 'bmf_organizations'
        elif form_type == '990PF':
            table_name = 'form_990pf'
        elif form_type == '990EZ':
            table_name = 'form_990ez'
        else:
            table_name = 'form_990'

        # Get database columns
        db_cols = get_db_columns(table_name)

        # Check each year
        year_findings = {}
        for year, filepath in years.items():
            csv_cols = get_csv_columns(filepath)

            if not csv_cols:
                continue

            # Calculate differences
            missing_from_db = csv_cols - db_cols
            extra_in_db = db_cols - csv_cols

            # Categorize missing
            categorized = categorize_missing_columns(missing_from_db, form_type)

            year_findings[year] = {
                'csv_cols': len(csv_cols),
                'db_cols': len(db_cols),
                'missing': categorized,
                'extra': sorted([col.upper() for col in extra_in_db]),
                'coverage': round(len(db_cols & csv_cols) / len(csv_cols) * 100, 1) if csv_cols else 0
            }

        all_findings[form_type] = year_findings

    # Print detailed findings
    print("\n" + "="*100)
    print("DETAILED SCHEMA AUDIT BY FORM TYPE")
    print("="*100)

    for form_type, years in all_findings.items():
        print(f"\n{'='*100}")
        print(f"FORM TYPE: {form_type}")
        print(f"{'='*100}")

        for year, findings in years.items():
            print(f"\n{year} Analysis:")
            print(f"  CSV Columns: {findings['csv_cols']}")
            print(f"  DB Columns:  {findings['db_cols']}")
            print(f"  Coverage:    {findings['coverage']}%")

            critical = findings['missing']['critical']
            important = findings['missing']['important']
            minor = findings['missing']['minor']

            if critical:
                print(f"\n  [CRITICAL] Missing {len(critical)} CRITICAL columns for grant research:")
                for col in critical[:10]:  # Show first 10
                    print(f"    - {col}")
                if len(critical) > 10:
                    print(f"    ... and {len(critical) - 10} more")

            if important:
                print(f"\n  [IMPORTANT] Missing {len(important)} important columns:")
                for col in important[:5]:  # Show first 5
                    print(f"    - {col}")
                if len(important) > 5:
                    print(f"    ... and {len(important) - 5} more")

            if minor:
                print(f"\n  [MINOR] Missing {len(minor)} minor columns")

            if findings['extra']:
                print(f"\n  [INFO] Database has {len(findings['extra'])} extra columns not in CSV")

    # Generate summary report
    print("\n" + "="*100)
    print("SUMMARY REPORT - DATA QUALITY & COMPLETENESS")
    print("="*100)

    # Coverage summary
    print("\nData Coverage by Form Type:")
    for form_type, years in all_findings.items():
        avg_coverage = sum(y['coverage'] for y in years.values()) / len(years) if years else 0
        print(f"  {form_type:10} Average Coverage: {avg_coverage:.1f}%")

    # Missing data summary
    print("\nCritical Missing Fields Summary:")
    total_critical = 0
    for form_type, years in all_findings.items():
        critical_count = sum(len(y['missing']['critical']) for y in years.values())
        if critical_count > 0:
            total_critical += critical_count
            print(f"  {form_type:10} {critical_count} critical fields missing")

    # Data completeness by year
    print("\nData Completeness by Year:")
    print("  Form 990:")
    for year in [2022, 2023, 2024]:
        count = db_records['form_990'].get(year, 0)
        status = "[MISSING]" if count == 0 else f"{count:,} records"
        print(f"    {year}: {status}")

    print("  Form 990-PF:")
    for year in [2022, 2023, 2024]:
        count = db_records['form_990pf'].get(year, 0)
        status = "[MISSING]" if count == 0 else f"{count:,} records"
        print(f"    {year}: {status}")

    print("  Form 990-EZ:")
    for year in [2022, 2023, 2024]:
        count = db_records['form_990ez'].get(year, 0)
        status = "[MISSING]" if count == 0 else f"{count:,} records"
        print(f"    {year}: {status}")

    # Final recommendations
    print("\n" + "="*100)
    print("RECOMMENDATIONS")
    print("="*100)

    if total_critical > 0:
        print(f"\n[CRITICAL] Found {total_critical} critical missing fields across all forms")
        print("  -> RECOMMENDATION: Update database schema to include critical fields")

    missing_years = []
    if db_records['form_990'].get(2023, 0) == 0:
        missing_years.append("Form 990 (2023)")
    if db_records['form_990pf'].get(2024, 0) == 0:
        missing_years.append("Form 990-PF (2024)")
    if db_records['form_990ez'].get(2022, 0) == 0:
        missing_years.append("Form 990-EZ (2022)")

    if missing_years:
        print(f"\n[DATA GAPS] Missing data for:")
        for item in missing_years:
            print(f"  - {item}")
        print("  -> RECOMMENDATION: Ingest missing year data")

    print("\n[ACTION REQUIRED]")
    print("  1. Update database schema to add critical missing fields")
    print("  2. Migrate existing data to new schema")
    print("  3. Ingest missing year data with complete field coverage")
    print("  4. Create backup before schema changes")

    print("\n" + "="*100)
    print("AUDIT COMPLETE")
    print("="*100)

if __name__ == "__main__":
    main()
