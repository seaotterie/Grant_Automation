"""
BMF/SOI ETL Pipeline - Nonprofit Financial Intelligence Database
Created: September 10, 2025

This module processes IRS Business Master File (BMF) and Statistics of Income (SOI) 
CSV files into a comprehensive SQLite database for advanced grant research intelligence.

Capabilities:
- Multi-year SOI data processing (2022-2024)
- Multiple form types (990, 990-PF, 990-EZ) 
- Multi-state BMF data integration
- Data validation and quality reporting
- Performance optimization and indexing
"""

import sqlite3
import pandas as pd
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BMFSOIETLProcessor:
    """
    Comprehensive ETL processor for BMF and SOI data integration.
    
    This class handles the extraction, transformation, and loading of multiple
    data sources into a unified nonprofit intelligence database.
    """
    
    def __init__(self, database_path: str = "data/nonprofit_intelligence.db"):
        """
        Initialize the ETL processor.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.schema_path = "src/database/bmf_soi_schema.sql"
        self.soi_files_dir = "SOI_Files"
        
        # Data quality tracking
        self.import_stats = {
            'bmf_records': 0,
            'form_990_records': 0,
            'form_990pf_records': 0,
            'form_990ez_records': 0,
            'total_errors': 0,
            'processing_time': 0
        }
        
        # File mapping configuration
        self.file_patterns = {
            'bmf': ['eo_va.csv', 'eo2.csv'],  # BMF files
            '990': ['22eoextract990.csv', '23eoextract990.csv', '24eoextract990.csv'],
            '990pf': ['22eoextract990pf.csv', '23eoextract990pf.csv', '24eoextract990pf.csv'],
            '990ez': []  # Will auto-detect EZ files
        }
        
    def create_database_schema(self):
        """Create the database schema from SQL file."""
        try:
            logger.info("Creating database schema...")
            
            # Ensure database directory exists
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            
            # Read schema file
            with open(self.schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation
            with sqlite3.connect(self.database_path) as conn:
                # Enable foreign key support
                conn.execute("PRAGMA foreign_keys = ON")
                conn.executescript(schema_sql)
                conn.commit()
            
            logger.info(f"Database schema created successfully at {self.database_path}")
            
        except Exception as e:
            logger.error(f"Error creating database schema: {e}")
            raise
    
    def detect_soi_files(self) -> Dict[str, List[str]]:
        """
        Auto-detect SOI CSV files in the SOI_Files directory.
        
        Returns:
            Dictionary mapping file types to file paths
        """
        files = {
            'bmf': [],
            '990': [],
            '990pf': [],
            '990ez': []
        }
        
        if not os.path.exists(self.soi_files_dir):
            logger.warning(f"SOI files directory not found: {self.soi_files_dir}")
            return files
        
        # Scan for files
        for filename in os.listdir(self.soi_files_dir):
            if not filename.endswith('.csv'):
                continue
                
            filepath = os.path.join(self.soi_files_dir, filename)
            
            # Classify file type
            filename_lower = filename.lower()
            
            if any(bmf_pattern in filename_lower for bmf_pattern in ['eo_va', 'eo2', 'eo3', 'eo4']):
                files['bmf'].append(filepath)
            elif '990pf' in filename_lower or 'pf' in filename_lower:
                files['990pf'].append(filepath)
            elif '990ez' in filename_lower or 'ez' in filename_lower:
                files['990ez'].append(filepath)
            elif '990' in filename_lower:
                files['990'].append(filepath)
        
        # Log discovered files
        for file_type, file_list in files.items():
            logger.info(f"Found {len(file_list)} {file_type.upper()} files: {[os.path.basename(f) for f in file_list]}")
        
        return files
    
    def clean_numeric_value(self, value) -> Optional[int]:
        """
        Clean and convert numeric values handling various formats.
        
        Args:
            value: Raw value from CSV
            
        Returns:
            Integer value or None if invalid
        """
        if pd.isna(value) or value == '' or value == '0':
            return None
        
        try:
            # Handle string values
            if isinstance(value, str):
                # Remove commas and whitespace
                value = value.replace(',', '').strip()
                if value == '' or value == '0':
                    return None
            
            # Convert to integer
            numeric_value = int(float(value))
            return numeric_value if numeric_value != 0 else None
            
        except (ValueError, TypeError):
            return None
    
    def clean_text_value(self, value) -> Optional[str]:
        """
        Clean text values handling nulls and empty strings.
        
        Args:
            value: Raw value from CSV
            
        Returns:
            Clean string value or None if empty
        """
        if pd.isna(value) or value == '':
            return None
            
        text_value = str(value).strip()
        return text_value if text_value else None
    
    def process_bmf_data(self, file_paths: List[str]):
        """
        Process BMF (Business Master File) data.
        
        Args:
            file_paths: List of BMF CSV file paths
        """
        logger.info("Processing BMF data...")
        
        with sqlite3.connect(self.database_path) as conn:
            total_processed = 0
            
            for file_path in file_paths:
                logger.info(f"Processing BMF file: {os.path.basename(file_path)}")
                
                try:
                    # Read CSV with error handling
                    df = pd.read_csv(file_path, dtype=str, encoding='utf-8')
                    logger.info(f"Loaded {len(df)} records from {os.path.basename(file_path)}")
                    
                    # Clean and prepare data
                    processed_records = []
                    
                    for _, row in df.iterrows():
                        try:
                            # Clean core fields
                            ein = self.clean_text_value(row.get('EIN'))
                            name = self.clean_text_value(row.get('NAME'))
                            
                            if not ein or not name:
                                continue  # Skip invalid records
                            
                            # Build record
                            record = {
                                'ein': ein,
                                'name': name,
                                'ico': self.clean_text_value(row.get('ICO')),
                                'street': self.clean_text_value(row.get('STREET')),
                                'city': self.clean_text_value(row.get('CITY')),
                                'state': self.clean_text_value(row.get('STATE')),
                                'zip': self.clean_text_value(row.get('ZIP')),
                                'ntee_code': self.clean_text_value(row.get('NTEE_CD')),
                                'subsection': self.clean_text_value(row.get('SUBSECTION')),
                                'classification': self.clean_text_value(row.get('CLASSIFICATION')),
                                'foundation_code': self.clean_text_value(row.get('FOUNDATION')),
                                'organization_code': self.clean_text_value(row.get('ORGANIZATION')),
                                'asset_cd': self.clean_text_value(row.get('ASSET_CD')),
                                'income_cd': self.clean_text_value(row.get('INCOME_CD')),
                                'asset_amt': self.clean_numeric_value(row.get('ASSET_AMT')),
                                'income_amt': self.clean_numeric_value(row.get('INCOME_AMT')),
                                'revenue_amt': self.clean_numeric_value(row.get('REVENUE_AMT')),
                                'ruling_date': self.clean_text_value(row.get('RULING')),
                                'tax_period': self.clean_text_value(row.get('TAX_PERIOD')),
                                'accounting_period': self.clean_text_value(row.get('ACCT_PD')),
                                'sort_name': self.clean_text_value(row.get('SORT_NAME'))
                            }
                            
                            processed_records.append(record)
                            
                        except Exception as e:
                            logger.warning(f"Error processing BMF record: {e}")
                            self.import_stats['total_errors'] += 1
                            continue
                    
                    # Batch insert using executemany to avoid SQL variables limit
                    if processed_records:
                        # Create INSERT statement
                        columns = list(processed_records[0].keys())
                        placeholders = ', '.join(['?' for _ in columns])
                        insert_sql = f"INSERT OR IGNORE INTO bmf_organizations ({', '.join(columns)}) VALUES ({placeholders})"
                        
                        # Convert records to tuples
                        record_tuples = [tuple(record[col] for col in columns) for record in processed_records]
                        
                        # Execute in smaller batches to avoid memory issues
                        batch_size = 1000
                        for i in range(0, len(record_tuples), batch_size):
                            batch = record_tuples[i:i+batch_size]
                            conn.executemany(insert_sql, batch)
                        conn.commit()
                        
                        processed_count = len(processed_records)
                        total_processed += processed_count
                        logger.info(f"Inserted {processed_count} BMF records from {os.path.basename(file_path)}")
                    
                except Exception as e:
                    logger.error(f"Error processing BMF file {file_path}: {e}")
                    self.import_stats['total_errors'] += 1
            
            self.import_stats['bmf_records'] = total_processed
            logger.info(f"BMF processing complete. Total records: {total_processed}")
    
    def process_990_data(self, file_paths: List[str]):
        """
        Process Form 990 data (large nonprofits).
        
        Args:
            file_paths: List of 990 CSV file paths
        """
        logger.info("Processing Form 990 data...")
        
        with sqlite3.connect(self.database_path) as conn:
            total_processed = 0
            
            for file_path in file_paths:
                logger.info(f"Processing 990 file: {os.path.basename(file_path)}")
                
                try:
                    # Extract tax year from filename
                    filename = os.path.basename(file_path)
                    tax_year = None
                    if '22eo' in filename:
                        tax_year = 2022
                    elif '23eo' in filename:
                        tax_year = 2023
                    elif '24eo' in filename:
                        tax_year = 2024
                    
                    if not tax_year:
                        logger.warning(f"Could not determine tax year for {filename}")
                        continue
                    
                    # Read CSV in chunks for large files
                    chunk_size = 10000
                    chunk_count = 0
                    
                    for chunk in pd.read_csv(file_path, dtype=str, encoding='utf-8', chunksize=chunk_size):
                        chunk_count += 1
                        logger.info(f"Processing chunk {chunk_count} ({len(chunk)} records)")
                        
                        # Clean and prepare data
                        processed_records = []
                        
                        for _, row in chunk.iterrows():
                            try:
                                # Clean core fields
                                ein = self.clean_text_value(row.get('EIN'))
                                if not ein:
                                    continue  # Skip invalid records
                                
                                # Build record with comprehensive field mapping
                                record = {
                                    'ein': ein,
                                    'tax_year': tax_year,
                                    'tax_pd': self.clean_numeric_value(row.get('tax_pd')),
                                    'efile': self.clean_text_value(row.get('efile')),
                                    'subseccd': self.clean_numeric_value(row.get('subseccd')),
                                    
                                    # Core financial data
                                    'totrevenue': self.clean_numeric_value(row.get('totrevenue')),
                                    'totcntrbgfts': self.clean_numeric_value(row.get('totcntrbgfts')),
                                    'prgmservrevnue': self.clean_numeric_value(row.get('totprgmrevnue')),
                                    'totfuncexpns': self.clean_numeric_value(row.get('totfuncexpns')),
                                    'totassetsend': self.clean_numeric_value(row.get('totassetsend')),
                                    'totliabend': self.clean_numeric_value(row.get('totliabend')),
                                    'totnetassetend': self.clean_numeric_value(row.get('totnetassetend')),
                                    
                                    # Revenue breakdown
                                    'invstmntinc': self.clean_numeric_value(row.get('invstmntinc')),
                                    'txexmptbndsproceeds': self.clean_numeric_value(row.get('txexmptbndsproceeds')),
                                    'royaltsinc': self.clean_numeric_value(row.get('royaltsinc')),
                                    'grsrntsreal': self.clean_numeric_value(row.get('grsrntsreal')),
                                    'grsrntsprsnl': self.clean_numeric_value(row.get('grsrntsprsnl')),
                                    'netrntlinc': self.clean_numeric_value(row.get('netrntlinc')),
                                    'netgnls': self.clean_numeric_value(row.get('netgnls')),
                                    'grsincfndrsng': self.clean_numeric_value(row.get('grsincfndrsng')),
                                    'netincfndrsng': self.clean_numeric_value(row.get('netincfndrsng')),
                                    'grsincgaming': self.clean_numeric_value(row.get('grsincgaming')),
                                    'netincgaming': self.clean_numeric_value(row.get('netincgaming')),
                                    'grsalesinvent': self.clean_numeric_value(row.get('grsalesinvent')),
                                    'netincsales': self.clean_numeric_value(row.get('netincsales')),
                                    
                                    # Program service revenue
                                    'prgmservcode2acd': self.clean_text_value(row.get('prgmservcode2acd')),
                                    'totrev2acola': self.clean_numeric_value(row.get('totrev2acola')),
                                    'prgmservcode2bcd': self.clean_text_value(row.get('prgmservcode2bcd')),
                                    'totrev2bcola': self.clean_numeric_value(row.get('totrev2bcola')),
                                    'prgmservcode2ccd': self.clean_text_value(row.get('prgmservcode2ccd')),
                                    'totrev2ccola': self.clean_numeric_value(row.get('totrev2ccola')),
                                    'prgmservcode2dcd': self.clean_text_value(row.get('prgmservcode2dcd')),
                                    'totrev2dcola': self.clean_numeric_value(row.get('totrev2dcola')),
                                    'prgmservcode2ecd': self.clean_text_value(row.get('prgmservcode2ecd')),
                                    'totrev2ecola': self.clean_numeric_value(row.get('totrev2ecola')),
                                    'totrev2fcola': self.clean_numeric_value(row.get('totrev2fcola')),
                                    
                                    # Expense breakdown
                                    'grntstogovt': self.clean_numeric_value(row.get('grntstogovt')),
                                    'grnsttoindiv': self.clean_numeric_value(row.get('grnsttoindiv')),
                                    'grntstofrgngovt': self.clean_numeric_value(row.get('grntstofrgngovt')),
                                    'benifitsmembrs': self.clean_numeric_value(row.get('benifitsmembrs')),
                                    'compnsatncurrofcr': self.clean_numeric_value(row.get('compnsatncurrofcr')),
                                    'compnsatnandothr': self.clean_numeric_value(row.get('compnsatnandothr')),
                                    'othrsalwages': self.clean_numeric_value(row.get('othrsalwages')),
                                    'pensionplancontrb': self.clean_numeric_value(row.get('pensionplancontrb')),
                                    'othremplyeebenef': self.clean_numeric_value(row.get('othremplyeebenef')),
                                    'payrolltx': self.clean_numeric_value(row.get('payrolltx')),
                                    'feesforsrvcmgmt': self.clean_numeric_value(row.get('feesforsrvcmgmt')),
                                    'legalfees': self.clean_numeric_value(row.get('legalfees')),
                                    'accntingfees': self.clean_numeric_value(row.get('accntingfees')),
                                    'feesforsrvclobby': self.clean_numeric_value(row.get('feesforsrvclobby')),
                                    'profndraising': self.clean_numeric_value(row.get('profndraising')),
                                    'feesforsrvcinvstmgmt': self.clean_numeric_value(row.get('feesforsrvcinvstmgmt')),
                                    'feesforsrvcothr': self.clean_numeric_value(row.get('feesforsrvcothr')),
                                    'advrtpromo': self.clean_numeric_value(row.get('advrtpromo')),
                                    'officexpns': self.clean_numeric_value(row.get('officexpns')),
                                    'infotech': self.clean_numeric_value(row.get('infotech')),
                                    'royaltsexpns': self.clean_numeric_value(row.get('royaltsexpns')),
                                    'occupancy': self.clean_numeric_value(row.get('occupancy')),
                                    'travel': self.clean_numeric_value(row.get('travel')),
                                    'travelofpublicoffcl': self.clean_numeric_value(row.get('travelofpublicoffcl')),
                                    'converconventmtng': self.clean_numeric_value(row.get('converconventmtng')),
                                    'interestamt': self.clean_numeric_value(row.get('interestamt')),
                                    'pymtoaffiliates': self.clean_numeric_value(row.get('pymtoaffiliates')),
                                    'deprcatndepletn': self.clean_numeric_value(row.get('deprcatndepletn')),
                                    'insurance': self.clean_numeric_value(row.get('insurance')),
                                    
                                    # Assets
                                    'nonintcashend': self.clean_numeric_value(row.get('nonintcashend')),
                                    'svngstempinvend': self.clean_numeric_value(row.get('svngstempinvend')),
                                    'pldgegrntrcvblend': self.clean_numeric_value(row.get('pldgegrntrcvblend')),
                                    'accntsrcvblend': self.clean_numeric_value(row.get('accntsrcvblend')),
                                    'lndbldgsequipend': self.clean_numeric_value(row.get('lndbldgsequipend')),
                                    'invstmntsend': self.clean_numeric_value(row.get('invstmntsend')),
                                    'invstmntsothrend': self.clean_numeric_value(row.get('invstmntsothrend')),
                                    'invstmntsprgmend': self.clean_numeric_value(row.get('invstmntsprgmend')),
                                    
                                    # Operational indicators
                                    's501c3or4947a1cd': self.clean_text_value(row.get('s501c3or4947a1cd')),
                                    'schdbind': self.clean_text_value(row.get('schdbind')),
                                    'politicalactvtscd': self.clean_text_value(row.get('politicalactvtscd')),
                                    'lbbyingactvtscd': self.clean_text_value(row.get('lbbyingactvtscd')),
                                    'operateschools170cd': self.clean_text_value(row.get('operateschools170cd')),
                                    'operatehosptlcd': self.clean_text_value(row.get('operatehosptlcd')),
                                    'frgnofficecd': self.clean_text_value(row.get('frgnofficecd')),
                                    'frgnrevexpnscd': self.clean_text_value(row.get('frgnrevexpnscd')),
                                    'frgngrntscd': self.clean_text_value(row.get('frgngrntscd')),
                                    'rptgrntstogovtcd': self.clean_text_value(row.get('rptgrntstogovtcd')),
                                    'rptgrntstoindvcd': self.clean_text_value(row.get('rptgrntstoindvcd')),
                                    'rptprofndrsngfeescd': self.clean_text_value(row.get('rptprofndrsngfeescd')),
                                    'rptincfnndrsngcd': self.clean_text_value(row.get('rptincfnndrsngcd')),
                                    'rptincgamingcd': self.clean_text_value(row.get('rptincgamingcd')),
                                    'txexmptbndcd': self.clean_text_value(row.get('txexmptbndcd')),
                                    'dnradvisedfundscd': self.clean_text_value(row.get('dnradvisedfundscd')),
                                    'prptyintrcvdcd': self.clean_text_value(row.get('prptyintrcvdcd')),
                                    'maintwrkofartcd': self.clean_text_value(row.get('maintwrkofartcd')),
                                    'crcounselingqstncd': self.clean_text_value(row.get('crcounselingqstncd')),
                                    'hldassetsintermpermcd': self.clean_text_value(row.get('hldassetsintermpermcd')),
                                    
                                    # Compensation
                                    'totreprtabled': self.clean_numeric_value(row.get('totreprtabled')),
                                    'totcomprelatede': self.clean_numeric_value(row.get('totcomprelatede')),
                                    'totestcompf': self.clean_numeric_value(row.get('totestcompf')),
                                    'noindiv100kcnt': self.clean_numeric_value(row.get('noindiv100kcnt')),
                                    'nocontractor100kcnt': self.clean_numeric_value(row.get('nocontractor100kcnt')),
                                    
                                    # Public support
                                    'nonpfrea': self.clean_text_value(row.get('nonpfrea')),
                                    'totnooforgscnt': self.clean_numeric_value(row.get('totnooforgscnt')),
                                    'totsupport': self.clean_numeric_value(row.get('totsupport')),
                                    'gftgrntsrcvd170': self.clean_numeric_value(row.get('gftgrntsrcvd170')),
                                    'totsupp170': self.clean_numeric_value(row.get('totsupp170')),
                                    'totgftgrntrcvd509': self.clean_numeric_value(row.get('totgftgrntrcvd509')),
                                    'totsupp509': self.clean_numeric_value(row.get('totsupp509')),
                                    
                                    # Filing indicators
                                    'unrelbusinccd': self.clean_text_value(row.get('unrelbusinccd')),
                                    'filedf990tcd': self.clean_text_value(row.get('filedf990tcd')),
                                    'frgnacctcd': self.clean_text_value(row.get('frgnacctcd')),
                                    'prohibtdtxshltrcd': self.clean_text_value(row.get('prohibtdtxshltrcd')),
                                    'solicitcntrbcd': self.clean_text_value(row.get('solicitcntrbcd')),
                                    'exprstmntcd': self.clean_text_value(row.get('exprstmntcd')),
                                    'providegoodscd': self.clean_text_value(row.get('providegoodscd')),
                                    'notfydnrvalcd': self.clean_text_value(row.get('notfydnrvalcd')),
                                    'filedf8282cd': self.clean_text_value(row.get('filedf8282cd')),
                                    'f8282cnt': self.clean_numeric_value(row.get('f8282cnt')),
                                    'fndsrcvdcd': self.clean_text_value(row.get('fndsrcvdcd')),
                                    'premiumspaidcd': self.clean_text_value(row.get('premiumspaidcd')),
                                    'filedf8899cd': self.clean_text_value(row.get('filedf8899cd')),
                                    'filedf1098ccd': self.clean_text_value(row.get('filedf1098ccd'))
                                }
                                
                                processed_records.append(record)
                                
                            except Exception as e:
                                logger.warning(f"Error processing 990 record: {e}")
                                self.import_stats['total_errors'] += 1
                                continue
                        
                        # Batch insert using executemany
                        if processed_records:
                            # Create INSERT statement
                            columns = list(processed_records[0].keys())
                            placeholders = ', '.join(['?' for _ in columns])
                            insert_sql = f"INSERT OR IGNORE INTO form_990 ({', '.join(columns)}) VALUES ({placeholders})"
                            
                            # Convert records to tuples
                            record_tuples = [tuple(record[col] for col in columns) for record in processed_records]
                            
                            # Execute in smaller batches
                            batch_size = 500  # Smaller batches for tables with many columns
                            for i in range(0, len(record_tuples), batch_size):
                                batch = record_tuples[i:i+batch_size]
                                conn.executemany(insert_sql, batch)
                            conn.commit()
                            
                            processed_count = len(processed_records)
                            total_processed += processed_count
                            logger.info(f"Inserted {processed_count} Form 990 records from chunk {chunk_count}")
                
                except Exception as e:
                    logger.error(f"Error processing 990 file {file_path}: {e}")
                    self.import_stats['total_errors'] += 1
            
            self.import_stats['form_990_records'] = total_processed
            logger.info(f"Form 990 processing complete. Total records: {total_processed}")
    
    def process_990pf_data(self, file_paths: List[str]):
        """
        Process Form 990-PF data (private foundations).
        
        Args:
            file_paths: List of 990-PF CSV file paths
        """
        logger.info("Processing Form 990-PF data...")
        
        with sqlite3.connect(self.database_path) as conn:
            total_processed = 0
            
            for file_path in file_paths:
                logger.info(f"Processing 990-PF file: {os.path.basename(file_path)}")
                
                try:
                    # Extract tax year from filename
                    filename = os.path.basename(file_path)
                    tax_year = None
                    if '22eo' in filename:
                        tax_year = 2022
                    elif '23eo' in filename:
                        tax_year = 2023
                    elif '24eo' in filename:
                        tax_year = 2024
                    
                    if not tax_year:
                        logger.warning(f"Could not determine tax year for {filename}")
                        continue
                    
                    # Read CSV
                    df = pd.read_csv(file_path, dtype=str, encoding='utf-8')
                    logger.info(f"Loaded {len(df)} 990-PF records from {os.path.basename(file_path)}")
                    
                    # Clean and prepare data
                    processed_records = []
                    
                    for _, row in df.iterrows():
                        try:
                            # Clean core fields
                            ein = self.clean_text_value(row.get('EIN'))
                            if not ein:
                                continue
                            
                            # Build 990-PF record (foundation-specific fields)
                            record = {
                                'ein': ein,
                                'tax_year': tax_year,
                                'tax_prd': self.clean_numeric_value(row.get('TAX_PRD')),
                                'elf': self.clean_text_value(row.get('ELF')),
                                'eostatus': self.clean_numeric_value(row.get('EOSTATUS')),
                                'operatingcd': self.clean_text_value(row.get('OPERATINGCD')),
                                'subcd': self.clean_numeric_value(row.get('SUBCD')),
                                
                                # Asset valuation
                                'fairmrktvalamt': self.clean_numeric_value(row.get('FAIRMRKTVALAMT')),
                                'fairmrktvaleoy': self.clean_numeric_value(row.get('FAIRMRKTVALEOY')),
                                'totassetsend': self.clean_numeric_value(row.get('TOTASSETSEND')),
                                
                                # Revenue
                                'grscontrgifts': self.clean_numeric_value(row.get('GRSCONTRGIFTS')),
                                'schedbind': self.clean_text_value(row.get('SCHEDBIND')),
                                'intrstrvnue': self.clean_numeric_value(row.get('INTRSTRVNUE')),
                                'dividndsamt': self.clean_numeric_value(row.get('DIVIDNDSAMT')),
                                'grsrents': self.clean_numeric_value(row.get('GRSRENTS')),
                                'otherincamt': self.clean_numeric_value(row.get('OTHERINCAMT')),
                                'totrcptperbks': self.clean_numeric_value(row.get('TOTRCPTPERBKS')),
                                
                                # Expenses
                                'compofficers': self.clean_numeric_value(row.get('COMPOFFICERS')),
                                'pensplemplbenf': self.clean_numeric_value(row.get('PENSPLEMPLBENF')),
                                'legalfeesamt': self.clean_numeric_value(row.get('LEGALFEESAMT')),
                                'accountingfees': self.clean_numeric_value(row.get('ACCOUNTINGFEES')),
                                'interestamt': self.clean_numeric_value(row.get('INTERESTAMT')),
                                'depreciationamt': self.clean_numeric_value(row.get('DEPRECIATIONAMT')),
                                'occupancyamt': self.clean_numeric_value(row.get('OCCUPANCYAMT')),
                                'travlconfmtngs': self.clean_numeric_value(row.get('TRAVLCONFMTNGS')),
                                
                                # Grant making (KEY FOUNDATION DATA)
                                'contrpdpbks': self.clean_numeric_value(row.get('CONTRPDPBKS')),
                                'totexpnspbks': self.clean_numeric_value(row.get('TOTEXPNSPBKS')),
                                'totexpnsexempt': self.clean_numeric_value(row.get('TOTEXPNSEXEMPT')),
                                
                                # Investment portfolio
                                'invstgovtoblig': self.clean_numeric_value(row.get('INVSTGOVTOBLIG')),
                                'invstcorpstk': self.clean_numeric_value(row.get('INVSTCORPSTK')),
                                'invstcorpbnd': self.clean_numeric_value(row.get('INVSTCORPBND')),
                                'totinvstsec': self.clean_numeric_value(row.get('TOTINVSTSEC')),
                                'mrtgloans': self.clean_numeric_value(row.get('MRTGLOANS')),
                                'othrinvstend': self.clean_numeric_value(row.get('OTHRINVSTEND')),
                                
                                # Financial position
                                'othrcashamt': self.clean_numeric_value(row.get('OTHRCASHAMT')),
                                'othrassetseoy': self.clean_numeric_value(row.get('OTHRASSETSEOY')),
                                'totliabend': self.clean_numeric_value(row.get('TOTLIABEND')),
                                'tfundnworth': self.clean_numeric_value(row.get('TFUNDNWORTH')),
                                
                                # Investment income
                                'netinvstinc': self.clean_numeric_value(row.get('NETINVSTINC')),
                                'adjnetinc': self.clean_numeric_value(row.get('ADJNETINC')),
                                
                                # Distribution requirements
                                'distribamt': self.clean_numeric_value(row.get('DISTRIBAMT')),
                                'undistribincyr': self.clean_numeric_value(row.get('UNDISTRIBINCYR')),
                                'cmpmininvstret': self.clean_numeric_value(row.get('CMPMININVSTRET')),
                                
                                # Future grants
                                'grntapprvfut': self.clean_numeric_value(row.get('GRNTAPPRVFUT')),
                                
                                # Qualifying distributions
                                'qlfydistriba': self.clean_numeric_value(row.get('QLFYDISTRIBA')),
                                'qlfydistribb': self.clean_numeric_value(row.get('QLFYDISTRIBB')),
                                'qlfydistribc': self.clean_numeric_value(row.get('QLFYDISTRIBC')),
                                'qlfydistribd': self.clean_numeric_value(row.get('QLFYDISTRIBD')),
                                'qlfydistribtot': self.clean_numeric_value(row.get('QLFYDISTRIBTOT')),
                                
                                # Taxes
                                'invstexcisetx': self.clean_numeric_value(row.get('INVSTEXCISETX')),
                                'sect511tx': self.clean_numeric_value(row.get('SECT511TX')),
                                'subtitleatx': self.clean_numeric_value(row.get('SUBTITLEATX')),
                                'totaxpyr': self.clean_numeric_value(row.get('TOTAXPYR')),
                                
                                # Compliance flags
                                'sec4940notxcd': self.clean_text_value(row.get('SEC4940NOTXCD')),
                                'sec4940redtxcd': self.clean_text_value(row.get('SEC4940REDTXCD')),
                                'filedf990tcd': self.clean_text_value(row.get('FILEDF990TCD')),
                                'grntindivcd': self.clean_text_value(row.get('GRNTINDIVCD')),
                                'nchrtygrntcd': self.clean_text_value(row.get('NCHRTYGRNTCD')),
                                'nreligiouscd': self.clean_text_value(row.get('NRELIGIOUSCD'))
                            }
                            
                            processed_records.append(record)
                            
                        except Exception as e:
                            logger.warning(f"Error processing 990-PF record: {e}")
                            self.import_stats['total_errors'] += 1
                            continue
                    
                    # Batch insert using executemany
                    if processed_records:
                        # Create INSERT statement
                        columns = list(processed_records[0].keys())
                        placeholders = ', '.join(['?' for _ in columns])
                        insert_sql = f"INSERT OR IGNORE INTO form_990pf ({', '.join(columns)}) VALUES ({placeholders})"
                        
                        # Convert records to tuples
                        record_tuples = [tuple(record[col] for col in columns) for record in processed_records]
                        
                        # Execute in smaller batches
                        batch_size = 500
                        for i in range(0, len(record_tuples), batch_size):
                            batch = record_tuples[i:i+batch_size]
                            conn.executemany(insert_sql, batch)
                        conn.commit()
                        
                        processed_count = len(processed_records)
                        total_processed += processed_count
                        logger.info(f"Inserted {processed_count} Form 990-PF records from {os.path.basename(file_path)}")
                
                except Exception as e:
                    logger.error(f"Error processing 990-PF file {file_path}: {e}")
                    self.import_stats['total_errors'] += 1
            
            self.import_stats['form_990pf_records'] = total_processed
            logger.info(f"Form 990-PF processing complete. Total records: {total_processed}")
    
    def process_990ez_data(self, file_paths: List[str]):
        """
        Process Form 990-EZ data (smaller nonprofits).
        
        Args:
            file_paths: List of 990-EZ CSV file paths
        """
        logger.info("Processing Form 990-EZ data...")
        
        with sqlite3.connect(self.database_path) as conn:
            total_processed = 0
            
            for file_path in file_paths:
                logger.info(f"Processing 990-EZ file: {os.path.basename(file_path)}")
                
                try:
                    # Extract tax year from filename
                    filename = os.path.basename(file_path)
                    tax_year = None
                    if '22eo' in filename:
                        tax_year = 2022
                    elif '23eo' in filename:
                        tax_year = 2023
                    elif '24eo' in filename:
                        tax_year = 2024
                    
                    if not tax_year:
                        logger.warning(f"Could not determine tax year for {filename}")
                        continue
                    
                    # Read CSV
                    df = pd.read_csv(file_path, dtype=str, encoding='utf-8')
                    logger.info(f"Loaded {len(df)} 990-EZ records from {os.path.basename(file_path)}")
                    
                    # Clean and prepare data
                    processed_records = []
                    
                    for _, row in df.iterrows():
                        try:
                            # Clean core fields
                            ein = self.clean_text_value(row.get('EIN'))
                            if not ein:
                                continue
                            
                            # Build 990-EZ record (simplified fields)
                            record = {
                                'ein': ein,
                                'tax_year': tax_year,
                                'taxpd': self.clean_numeric_value(row.get('taxpd')),
                                'efile': self.clean_text_value(row.get('efile')),
                                'subseccd': self.clean_numeric_value(row.get('subseccd')),
                                
                                # Core financial data (simplified)
                                'totrevnue': self.clean_numeric_value(row.get('totrevnue')),
                                'totcntrbs': self.clean_numeric_value(row.get('totcntrbs')),
                                'prgmservrev': self.clean_numeric_value(row.get('prgmservrev')),
                                'duesassesmnts': self.clean_numeric_value(row.get('duesassesmnts')),
                                'othrinvstinc': self.clean_numeric_value(row.get('othrinvstinc')),
                                'grsamtsalesastothr': self.clean_numeric_value(row.get('grsamtsalesastothr')),
                                'grsincgaming': self.clean_numeric_value(row.get('grsincgaming')),
                                'grsrevnuefndrsng': self.clean_numeric_value(row.get('grsrevnuefndrsng')),
                                'netincfndrsng': self.clean_numeric_value(row.get('netincfndrsng')),
                                'grsalesminusret': self.clean_numeric_value(row.get('grsalesminusret')),
                                'costgoodsold': self.clean_numeric_value(row.get('costgoodsold')),
                                'grsprft': self.clean_numeric_value(row.get('grsprft')),
                                'othrevnue': self.clean_numeric_value(row.get('othrevnue')),
                                
                                # Expenses
                                'totexpns': self.clean_numeric_value(row.get('totexpns')),
                                'grntsandothrasstnc': self.clean_numeric_value(row.get('grntsandothrasstnc')),
                                'benftspaidtomembers': self.clean_numeric_value(row.get('benftspaidtomembers')),
                                'salariesothrcompempl': self.clean_numeric_value(row.get('salariesothrcompempl')),
                                'profndraising': self.clean_numeric_value(row.get('profndraising')),
                                'totfundrsngexpns': self.clean_numeric_value(row.get('totfundrsngexpns')),
                                'othrexpnstot': self.clean_numeric_value(row.get('othrexpnstot')),
                                
                                # Net position
                                'totexcessyr': self.clean_numeric_value(row.get('totexcessyr')),
                                'totnetassetsend': self.clean_numeric_value(row.get('totnetassetsend')),
                                'totnetassetsbod': self.clean_numeric_value(row.get('totnetassetsbod')),
                                
                                # Assets (simplified)
                                'totassetsend': self.clean_numeric_value(row.get('totassetsend')),
                                'casheoyamount': self.clean_numeric_value(row.get('casheoyamount')),
                                'accntsrcvblend': self.clean_numeric_value(row.get('accntsrcvblend')),
                                'lndbldngsequipend': self.clean_numeric_value(row.get('lndbldngsequipend')),
                                'invstmntsend': self.clean_numeric_value(row.get('invstmntsend')),
                                'othrassetsend': self.clean_numeric_value(row.get('othrassetsend')),
                                
                                # Liabilities (simplified)
                                'totliabltend': self.clean_numeric_value(row.get('totliabltend')),
                                'accntspyblend': self.clean_numeric_value(row.get('accntspyblend')),
                                'mortgnotespyblend': self.clean_numeric_value(row.get('mortgnotespyblend')),
                                'othrliabltend': self.clean_numeric_value(row.get('othrliabltend')),
                                
                                # Operational
                                'unrelbusincd': self.clean_numeric_value(row.get('unrelbusincd')),
                                'initiationfee': self.clean_numeric_value(row.get('initiationfee')),
                                'grspublicrcpts': self.clean_numeric_value(row.get('grspublicrcpts')),
                                
                                # Public support
                                'nonpfrea': self.clean_text_value(row.get('nonpfrea')),
                                'gftgrntrcvd170': self.clean_numeric_value(row.get('gftgrntrcvd170')),
                                'totsupp509': self.clean_numeric_value(row.get('totsupp509'))
                            }
                            
                            processed_records.append(record)
                            
                        except Exception as e:
                            logger.warning(f"Error processing 990-EZ record: {e}")
                            self.import_stats['total_errors'] += 1
                            continue
                    
                    # Batch insert using executemany
                    if processed_records:
                        # Create INSERT statement
                        columns = list(processed_records[0].keys())
                        placeholders = ', '.join(['?' for _ in columns])
                        insert_sql = f"INSERT OR IGNORE INTO form_990ez ({', '.join(columns)}) VALUES ({placeholders})"
                        
                        # Convert records to tuples
                        record_tuples = [tuple(record[col] for col in columns) for record in processed_records]
                        
                        # Execute in smaller batches
                        batch_size = 1000  # 990-EZ has fewer columns
                        for i in range(0, len(record_tuples), batch_size):
                            batch = record_tuples[i:i+batch_size]
                            conn.executemany(insert_sql, batch)
                        conn.commit()
                        
                        processed_count = len(processed_records)
                        total_processed += processed_count
                        logger.info(f"Inserted {processed_count} Form 990-EZ records from {os.path.basename(file_path)}")
                
                except Exception as e:
                    logger.error(f"Error processing 990-EZ file {file_path}: {e}")
                    self.import_stats['total_errors'] += 1
            
            self.import_stats['form_990ez_records'] = total_processed
            logger.info(f"Form 990-EZ processing complete. Total records: {total_processed}")
    
    def log_import_stats(self):
        """Log detailed import statistics to database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Insert import log entry
                log_entry = {
                    'import_date': datetime.now().isoformat(),
                    'file_name': 'Comprehensive BMF/SOI Import',
                    'file_type': 'Multi-Type',
                    'tax_year': None,
                    'records_processed': sum([
                        self.import_stats['bmf_records'],
                        self.import_stats['form_990_records'],
                        self.import_stats['form_990pf_records'],
                        self.import_stats['form_990ez_records']
                    ]),
                    'records_success': sum([
                        self.import_stats['bmf_records'],
                        self.import_stats['form_990_records'],
                        self.import_stats['form_990pf_records'],
                        self.import_stats['form_990ez_records']
                    ]),
                    'records_error': self.import_stats['total_errors'],
                    'processing_time_seconds': self.import_stats['processing_time'],
                    'notes': f"BMF: {self.import_stats['bmf_records']}, 990: {self.import_stats['form_990_records']}, 990-PF: {self.import_stats['form_990pf_records']}, 990-EZ: {self.import_stats['form_990ez_records']}"
                }
                
                df_log = pd.DataFrame([log_entry])
                df_log.to_sql('data_import_log', conn, if_exists='append', index=False)
                
                logger.info("Import statistics logged to database")
                
        except Exception as e:
            logger.error(f"Error logging import stats: {e}")
    
    def generate_summary_report(self):
        """Generate comprehensive summary report."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Get table counts
                counts = {}
                tables = ['bmf_organizations', 'form_990', 'form_990pf', 'form_990ez']
                
                for table in tables:
                    result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    counts[table] = result[0] if result else 0
                
                # Get coverage by year
                year_coverage = {}
                for table in ['form_990', 'form_990pf', 'form_990ez']:
                    if counts[table] > 0:
                        year_query = f"SELECT tax_year, COUNT(*) FROM {table} GROUP BY tax_year ORDER BY tax_year"
                        year_results = conn.execute(year_query).fetchall()
                        year_coverage[table] = {year: count for year, count in year_results}
                
                # Get state coverage
                state_query = "SELECT state, COUNT(*) FROM bmf_organizations GROUP BY state ORDER BY COUNT(*) DESC"
                state_results = conn.execute(state_query).fetchall()
                state_coverage = {state: count for state, count in state_results}
                
                # Print comprehensive report
                print("\n" + "="*80)
                print("BMF/SOI DATABASE CREATION COMPLETE")
                print("="*80)
                
                print(f"\n📊 RECORD COUNTS:")
                print(f"   BMF Organizations: {counts['bmf_organizations']:,}")
                print(f"   Form 990 (Large Nonprofits): {counts['form_990']:,}")
                print(f"   Form 990-PF (Foundations): {counts['form_990pf']:,}")
                print(f"   Form 990-EZ (Small Nonprofits): {counts['form_990ez']:,}")
                print(f"   TOTAL RECORDS: {sum(counts.values()):,}")
                
                print(f"\n📅 YEAR COVERAGE:")
                for table, years in year_coverage.items():
                    print(f"   {table}:")
                    for year, count in years.items():
                        print(f"     {year}: {count:,} records")
                
                print(f"\n🗺️  STATE COVERAGE (Top 10):")
                for i, (state, count) in enumerate(list(state_coverage.items())[:10]):
                    print(f"   {state}: {count:,} organizations")
                
                print(f"\n⚡ PERFORMANCE:")
                print(f"   Processing Time: {self.import_stats['processing_time']:.2f} seconds")
                print(f"   Total Errors: {self.import_stats['total_errors']:,}")
                print(f"   Database Size: {os.path.getsize(self.database_path) / (1024*1024*1024):.2f} GB")
                
                print(f"\n🎯 SUCCESS METRICS:")
                total_expected = sum(counts.values())
                success_rate = (total_expected - self.import_stats['total_errors']) / total_expected * 100 if total_expected > 0 else 0
                print(f"   Success Rate: {success_rate:.2f}%")
                print(f"   Average Records/Second: {total_expected / self.import_stats['processing_time']:.0f}")
                
                print(f"\n🚀 READY FOR INTEGRATION:")
                print(f"   Database Path: {self.database_path}")
                print(f"   BMF Processor Migration: Ready")
                print(f"   Advanced Discovery: Enabled")
                print(f"   Foundation Intelligence: Activated")
                
                print("="*80)
                
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
    
    def run_full_etl(self):
        """
        Execute complete ETL pipeline for all data sources.
        """
        start_time = time.time()
        logger.info("Starting comprehensive BMF/SOI ETL pipeline...")
        
        try:
            # Step 1: Create database schema
            self.create_database_schema()
            
            # Step 2: Detect available files
            files = self.detect_soi_files()
            
            # Step 3: Process each data source
            if files['bmf']:
                self.process_bmf_data(files['bmf'])
            
            if files['990']:
                self.process_990_data(files['990'])
            
            if files['990pf']:
                self.process_990pf_data(files['990pf'])
            
            if files['990ez']:
                self.process_990ez_data(files['990ez'])
            
            # Step 4: Calculate processing time
            end_time = time.time()
            self.import_stats['processing_time'] = end_time - start_time
            
            # Step 5: Log statistics and generate report
            self.log_import_stats()
            self.generate_summary_report()
            
            logger.info("ETL pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            raise


def main():
    """Main execution function for ETL pipeline."""
    try:
        # Initialize processor
        processor = BMFSOIETLProcessor()
        
        # Run full ETL pipeline
        processor.run_full_etl()
        
        print("\n🎉 SUCCESS: Nonprofit Intelligence Database Created!")
        print("Ready for BMF processor migration and advanced discovery capabilities.")
        
    except Exception as e:
        logger.error(f"ETL pipeline execution failed: {e}")
        raise


if __name__ == "__main__":
    main()