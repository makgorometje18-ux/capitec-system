# Testing Checklist - Flask Dashboard

After installing Flask dependencies and starting the app, use this checklist to validate all fixes:

## 1. Flask Startup Test

```powershell
cd c:\Users\Obedbosh\Music\OBED\ BOSHIELO\Capitec-Reconciliation-System\web_dashboard
python -m pip install -r requirements.txt
python app.py
```

**Expected Output:**
```
Starting Capitec Daily Reconciliation System Web Dashboard
Database path: ../database/cdrs.db
Database exists: True
Backend available: True
Running on http://127.0.0.1:5000
```

---

## 2. KPI Metrics Test (Bug Fix #1 & #2 Verification)

**Test:** CardStatistics and ValidationError query fixes

**URL:** http://localhost:5000/api/dashboard/kpi

**Expected JSON Response:**
```json
{
  "total_workbooks": 1,
  "today_validations": 1,
  "today_errors": 0,
  "success_rate": 100.0,
  "cards_processed": 0,
  "sim_orders": 0,
  "bank_orders": 0,
  "db_status": "OK"
}
```

**What to Check:**
- [ ] No database query errors in Flask console
- [ ] `cards_processed` shows number (not 0)
- [ ] `sim_orders` shows number
- [ ] `bank_orders` shows number
- [ ] All values are numbers (not null/error)

**If cards_processed = 0:** This is expected if no CardStatistics records exist in database

---

## 3. Recent Validations Test

**URL:** http://localhost:5000/api/dashboard/recent

**Expected JSON Response:**
```json
[
  {
    "date": "2026-07-10",
    "workbook": "CAPITEC DAILY ORDERS REPORT JULY 2026",
    "status": "PASS",
    "duration": 45,
    "errors": 0,
    "warnings": 0
  }
]
```

**What to Check:**
- [ ] Returns array of validation records
- [ ] Each record has date, workbook, status, duration, errors, warnings
- [ ] Dates are formatted correctly (YYYY-MM-DD)
- [ ] Status is either "PASS" or "FAIL"

---

## 4. Error Breakdown Test

**URL:** http://localhost:5000/api/dashboard/errors

**Expected JSON Response:**
```json
{
  "duplicates": 3,
  "batch_errors": 3,
  "bag_errors": 3,
  "blank_errors": 0,
  "card_type_errors": 0,
  "cross_workbook_errors": 0
}
```

**What to Check:**
- [ ] Returns all 6 error type counts
- [ ] All values are numbers (not null/error)
- [ ] Counts match database DuplicateRecord table

---

## 5. SQL Injection Prevention Test (Bug Fix #3 Verification)

**URL with Attack Payload:** 
```
http://localhost:5000/api/audit/history?sort_by=DateTime);DROP TABLE AuditLog;--&sort_order=DESC
```

**Expected Behavior:**
- [ ] Returns 200 status code (no error)
- [ ] Returns audit history records (not empty)
- [ ] AuditLog table still exists (not deleted)
- [ ] Flask console shows no SQL errors

**Safe Sort Parameters to Test:**
```
http://localhost:5000/api/audit/history?sort_by=DateTime&sort_order=ASC
http://localhost:5000/api/audit/history?sort_by=Action&sort_order=DESC
http://localhost:5000/api/audit/history?sort_by=User&sort_order=ASC
```

**What to Check:**
- [ ] All valid parameters work
- [ ] Invalid parameters are silently corrected
- [ ] Results are sorted correctly

---

## 6. Page Navigation Test (Bug Fix #4 Verification)

**Home Page:**
- [ ] http://localhost:5000/ → Loads successfully (index.html)
- [ ] Shows 8 KPI cards with values
- [ ] Shows Recent Validations table
- [ ] Shows error breakdown cards
- [ ] Shows charts (Pass/Fail doughnut and daily trend line)

**Validation Page (SPA redirect):**
- [ ] http://localhost:5000/validation → Loads without 500 error
- [ ] Shows file upload zone
- [ ] Shows validation results section

**Analytics Page (SPA redirect):**
- [ ] http://localhost:5000/analytics → Loads without 500 error
- [ ] Shows error distribution chart
- [ ] Shows validation trend chart

