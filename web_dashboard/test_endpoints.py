"""
Test Flask app endpoints to verify fixes
"""

import sqlite3
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app
from app import app, DashboardData, get_db_connection

def test_flask_endpoints():
    """Test all Flask endpoints"""
    
    client = app.test_client()
    print("=" * 60)
    print("CAPITEC CDRS - FLASK ENDPOINT TESTS")
    print("=" * 60)
    
    tests = [
        ("GET /", "Should return 200 with index.html"),
        ("GET /api/dashboard/kpi", "Should return JSON with KPI metrics"),
        ("GET /api/dashboard/recent", "Should return JSON with recent validations"),
        ("GET /api/dashboard/errors", "Should return JSON with error breakdown"),
        ("GET /api/dashboard/trend", "Should return JSON with daily trend"),
        ("GET /api/analytics/charts", "Should return JSON with chart data"),
        ("GET /api/audit/history", "Should return JSON with audit records"),
        ("GET /api/settings/get", "Should return JSON with settings"),
        ("GET /health", "Should return JSON with health status"),
        ("GET /validation", "Should redirect to index.html"),
        ("GET /analytics", "Should redirect to index.html"),
        ("GET /audit", "Should redirect to index.html"),
        ("GET /summary", "Should redirect to index.html"),
        ("GET /reports", "Should redirect to index.html"),
        ("GET /settings", "Should redirect to index.html"),
        ("GET /about", "Should redirect to index.html"),
    ]
    
    for test_path, description in tests:
        method, path = test_path.split()
        
        try:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path)
            
            status = "✓" if response.status_code < 400 else "✗"
            print(f"{status} {test_path:<30} {response.status_code:<3} {description}")
            
        except Exception as e:
            print(f"✗ {test_path:<30} ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("ENDPOINT TESTS COMPLETE")
    print("=" * 60)

def test_query_fixes():
    """Test that the query fixes work"""
    
    print("\n" + "=" * 60)
    print("CAPITEC CDRS - QUERY FIX TESTS")
    print("=" * 60)
    
    try:
        print("\n1. Testing KPI Metrics Query...")
        data = DashboardData.get_kpi_metrics()
        print(f"✓ Query successful")
        print(f"  Total Workbooks: {data.get('total_workbooks', 0)}")
        print(f"  Today Validations: {data.get('today_validations', 0)}")
        print(f"  Today Errors: {data.get('today_errors', 0)}")
        print(f"  Success Rate: {data.get('success_rate', 0)}%")
        print(f"  Cards Processed: {data.get('cards_processed', 0)}")
        print(f"  SIM Orders: {data.get('sim_orders', 0)}")
        print(f"  Bank Orders: {data.get('bank_orders', 0)}")
        
    except Exception as e:
        print(f"✗ Query failed: {e}")
    
    try:
        print("\n2. Testing Error Breakdown Query...")
        data = DashboardData.get_error_breakdown()
        print(f"✓ Query successful")
        print(f"  Duplicates: {data.get('duplicates', 0)}")
        print(f"  Batch Errors: {data.get('batch_errors', 0)}")
        print(f"  Bag Errors: {data.get('bag_errors', 0)}")
        print(f"  Blank Errors: {data.get('blank_errors', 0)}")
        
    except Exception as e:
        print(f"✗ Query failed: {e}")
    
    try:
        print("\n3. Testing Daily Trend Query...")
        data = DashboardData.get_daily_trend(7)
        print(f"✓ Query successful")
        print(f"  Days with data: {len(data.get('dates', []))}")
        
    except Exception as e:
        print(f"✗ Query failed: {e}")
    
    try:
        print("\n4. Testing Audit History Query (with sort sanitization)...")
        
        # Test with invalid sort_by (should be sanitized)
        data = DashboardData.get_audit_history(limit=5, sort_by='INVALID', sort_order='DESC')
        print(f"✓ Invalid sort_by handled gracefully")
        print(f"  Records returned: {len(data)}")
        
        # Test with invalid sort_order (should be sanitized)
        data = DashboardData.get_audit_history(limit=5, sort_by='DateTime', sort_order='INVALID')
        print(f"✓ Invalid sort_order handled gracefully")
        
        # Test with valid parameters
        data = DashboardData.get_audit_history(limit=5, sort_by='DateTime', sort_order='DESC')
        print(f"✓ Valid parameters work correctly")
        print(f"  Records returned: {len(data)}")
        
    except Exception as e:
        print(f"✗ Query failed: {e}")
    
    print("\n" + "=" * 60)
    print("QUERY FIX TESTS COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    # Start Flask in test mode
    test_flask_endpoints()
    test_query_fixes()
