#!/usr/bin/env python3
"""
Inspect database schema to understand the structure
"""

import sqlite3
import json

def inspect_database():
    conn = sqlite3.connect("data/catalynx.db")
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Database Tables:")
    for table in tables:
        table_name = table[0]
        print(f"\n{table_name}:")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample_rows = cursor.fetchall()
        
        if sample_rows:
            print(f"  Sample data ({len(sample_rows)} rows):")
            column_names = [col[1] for col in columns]
            for i, row in enumerate(sample_rows):
                print(f"    Row {i+1}: {dict(zip(column_names, row))}")
    
    conn.close()

if __name__ == "__main__":
    inspect_database()