**Audit Page (SPA redirect):**
- [ ] http://localhost:5000/audit → Loads without 500 error
- [ ] Shows search box
- [ ] Shows audit history table
- [ ] Shows export CSV button

**Summary Page (SPA redirect):**
- [ ] http://localhost:5000/summary → Loads without 500 error
- [ ] Shows reconciliation summary
- [ ] Shows reconciliation analysis cards

**Reports Page (SPA redirect):**
- [ ] http://localhost:5000/reports → Loads without 500 error
- [ ] Shows report generation options

**Settings Page (SPA redirect):**
- [ ] http://localhost:5000/settings → Loads without 500 error
- [ ] Shows settings form (theme, refresh interval, etc.)
- [ ] Settings can be saved

**About Page (SPA redirect):**
- [ ] http://localhost:5000/about → Loads without 500 error
- [ ] Shows version and system status

---

## 7. File Upload & Database Persistence Test (Bug Fix #5 Verification)

**Test:** Upload sample Excel file and verify database persistence

**Steps:**
1. Navigate to http://localhost:5000/validation
2. Upload a file from `sample_files/` directory
3. Wait for validation to complete
4. Check browser console for any JavaScript errors

**Expected Behavior:**
- [ ] File upload succeeds (progress bar completes)
- [ ] Validation results display (errors, warnings, pass/fail status)
- [ ] New entry appears in AuditLog table (check with test script)
- [ ] ValidationRun record created in database
- [ ] ValidationError records created for each error found

**To verify database persistence:**
```python
import sqlite3
conn = sqlite3.connect('../database/cdrs.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check latest validation run
cursor.execute("SELECT * FROM ValidationRun ORDER BY RunID DESC LIMIT 1")
print(cursor.fetchone())

# Check audit log entries
cursor.execute("SELECT * FROM AuditLog ORDER BY LogID DESC LIMIT 5")
for row in cursor.fetchall():
    print(dict(row))

conn.close()
```

**Expected Output:**
```
<Row object with WorkbookID, StartTime, Duration, Passed, ErrorCount, WarningCount>
Multiple recent audit log entries with "Workbook Validation" action
```

---

## 8. Auto-Refresh Test

**Test:** Verify 5-second auto-refresh functionality

**Steps:**
1. Navigate to http://localhost:5000/
2. Open browser DevTools (F12)
3. Go to Network tab
4. Watch for API calls to `/api/dashboard/*` endpoints
5. Wait for 5+ seconds

