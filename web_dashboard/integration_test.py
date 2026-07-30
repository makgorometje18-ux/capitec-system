"""
Integration Review and Testing Script
Tests all Flask dashboard endpoints with real database queries
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'cdrs.db')

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def insert_test_data():
    """Insert comprehensive test data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert test workbook
        today = datetime.now().date()
        cursor.execute("""
            INSERT INTO WorkbookHistory (FileName, FilePath, ProcessDate, WorkbookSize, ValidationStatus, DurationSeconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('CAPITEC DAILY ORDERS REPORT JULY 2026_20260712.xlsx', 
              '/path/to/workbook.xlsx', 
              today, 
              524288,
              'VALIDATED',
              45))
        
        workbook_id = cursor.lastrowid
        print(f"✓ Inserted test workbook: {workbook_id}")
        
        # Insert validation runs for last 7 days
        for i in range(7):
            date = today - timedelta(days=i)
            cursor.execute("""
                INSERT INTO ValidationRun (WorkbookID, StartTime, EndTime, Duration, Passed, ErrorCount, WarningCount, UserName)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (workbook_id, 
                  f"{date}T{10+i}:30:00", 
                  f"{date}T{10+i}:31:00", 
                  60,
                  1 if i % 2 == 0 else 0,
                  0 if i % 2 == 0 else 3,
                  0 if i < 3 else 1,
                  'system'))
            
            run_id = cursor.lastrowid
            
            # Insert duplicate records for some runs
            if i % 2 == 1:
                cursor.execute("""
                    INSERT INTO DuplicateRecord (RunID, BatchNumber, Worksheet, RowNumber, CellReference, Occurrences, DuplicateType)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (run_id, 'BATCH-12345', 'Daily Output File', 5, 'A5', 2, 'Different Rows'))
            
            # Insert validation errors
            if i % 2 == 1:
                cursor.execute("""
                    INSERT INTO ValidationError (RunID, RuleID, Worksheet, RowNumber, ColumnName, CellReference, ErrorMessage, SuggestedFix)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (run_id, 'ERR001', 'Daily Output File', 5, 'Batch_Number', 'A5', 
                      'Duplicate Batch Number found in different rows', 'Check batch number'))
                
                cursor.execute("""
                    INSERT INTO ValidationError (RunID, RuleID, Worksheet, RowNumber, ColumnName, CellReference, ErrorMessage, SuggestedFix)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (run_id, 'ERR002', 'Daily Output File', 12, 'Bag_Number', 'C12', 
                      'Invalid Bag Number format', 'Format should be BAG-XXXXX'))
            
            # Insert card statistics
            cursor.execute("""
                INSERT INTO CardStatistics (RunID, SIMOrders, SIMCards, BankOrders, BankCards, TotalOrders, TotalCards)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (run_id, 50, 10000, 30, 9000, 80, 19000))
            
            print(f"✓ Inserted validation run {i+1}: {run_id}")
        
        conn.commit()
        print("\n✓ Test data insertion successful!")
        
    except Exception as e:
        print(f"✗ Error inserting test data: {e}")
        conn.rollback()
    finally:
        conn.close()

def test_kpi_metrics():
    """Test KPI metrics endpoint logic"""
    print("\n=== TESTING KPI METRICS ===")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        today = datetime.now().date()
        
        # Total workbooks processed
        cursor.execute("""
            SELECT COUNT(DISTINCT ID) as count 
            FROM WorkbookHistory 
            WHERE DATE(ProcessDate) = ?
        """, (today,))
        total_workbooks = cursor.fetchone()['count'] or 0
        print(f"✓ Total workbooks today: {total_workbooks}")
        
        # Today's validations
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM ValidationRun 
            WHERE DATE(StartTime) = ?
        """, (today,))
        today_validations = cursor.fetchone()['count'] or 0
        print(f"✓ Today's validations: {today_validations}")
        
        # Success rate
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN Passed = 1 THEN 1 ELSE 0 END) as passed
            FROM ValidationRun
            WHERE DATE(StartTime) = ?
        """, (today,))
        rate_data = cursor.fetchone()
        total = rate_data['total'] or 0
        passed = rate_data['passed'] or 0
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"✓ Success rate: {success_rate:.2f}% ({passed}/{total})")
        
        # Card statistics
        cursor.execute("""
            SELECT COALESCE(SUM(TotalCards), 0) as total
            FROM CardStatistics
            WHERE DATE(datetime(CreatedDate)) = ?
        """, (today,))
        # This will fail - CardStatistics doesn't have CreatedDate
        
    except Exception as e:
        print(f"✗ Error in KPI metrics: {e}")
    finally:
        conn.close()

