"""
Complete Database Schema Update - Add All Missing Fields
Updates schema to include 92 critical missing fields across all tables
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = "data/nonprofit_intelligence.db"

# Missing columns to add to each table
FORM_990_MISSING_COLS = """
    -- Additional critical 990 fields
    grantoofficercd TEXT,
    grsrcptspublicuse INTEGER,

    -- Additional assets and liabilities
    capitalstktrstend INTEGER,
    paidinsurplusend INTEGER,
    retainedearnend INTEGER,

    -- Additional operational indicators
    actonbehalfcd TEXT,
    ceaseoperationscd TEXT,
    compltschocd TEXT,
    conduct5percentcd TEXT,
    dirbusnreltdcd TEXT,
    distribtodonorcd TEXT,
    engageexcessbnftcd TEXT,
    excbushldngscd TEXT,
    exceeds1pct509 INTEGER,
    exceeds2pct170 INTEGER,
    f1096cnt INTEGER,
    filedf720cd TEXT,
    filedlieuf1041cd TEXT,
    filerqrdrtnscd TEXT,
    fmlybusnreltdcd TEXT,
    frgnaggragrntscd TEXT,
    fw2gcnt INTEGER,

    -- Sales and cost basis
    cstbasisecur INTEGER,
    cstbasisothr INTEGER,
    grsalesecur INTEGER,
    grsalesothr INTEGER,
    gnlsecur INTEGER,
    gnlsothr INTEGER,
    lesscstofgoods INTEGER,
    lessdirfndrsng INTEGER,
    lessdirgaming INTEGER,

    -- Income details
    grsincmembers INTEGER,
    grsincother INTEGER,
    grsinc170 INTEGER,
    grsinc509 INTEGER,
    grsrcptsrelated170 INTEGER,

    -- Support calculations
    grsrcptspublicuse INTEGER,
    netincunrelatd509 INTEGER,
    netincunreltd170 INTEGER,
    othrinc170 INTEGER,
    othrinc509 INTEGER,
    pubsupplesspct170 REAL,
    pubsupplesub509 INTEGER,
    rcvdfrmdisqualsub509 INTEGER,
    samepubsuppsubtot170 INTEGER,
    samepubsuppsubtot509 INTEGER,
    srvcsval170 INTEGER,
    subtotpub509 INTEGER,
    subtotsuppinc509 INTEGER,
    txrevnuelevied170 INTEGER,

    -- Hospitals and healthcare
    hospaudfinstmtcd TEXT,
    inclinfinstmtcd TEXT,
    qualhlthonhnd INTEGER,
    qualhlthplncd TEXT,
    qualhlthreqmntn INTEGER,

    -- Excess benefit transactions
    awarexcessbnftcd TEXT,
    s4966distribcd TEXT,

    -- Investment and transaction codes
    intincntrlcd TEXT,
    invstproceedscd TEXT,
    loantofficercd TEXT,
    maintescrwaccntcd TEXT,

    -- Miscellaneous revenue
    miscrev11acd TEXT,
    miscrev11bcd TEXT,
    miscrev11ccd TEXT,
    miscrevtota INTEGER,
    miscrevtot11b INTEGER,
    miscrevtot11c INTEGER,
    miscrevtot11d INTEGER,
    miscrevtot11e INTEGER,

    -- Employee information
    noemplyeesw3cnt INTEGER,

    -- Organization structure
    orgtrnsfrcd TEXT,
    ownsepentcd TEXT,

    -- Related organization
    reltdorgcd TEXT,
    rcvdpdtngcd TEXT,
    recvartcd TEXT,
    recvnoncashcd TEXT,

    -- Rental details
    rntlexpnsreal INTEGER,
    rntlexpnsprsnl INTEGER,
    rntlincreal INTEGER,
    rntlincprsnl INTEGER,

    -- Investment reporting
    rptinvstothsecd TEXT,
    rptinvstprgrelcd TEXT,
    rptlndbldgeqptcd TEXT,
    rptothasstcd TEXT,
    rptothliabcd TEXT,

    -- Compensation reporting
    rptyestocompnstncd TEXT,

    -- Separate statements
    sepcnsldtfinstmtcd TEXT,
    sepindaudfinstmtcd TEXT,
    servasofficercd TEXT,
    sellorexchcd TEXT,

    -- Additional codes
    subjto6033cd TEXT,
    txexmptint INTEGER,
    wthldngrulescd TEXT
"""

FORM_990PF_MISSING_COLS = """
    -- Multi-year adjusted net income (CRITICAL)
    adjnetinccola INTEGER,
    adjnetinccolb INTEGER,
    adjnetinccolc INTEGER,
    adjnetinccold INTEGER,
    adjnetinctot INTEGER,

    -- Endowment tracking (CRITICAL)
    endwmntscola INTEGER,
    endwmntscolb INTEGER,
    endwmntscolc INTEGER,
    endwmntscold INTEGER,
    endwmntstot INTEGER,

    -- Qualifying assets (CRITICAL)
    qlfyasseta INTEGER,
    qlfyassetb INTEGER,
    qlfyassetc INTEGER,
    qlfyassetd INTEGER,
    qlfyassettot INTEGER,

    -- Extended program services D-G (CRITICAL)
    progsrvcdcold INTEGER,
    progsrvcdcole INTEGER,
    progsrvcecold INTEGER,
    progsrvcecole INTEGER,
    progsrvcfcold INTEGER,
    progsrvcfcole INTEGER,
    progsrvcgcold INTEGER,
    progsrvcgcole INTEGER,

    -- Compliance indicators (CRITICAL)
    excessrcpts INTEGER,
    excptransind TEXT,
    s4960_tx_pymt_cd TEXT