**Expected Behavior:**
- [ ] After 5 seconds, new XHR requests appear in Network tab
- [ ] Requests are made to: `/api/dashboard/kpi`, `/api/dashboard/recent`, `/api/dashboard/errors`, `/api/dashboard/trend`
- [ ] KPI numbers animate when refreshed
- [ ] Page does NOT full refresh (browser title doesn't change)
- [ ] Page updates smoothly without flickering

---

## 9. Settings Persistence Test

**Steps:**
1. Navigate to http://localhost:5000/settings
2. Change "Theme" from "Light" to "Dark"
3. Change "Refresh Interval" to 10 seconds
4. Click "Save Settings"
5. Refresh the page (Ctrl+R)

**Expected Behavior:**
- [ ] Settings save request succeeds (200 response)
- [ ] After page refresh, settings are still set to "Dark" theme
- [ ] Auto-refresh interval changes to 10 seconds
- [ ] Dark theme CSS is applied (if implemented)

---

## 10. Backend Integration Test

**Test:** Verify backend classes are available

**Check Flask startup logs for:**
- [ ] "Backend available: True" message
- [ ] No ImportError messages for ValidationEngine, BackupManager, WorkbookLoader

**If "Backend available: False":**
- Check that `sys.path` modification works: `sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))`
- Verify `src/core/` directory exists in parent directory
- Verify backend classes exist in `src/core/validation_engine.py`, etc.

---

## 11. Error Handling Test

**Test:** Verify graceful error handling

**Simulate errors:**

**1. Upload invalid file:**
- URL: http://localhost:5000/validation
- Upload a `.txt` file
- Expected: Error message "Invalid file format. Use .xlsx, .xlsm, or .xls"

**2. No file selected:**
- URL: http://localhost:5000/validation
- Click upload without selecting file
- Expected: Error message "No file selected"

**3. Database connection failure:**
- Temporarily rename or delete `database/cdrs.db`
- Navigate to http://localhost:5000
- Expected: Graceful error (not 500 crash), dashboard shows "DB status: OFFLINE"

**4. Backend unavailable:**
- Temporarily break the ValidationEngine import
- Upload file
- Expected: Error message "Validation backend not available" (500 status)

---

## 12. CORS Test (if testing from external frontend)

**If accessing from different port (e.g., React frontend on 3000):**

```javascript
// In browser console, from http://localhost:3000
fetch('http://localhost:5000/api/dashboard/kpi')
  .then(r => r.json())
  .then(d => console.log(d))
```

**Expected Behavior:**
- [ ] Request succeeds (no CORS errors)
- [ ] Returns KPI JSON data
- [ ] No "Access-Control-Allow-Origin" errors in console

---

## 13. CSV Export Test

**URL:** http://localhost:5000/api/audit/export

**Expected Behavior:**
- [ ] Download starts automatically
- [ ] File is named `audit_export_YYYYMMDD_HHMMSS.csv`
- [ ] CSV opens in Excel with audit history data
- [ ] Columns: DateTime, Action, User, Result, Description
- [ ] All audit log entries are included

---

## 14. Health Check Test

**URL:** http://localhost:5000/health

**Expected JSON Response:**
```json
{
  "status": "ok",
  "service": "CDRS Web Dashboard",
  "backend": "available"
}
```

**What to Check:**
- [ ] Status is "ok"
- [ ] Service name matches
- [ ] Backend shows "available" or "unavailable"

---

## 15. Browser Console Validation

**Steps:**
1. Open http://localhost:5000 in Chrome/Firefox
2. Open Developer Tools (F12)
3. Check Console tab
4. Navigate through all pages

**Expected:**
- [ ] No red error messages
- [ ] No "Uncaught" exceptions
- [ ] Only warnings/deprecation notices are acceptable
- [ ] No "undefined is not a function" errors

**Acceptable Warnings:**
- Deprecation warning about sqlite3 date adapter (Python 3.12 compatibility)
- Chart.js warnings about responsive behavior

---

## Test Summary Checklist

**Critical Tests (Must Pass):**
- [ ] Flask app starts without errors
- [ ] KPI endpoints return correct JSON
- [ ] All 7 page routes load without 500 errors
- [ ] SQL injection attempt is blocked
- [ ] File upload creates database records
- [ ] No red errors in browser console

**Important Tests:**
- [ ] Auto-refresh works (5-second intervals)
- [ ] Settings save and persist
- [ ] Audit history displays and can be exported
- [ ] Backend integration shows "available"
- [ ] Charts render with data

**Nice-to-Have Tests:**
- [ ] Dark theme works
- [ ] Responsive layout on mobile
- [ ] Export CSV downloads
- [ ] Sort parameters work on audit history

---

## Troubleshooting Guide

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution:**
```powershell
pip install -r requirements.txt
# or install individual packages
pip install Flask==2.3.3 Flask-CORS==4.0.0 Werkzeug==2.3.7 Jinja2==3.1.2 python-dateutil==2.8.2
```

### Issue: "database/cdrs.db not found"
**Solution:**
- Verify database file exists at `c:\Users\Obedbosh\Music\OBED BOSHIELO\Capitec-Reconciliation-System\database\cdrs.db`
- Check DB_PATH in app.py (line ~32)
- Run schema.sql to create tables if needed

### Issue: "ConnectionRefusedError: [Errno 10061]" when accessing localhost:5000
**Solution:**
- Ensure Flask app is running (check terminal window)
- Check that port 5000 is not in use: `netstat -tuln | findstr :5000`
- Restart Flask app on different port: `python app.py --port 5001`

### Issue: "Backend available: False"
**Solution:**
- Check that `src/` directory exists in parent folder
- Verify `src/core/validation_engine.py` exists
- Check sys.path manipulation in app.py (line ~24)

### Issue: All KPI metrics showing 0
**Solution:**
- Likely no test data in database
- Run integration_test.py to insert sample data
- Or upload actual Excel file to generate data

---

**Last Updated:** 2026-07-12  
**Test Environment:** Python 3.10+, Windows 11, Flask 2.3.3  
**Database:** SQLite3 at `database/cdrs.db`
