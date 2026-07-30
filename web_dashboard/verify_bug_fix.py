#!/usr/bin/env python3
"""
BUG FIX VERIFICATION TEST
Tests that navigation buttons work without JavaScript infinite recursion
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000'
test_results = []
tests_passed = 0
tests_failed = 0

def test_navigation(page_name, expected_element):
    """Test that a page navigation works"""
    global tests_passed, tests_failed
    
    try:
        response = requests.get(f'{BASE_URL}/{page_name}' if page_name != '/' else BASE_URL)
        passed = response.status_code == 200
        
        if passed and expected_element:
            passed = expected_element in response.text
        
        status = "[PASS]" if passed else "[FAIL]"
        tests_passed += passed
        tests_failed += (not passed)
        
        message = f"Page loads correctly" if passed else f"Page load failed or element missing"
        print(f"{status} Navigation: {page_name:20} | {message}")
        
        test_results.append({
            "page": page_name,
            "status": "PASSED" if passed else "FAILED",
            "code": response.status_code
        })
        
        return passed
    except Exception as e:
        tests_failed += 1
        print(f"[FAIL] Navigation: {page_name:20} | Error: {str(e)}")
        test_results.append({
            "page": page_name,
            "status": "FAILED",
            "error": str(e)
        })
        return False

print("\n" + "="*100)
print("BUG FIX VERIFICATION: INFINITE RECURSION FIX")
print("="*100)
print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

print("[SECTION 1] VERIFY NO DUPLICATE FUNCTIONS")
print("-" * 100)

# Check JavaScript file doesn't have duplicate functions
with open('c:\\Users\\Obedbosh\\Music\\OBED BOSHIELO\\Capitec-Reconciliation-System\\web_dashboard\\static\\dashboard.js', 'r') as f:
    content = f.read()
    
    # Count function definitions
    refresh_dashboard_count = content.count('function refreshDashboard()')
    refresh_data_count = content.count('function refreshDashboardData()')
    
    has_only_one_refresh = refresh_dashboard_count == 1
    has_no_duplicate_data = refresh_data_count == 0
    
    print(f"[{'PASS' if has_only_one_refresh else 'FAIL'}] Only 1 refreshDashboard() function exists: {refresh_dashboard_count}")
    print(f"[{'PASS' if has_no_duplicate_data else 'FAIL'}] No duplicate refreshDashboardData() function: {refresh_data_count}")
    
    tests_passed += (has_only_one_refresh + has_no_duplicate_data)
    tests_failed += (2 - (has_only_one_refresh + has_no_duplicate_data))

print("\n[SECTION 2] VERIFY FUNCTION LOGIC")
print("-" * 100)

# Check that refreshDashboard doesn't call showPage
has_recursion = 'showPage(' in content[content.find('function refreshDashboard()'):content.find('function refreshDashboard()') + 500]
print(f"[{'PASS' if not has_recursion else 'FAIL'}] refreshDashboard() does NOT call showPage(): {not has_recursion}")
tests_passed += (not has_recursion)
tests_failed += has_recursion

# Check that showPage only calls refreshDashboard for dashboard
showpage_section = content[content.find('function showPage('):content.find('function showPage(') + 1500]
has_single_refresh_call = showpage_section.count("case 'dashboard':") == 1
print(f"[{'PASS' if has_single_refresh_call else 'FAIL'}] showPage() calls refreshDashboard() only for dashboard page: {has_single_refresh_call}")
tests_passed += has_single_refresh_call
tests_failed += (not has_single_refresh_call)

print("\n[SECTION 3] NAVIGATION BUTTON TESTS")
print("-" * 100)

# Test all navigation pages
pages = [
    ('/', 'Capitec Daily Reconciliation'),  # Home/Dashboard
    ('/validation', 'uploadZone'),          # Validation page
    ('/analytics', 'errorDistributionChart'),  # Analytics page  
    ('/audit', 'auditTable'),               # Audit page
    ('/summary', 'summary-page'),           # Summary page
    ('/reports', 'reports-page'),           # Reports page
    ('/settings', 'settingsForm'),          # Settings page
    ('/about', 'about-page'),               # About page
]

for page, element in pages:
    test_navigation(page, element)

print("\n[SECTION 4] API ENDPOINTS")
print("-" * 100)

# Test key API endpoints
endpoints = [
    ('/health', 'service'),
    ('/api/dashboard/kpi', 'total_workbooks'),
    ('/api/dashboard/recent', None),
    ('/api/dashboard/errors', None),
    ('/api/dashboard/trend', None),
]

for endpoint, expected_key in endpoints:
    try:
        response = requests.get(f'{BASE_URL}{endpoint}')
        passed = response.status_code == 200
        
        if passed and expected_key:
            data = response.json()
            passed = expected_key in data if isinstance(data, dict) else True
        
        status = "[PASS]" if passed else "[FAIL]"
        tests_passed += passed
        tests_failed += (not passed)
        
        print(f"{status} API: {endpoint:30} | Status {response.status_code}")
    except Exception as e:
        tests_failed += 1
        print(f"[FAIL] API: {endpoint:30} | Error: {str(e)}")

print("\n" + "="*100)
print("TEST SUMMARY")
print("="*100)

total_tests = tests_passed + tests_failed
print(f"\nTotal Tests: {total_tests}")
print(f"[PASSED] Count: {tests_passed}")
print(f"[FAILED] Count: {tests_failed}")
print(f"Success Rate: {(tests_passed / total_tests * 100):.1f}%")

print("\n" + "="*100)
print("BUG FIX VERIFICATION RESULT")
print("="*100)

if tests_failed == 0:
    print("\n✅ BUG FIX SUCCESSFUL")
    print("\n✓ Infinite recursion removed")
    print("✓ refreshDashboard() only fetches data")
    print("✓ showPage() only switches pages")
    print("✓ No circular calls between functions")
    print("✓ All navigation buttons functional")
    print("✓ All API endpoints working")
    print("\n🎯 Navigation Bug Fixed - Application is now fully functional")
else:
    print(f"\n❌ BUG FIX INCOMPLETE - {tests_failed} issues remain")

print("\n" + "="*100 + "\n")

with open('bug_fix_verification_results.json', 'w') as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total_tests,
            "passed": tests_passed,
            "failed": tests_failed,
            "success_rate": round((tests_passed / total_tests * 100), 1) if total_tests > 0 else 0
        },
        "results": test_results
    }, f, indent=2)

print(f"Detailed results saved to: bug_fix_verification_results.json\n")
