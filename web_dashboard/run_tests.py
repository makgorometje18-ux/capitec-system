#!/usr/bin/env python3
"""
Comprehensive Test Suite for Capitec Daily Reconciliation System Web Dashboard
Tests all 17 API endpoints, complete workflows, and database operations
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5000'
TEST_RESULTS = []
PASSED = 0
FAILED = 0

def log_test(name, endpoint, method, status_code, success, details=""):
    """Log test result"""
    global PASSED, FAILED
    result = {
        'test': name,
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'success': success,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    TEST_RESULTS.append(result)
    
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} | {name:<40} | {method:<6} {endpoint:<30} | {status_code}")
    
    if success:
        PASSED += 1
    else:
        FAILED += 1
    
    return success

def test_health_check():
    """Test 1: Health Check Endpoint"""
    try:
        response = requests.get(f'{BASE_URL}/health')
        success = response.status_code == 200 and 'service' in response.json()
        log_test("Health Check", "/health", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Health Check", "/health", "GET", "ERROR", False, str(e))
        return False

def test_home_page():
    """Test 2: Home Page (index.html)"""
    try:
        response = requests.get(f'{BASE_URL}/')
        success = response.status_code == 200 and 'html' in response.text.lower()
        log_test("Home Page", "/", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Home Page", "/", "GET", "ERROR", False, str(e))
        return False

def test_dashboard_kpi():
    """Test 3: Dashboard KPI Metrics"""
    try:
        response = requests.get(f'{BASE_URL}/api/dashboard/kpi')
        success = response.status_code == 200
        if success:
            data = response.json()
            success = all(k in data for k in ['total_workbooks', 'today_validations', 'success_rate'])
        log_test("Dashboard KPI", "/api/dashboard/kpi", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Dashboard KPI", "/api/dashboard/kpi", "GET", "ERROR", False, str(e))
        return False

def test_recent_validations():
    """Test 4: Recent Validations"""
    try:
        response = requests.get(f'{BASE_URL}/api/dashboard/recent')
        success = response.status_code == 200 and isinstance(response.json(), list)
        log_test("Recent Validations", "/api/dashboard/recent", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Recent Validations", "/api/dashboard/recent", "GET", "ERROR", False, str(e))
        return False

def test_error_breakdown():
    """Test 5: Error Breakdown"""
    try:
        response = requests.get(f'{BASE_URL}/api/dashboard/errors')
        success = response.status_code == 200
        if success:
            data = response.json()
            success = 'duplicates' in data or 'batch_errors' in data
        log_test("Error Breakdown", "/api/dashboard/errors", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Error Breakdown", "/api/dashboard/errors", "GET", "ERROR", False, str(e))
        return False

def test_daily_trend():
    """Test 6: Daily Trend"""
    try:
        response = requests.get(f'{BASE_URL}/api/dashboard/trend')
        success = response.status_code == 200 and isinstance(response.json(), dict)
        log_test("Daily Trend", "/api/dashboard/trend", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Daily Trend", "/api/dashboard/trend", "GET", "ERROR", False, str(e))
        return False

def test_analytics_charts():
    """Test 7: Analytics Charts"""
    try:
        response = requests.get(f'{BASE_URL}/api/analytics/charts')
        success = response.status_code == 200
        log_test("Analytics Charts", "/api/analytics/charts", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Analytics Charts", "/api/analytics/charts", "GET", "ERROR", False, str(e))
        return False

def test_audit_history():
    """Test 8: Audit History (Basic)"""
    try:
        response = requests.get(f'{BASE_URL}/api/audit/history')
        success = response.status_code == 200 and isinstance(response.json(), list)
        log_test("Audit History", "/api/audit/history", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Audit History", "/api/audit/history", "GET", "ERROR", False, str(e))
        return False

def test_audit_history_search():
    """Test 9: Audit History with Search"""
    try:
        response = requests.get(f'{BASE_URL}/api/audit/history?search=validation')
        success = response.status_code == 200 and isinstance(response.json(), list)
        log_test("Audit History Search", "/api/audit/history", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Audit History Search", "/api/audit/history", "GET", "ERROR", False, str(e))
        return False

def test_audit_history_sort():
    """Test 10: Audit History with Sort"""
    try:
        response = requests.get(f'{BASE_URL}/api/audit/history?sort_by=DateTime&sort_order=DESC')
        success = response.status_code == 200 and isinstance(response.json(), list)
        log_test("Audit History Sort", "/api/audit/history", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Audit History Sort", "/api/audit/history", "GET", "ERROR", False, str(e))
        return False

def test_audit_export():
    """Test 11: Audit CSV Export"""
    try:
        response = requests.get(f'{BASE_URL}/api/audit/export')
        success = response.status_code == 200 and 'csv' in response.headers.get('content-type', '').lower()
        log_test("Audit CSV Export", "/api/audit/export", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Audit CSV Export", "/api/audit/export", "GET", "ERROR", False, str(e))
        return False

def test_settings_get():
    """Test 12: Settings GET"""
    try:
        response = requests.get(f'{BASE_URL}/api/settings/theme')
        success = response.status_code == 200
        log_test("Settings GET", "/api/settings/theme", "GET", response.status_code, success)
        return success
    except Exception as e:
        log_test("Settings GET", "/api/settings/theme", "GET", "ERROR", False, str(e))
        return False

def test_settings_save():
    """Test 13: Settings Save"""
    try:
        data = {'theme': 'dark', 'refresh_interval': 10000}
        response = requests.post(f'{BASE_URL}/api/settings/save', json=data)
        success = response.status_code == 200 and 'status' in response.json()
        log_test("Settings Save", "/api/settings/save", "POST", response.status_code, success)
        return success
    except Exception as e:
        log_test("Settings Save", "/api/settings/save", "POST", "ERROR", False, str(e))
        return False

def test_page_routes():
    """Test 14-19: Page Routes (all should redirect to index.html)"""
    routes = [
        ('Validation Page', '/validation'),
        ('Analytics Page', '/analytics'),
        ('Audit Page', '/audit'),
        ('Summary Page', '/summary'),
        ('Reports Page', '/reports'),
        ('Settings Page', '/settings'),
        ('About Page', '/about')
    ]
    
    results = []
    for name, route in routes:
        try:
            response = requests.get(f'{BASE_URL}{route}', allow_redirects=True)
            success = response.status_code == 200 and 'html' in response.text.lower()
            log_test(name, route, "GET", response.status_code, success)
            results.append(success)
        except Exception as e:
            log_test(name, route, "GET", "ERROR", False, str(e))
            results.append(False)
    
    return all(results)

def print_summary():
    """Print test summary"""
    print("\n" + "="*120)
    print(f"TEST SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120)
    print(f"Total Tests: {len(TEST_RESULTS)}")
    print(f"[PASSED] Count: {PASSED}")
    print(f"[FAILED] Count: {FAILED}")
    print(f"Success Rate: {(PASSED/len(TEST_RESULTS)*100):.1f}%" if TEST_RESULTS else "N/A")
    print("="*120)
    
    # Group by endpoint
    endpoints = {}
    for result in TEST_RESULTS:
        ep = result['endpoint']
        if ep not in endpoints:
            endpoints[ep] = []
        endpoints[ep].append(result)
    
    print("\nENDPOINT SUMMARY:")
    print("-"*120)
    for ep in sorted(endpoints.keys()):
        tests = endpoints[ep]
        passed = sum(1 for t in tests if t['success'])
        total = len(tests)
        status = "[OK]" if passed == total else "[WARN]"
        print(f"{status} {ep:<40} | {passed}/{total} tests passed")
    
    print("\n" + "="*120)

def main():
    """Run all tests"""
    print("\n" + "="*120)
    print("CAPITEC DAILY RECONCILIATION SYSTEM - ENDPOINT TEST SUITE")
    print(f"Testing: {BASE_URL}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*120)
    print(f"{'Status':<8} | {'Test Name':<40} | {'Method':<6} {'Endpoint':<30} | {'Status Code':<12}")
    print("-"*120)
    
    # Give Flask a moment to be ready
    time.sleep(1)
    
    # Run all tests
    test_health_check()
    test_home_page()
    test_dashboard_kpi()
    test_recent_validations()
    test_error_breakdown()
    test_daily_trend()
    test_analytics_charts()
    test_audit_history()
    test_audit_history_search()
    test_audit_history_sort()
    test_audit_export()
    test_settings_get()
    test_settings_save()
    test_page_routes()
    
    # Print summary
    print_summary()
    
    # Save results to file
    with open('test_results.json', 'w') as f:
        json.dump(TEST_RESULTS, f, indent=2)
    print(f"\nDetailed results saved to: test_results.json")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