"""

FORM_990EZ_MISSING_COLS = """
    -- Additional support calculations (CRITICAL)
    totsupport INTEGER,
    totsupport170 INTEGER,

    -- Additional operational fields
    actvtynotprevrptcd TEXT,
    chngsinorgcd TEXT,
    contractioncd TEXT,
    excds1pct509 INTEGER,
    excds2pct170 INTEGER,
    filedf1120polcd TEXT,
    loanstoofficers INTEGER,
    loanstoofficerscd TEXT,
    networthend INTEGER,
    politicalexpend INTEGER,
    prohibtdtxshltrcd TEXT,
    pubsupplesspct170 REAL,
    pubsupplesssub509 INTEGER,
    pubsuppsubtot170 INTEGER,
    pubsuppsubtot509 INTEGER,
    rcvdfrmdisqualsub509 INTEGER,
    s4958excessbenefcd TEXT,
    samepubsuppsubtot170 INTEGER,
    samepubsuppsubtot509 INTEGER,
    subtotpub509 INTEGER,
    totnoforgscnt INTEGER,
    unreltxincls511tx509 INTEGER,

    -- Additional income/revenue
    grsrcptsactvts509 INTEGER,
    netincunrelatd170 INTEGER,
    netincunreltd509 INTEGER,
    othrinc170 INTEGER,
    othrinc509 INTEGER
"""

BMF_MISSING_COLS = """
    -- Critical BMF classification fields
    ntee_cd TEXT,
    foundation TEXT,
    organization TEXT,

    -- Additional administrative fields
    activity INTEGER,
    affiliation INTEGER,
    deductibility INTEGER,
    filing_req_cd TEXT,
    group_code INTEGER,
    pf_filing_req_cd TEXT,
    status TEXT
"""


def add_columns_to_table(cursor, table_name: str, columns_sql: str):
    """Add multiple columns to a table"""
    print(f"\nUpdating {table_name}...")

    # Parse column definitions
    lines = [line.strip() for line in columns_sql.strip().split('\n') if line.strip() and not line.strip().startswith('--')]

    added_count = 0
    skipped_count = 0

    for line in lines:
        if not line or line.startswith('--'):
            continue

        # Extract column name and type
        parts = line.rstrip(',').split()
        if len(parts) >= 2:
            col_name = parts[0]
            col_type = ' '.join(parts[1:])

            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                added_count += 1
                print(f"  [+] Added: {col_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    skipped_count += 1
                    print(f"  [=] Exists: {col_name}")
                else:
                    print(f"  [X] Error adding {col_name}: {e}")

    print(f"  Summary: {added_count} added, {skipped_count} already exist")
    return added_count, skipped_count


def verify_schema_updates(cursor):
    """Verify all columns were added successfully"""
    print("\n" + "="*80)
    print("SCHEMA UPDATE VERIFICATION")
    print("="*80)

    tables = {
        'form_990': 246,  # Expected total columns after update
        'form_990pf': 181,  # Expected total
        'form_990ez': 100,  # Expected total
        'bmf_organizations': 37  # Expected total
    }

    all_good = True
    for table, expected_cols in tables.items():
        cursor.execute(f'PRAGMA table_info({table})')
        actual_cols = len(cursor.fetchall())

        status = "[OK]" if actual_cols >= expected_cols else "[!!]"
        print(f"{status} {table:25} {actual_cols} columns (expected ~{expected_cols})")

        if actual_cols < expected_cols:
            all_good = False

    return all_good


def main():
    print("="*80)
    print("DATABASE SCHEMA UPDATE - ADD ALL MISSING FIELDS")
    print("="*80)
    print(f"Database: {DATABASE_PATH}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not os.path.exists(DATABASE_PATH):
        print(f"\n[ERROR] Database not found at {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Update each table
        total_added = 0

        # Form 990
        added, skipped = add_columns_to_table(cursor, 'form_990', FORM_990_MISSING_COLS)
        total_added += added

        # Form 990-PF
        added, skipped = add_columns_to_table(cursor, 'form_990pf', FORM_990PF_MISSING_COLS)
        total_added += added

        # Form 990-EZ
        added, skipped = add_columns_to_table(cursor, 'form_990ez', FORM_990EZ_MISSING_COLS)
        total_added += added

        # BMF Organizations
        added, skipped = add_columns_to_table(cursor, 'bmf_organizations', BMF_MISSING_COLS)
        total_added += added

        # Commit changes
        conn.commit()
        print(f"\n[OK] Changes committed to database")

        # Verify updates
        success = verify_schema_updates(cursor)

        # Summary
        print("\n" + "="*80)
        print("UPDATE COMPLETE")
        print("="*80)
        print(f"Total columns added: {total_added}")
        print(f"Status: {'SUCCESS' if success else 'PARTIAL - Some columns missing'}")

        if success:
            print("\n[SUCCESS] Database schema updated successfully!")
            print("  Ready for Phase 3: Data migration")
        else:
            print("\n[WARNING] Some expected columns may be missing")
            print("  Review output above for details")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
