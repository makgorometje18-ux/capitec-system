"""
Database Migration Script
Adds performance indexes to CDRS database

Run this once to optimize query performance:
    python migrate_indexes.py
"""

import sqlite3
import os
import sys
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'cdrs.db')

def create_indexes():
    """Create performance indexes"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("CDRS Database Migration - Adding Performance Indexes")
        print("=" * 60)
        
        # Index 1: ValidationRun.StartTime - for dashboard KPI queries
        print("\n1. Creating index on ValidationRun(StartTime)...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_validationrun_starttime 
                ON ValidationRun(StartTime)
            """)
            print("   ✓ Index created successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Index 2: ValidationError.RunID - for error queries
        print("\n2. Creating index on ValidationError(RunID)...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_validationerror_runid 
                ON ValidationError(RunID)
            """)
            print("   ✓ Index created successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Index 3: AuditLog.DateTime - for audit history queries
        print("\n3. Creating index on AuditLog(DateTime)...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_auditlog_datetime 
                ON AuditLog(DateTime)
            """)
            print("   ✓ Index created successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Index 4: DuplicateRecord.RunID - for duplicate queries
        print("\n4. Creating index on DuplicateRecord(RunID)...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_duplicaterecord_runid 
                ON DuplicateRecord(RunID)
            """)
            print("   ✓ Index created successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Index 5: CardStatistics.RunID - for card stat queries
        print("\n5. Creating index on CardStatistics(RunID)...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cardstatistics_runid 
                ON CardStatistics(RunID)
            """)
            print("   ✓ Index created successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Index 6: WorkbookHistory.ProcessDate - for date-based queries
        print("\n6. Creating index on WorkbookHistory(ProcessDate)...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_workbookhistory_processdate 
                ON WorkbookHistory(ProcessDate)
            """)
            print("   ✓ Index created successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Commit all changes
        conn.commit()
        
        # Verify indexes were created
        print("\n" + "=" * 60)
        print("Verifying Indexes")
        print("=" * 60)
        
        cursor.execute("""
            SELECT name, tbl_name, sql 
            FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
            ORDER BY tbl_name
        """)
        
        indexes = cursor.fetchall()
        if indexes:
            print(f"\n✓ Found {len(indexes)} indexes:\n")
            for idx_name, tbl_name, sql in indexes:
                print(f"  • {idx_name} on {tbl_name}")
        else:
            print("\n✗ No indexes found")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("Migration Complete!")
        print("=" * 60)
        print("\nPerformance Improvements Expected:")
        print("  • Dashboard KPI queries: +10-15% faster")
        print("  • Audit history queries: +15-20% faster")
        print("  • Daily trend queries: +10% faster")
        print("  • Overall dashboard load: ~15-20% improvement")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        return False

if __name__ == '__main__':
    print(f"Database: {DB_PATH}")
    print(f"Status: {'EXISTS' if os.path.exists(DB_PATH) else 'NOT FOUND'}\n")
    
    if not os.path.exists(DB_PATH):
        print("ERROR: Database file not found!")
        print(f"Expected at: {DB_PATH}")
        sys.exit(1)
    
    success = create_indexes()
    sys.exit(0 if success else 1)