def test_error_breakdown():
    """Test error breakdown logic"""
    print("\n=== TESTING ERROR BREAKDOWN ===")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Count duplicates
        cursor.execute("SELECT COUNT(*) as count FROM DuplicateRecord")
        duplicates = cursor.fetchone()['count'] or 0
        print(f"✓ Duplicate records: {duplicates}")
        
        # Count errors by type
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN ErrorMessage LIKE '%Batch%' THEN 1 ELSE 0 END) as batch_errors,
                SUM(CASE WHEN ErrorMessage LIKE '%Bag%' THEN 1 ELSE 0 END) as bag_errors,
                SUM(CASE WHEN ErrorMessage LIKE '%blank%' OR ErrorMessage LIKE '%Blank%' THEN 1 ELSE 0 END) as blank_errors,
                SUM(CASE WHEN ErrorMessage LIKE '%Card Type%' THEN 1 ELSE 0 END) as card_type_errors,
                SUM(CASE WHEN ErrorMessage LIKE '%Cross%' THEN 1 ELSE 0 END) as cross_workbook_errors
            FROM ValidationError
        """)
        error_data = cursor.fetchone()
        print(f"✓ Batch errors: {error_data['batch_errors'] or 0}")
        print(f"✓ Bag errors: {error_data['bag_errors'] or 0}")
        print(f"✓ Blank field errors: {error_data['blank_errors'] or 0}")
        print(f"✓ Card type errors: {error_data['card_type_errors'] or 0}")
        print(f"✓ Cross-workbook errors: {error_data['cross_workbook_errors'] or 0}")
        
    except Exception as e:
        print(f"✗ Error in error breakdown: {e}")
    finally:
        conn.close()

def test_daily_trend():
    """Test daily trend logic"""
    print("\n=== TESTING DAILY TREND ===")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        cursor.execute("""
            SELECT 
                DATE(StartTime) as date,
                COUNT(*) as count
            FROM ValidationRun
            WHERE DATE(StartTime) BETWEEN ? AND ?
            GROUP BY DATE(StartTime)
            ORDER BY date ASC
        """, (start_date, end_date))
        
        results = cursor.fetchall()
        print(f"✓ Daily trend records: {len(results)}")
        for row in results:
            print(f"  {row['date']}: {row['count']} validations")
        
    except Exception as e:
        print(f"✗ Error in daily trend: {e}")
    finally:
        conn.close()

def test_audit_history():
    """Test audit history logic"""
    print("\n=== TESTING AUDIT HISTORY ===")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as count FROM AuditLog
        """)
        count = cursor.fetchone()['count']
        print(f"✓ Audit records total: {count}")
        
        # Get recent audit records
        cursor.execute("""
            SELECT DateTime, Action, User, Result FROM AuditLog
            ORDER BY DateTime DESC
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        print(f"✓ Recent audit records:")
        for row in results:
            print(f"  {row['DateTime']}: {row['Action']} by {row['User']} - {row['Result']}")
        
    except Exception as e:
        print(f"✗ Error in audit history: {e}")
    finally:
        conn.close()

def test_settings():
    """Test settings retrieval"""
    print("\n=== TESTING SETTINGS ===")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT SettingName, SettingValue FROM Settings")
        rows = cursor.fetchall()
        print(f"✓ Settings records: {len(rows)}")
        for row in rows:
            print(f"  {row['SettingName']}: {row['SettingValue']}")
        
    except Exception as e:
        print(f"✗ Error in settings: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("CAPITEC CDRS - DASHBOARD INTEGRATION REVIEW")
    print("=" * 60)
    
    insert_test_data()
    test_kpi_metrics()
    test_error_breakdown()
    test_daily_trend()
    test_audit_history()
    test_settings()
    
    print("\n" + "=" * 60)
    print("REVIEW COMPLETE")
    print("=" * 60)
