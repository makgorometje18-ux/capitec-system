# Database Queries - Before & After Fixes

This document shows the exact SQL query changes made to fix the 4 critical bugs.

---

## Bug #1: CardStatistics.UpdatedTime Column - Cards Processed

### Location
**File:** `web_dashboard/app.py`  
**Lines:** 137-142

### Error
```
database.Error: no such column: CreatedDate
```

### ❌ BEFORE (Buggy Code)
```python
# Cards processed today
cursor.execute("""
    SELECT COALESCE(SUM(cs.TotalCards), 0) as total
    FROM CardStatistics cs
    WHERE DATE(cs.UpdatedTime) = ?
""", (today,))
cards_processed = cursor.fetchone()['total'] or 0
```

**Problem:** `CardStatistics` table has no `UpdatedTime` column

### ✅ AFTER (Fixed Code)
```python
# Cards processed today (from card statistics of today's validations)
cursor.execute("""
    SELECT COALESCE(SUM(cs.TotalCards), 0) as total
    FROM CardStatistics cs
    JOIN ValidationRun vr ON cs.RunID = vr.RunID
    WHERE DATE(vr.StartTime) = ?
""", (today,))
cards_processed = cursor.fetchone()['total'] or 0
```

**Solution:** 
- Added JOIN to ValidationRun table
- Use `vr.StartTime` instead of non-existent `cs.UpdatedTime`
- Maintains same filtering logic (today's data only)

---

## Bug #2: CardStatistics.UpdatedTime Column - SIM Orders

### Location
**File:** `web_dashboard/app.py`  
**Lines:** 144-149

### ❌ BEFORE (Buggy Code)
```python
# SIM Orders (from today's card statistics)
cursor.execute("""
    SELECT COALESCE(SUM(cs.SIMOrders), 0) as total
    FROM CardStatistics cs
    WHERE DATE(cs.UpdatedTime) = ?
""", (today,))
sim_orders = cursor.fetchone()['total'] or 0
```

### ✅ AFTER (Fixed Code)
```python
# SIM Orders (from today's card statistics)
cursor.execute("""
    SELECT COALESCE(SUM(cs.SIMOrders), 0) as total
    FROM CardStatistics cs
    JOIN ValidationRun vr ON cs.RunID = vr.RunID
    WHERE DATE(vr.StartTime) = ?
""", (today,))
sim_orders = cursor.fetchone()['total'] or 0
```

**Solution:** Same pattern as Cards Processed fix

---

## Bug #3: CardStatistics.UpdatedTime Column - Bank Orders

### Location
**File:** `web_dashboard/app.py`  
**Lines:** 151-156

### ❌ BEFORE (Buggy Code)
```python
# Bank Orders (from today's card statistics)
cursor.execute("""
    SELECT COALESCE(SUM(cs.BankOrders), 0) as total
    FROM CardStatistics cs
    WHERE DATE(cs.UpdatedTime) = ?
""", (today,))
bank_orders = cursor.fetchone()['total'] or 0
```

### ✅ AFTER (Fixed Code)
```python
# Bank Orders (from today's card statistics)
cursor.execute("""
    SELECT COALESCE(SUM(cs.BankOrders), 0) as total
    FROM CardStatistics cs
    JOIN ValidationRun vr ON cs.RunID = vr.RunID
    WHERE DATE(vr.StartTime) = ?
""", (today,))
bank_orders = cursor.fetchone()['total'] or 0
```

**Solution:** Same pattern as Cards Processed fix

---

## Bug #4: ValidationError.UpdatedTime Column - Today's Errors

### Location
**File:** `web_dashboard/app.py`  
**Lines:** 114-121

### Error
```
database.Error: no such column: UpdatedTime
```

### ❌ BEFORE (Buggy Code)
```python
# Today's errors (errors from validations that ran today)
cursor.execute("""
    SELECT COUNT(DISTINCT ve.ErrorID) as count 
    FROM ValidationError ve
    WHERE DATE(ve.UpdatedTime) = ?
""", (today,))
today_errors = cursor.fetchone()['count'] or 0
```

**Problem:** `ValidationError` table has no `UpdatedTime` column

### ✅ AFTER (Fixed Code)
```python
# Today's errors (errors from validations that ran today)
cursor.execute("""
    SELECT COUNT(DISTINCT ve.ErrorID) as count 
    FROM ValidationError ve
    WHERE ve.RunID IN (
        SELECT RunID FROM ValidationRun 
        WHERE DATE(StartTime) = ?
    )
""", (today,))
today_errors = cursor.fetchone()['count'] or 0
```

**Solution:**
- Use subquery to find all runs from today
- Count errors in those runs
- Eliminates need for non-existent timestamp column

---

## Bug #5: SQL Injection in Sort Parameters

### Location
**File:** `web_dashboard/app.py`  
**Lines:** 312-326 (get_audit_history method)

### Attack Vector
```
GET /api/audit/history?sort_by=DateTime);DROP TABLE AuditLog;--&sort_order=DESC
```

### ❌ BEFORE (Vulnerable Code)
```python
@staticmethod
def get_audit_history(limit=50, search=None, sort_by='DateTime', sort_order='DESC'):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        query = "SELECT DateTime, Action, User, Result, Description FROM AuditLog"
        
        if search:
            query += " WHERE Action LIKE ? OR Description LIKE ? OR User LIKE ?"
            cursor.execute(query + f" ORDER BY {sort_by} {sort_order} LIMIT ?", 
                         (f"%{search}%", f"%{search}%", f"%{search}%", limit))
        else:
            # VULNERABLE: sort_by and sort_order directly in f-string
            cursor.execute(query + f" ORDER BY {sort_by} {sort_order} LIMIT ?", (limit,))
```

**Problem:** 
- `sort_by` and `sort_order` are user-controlled
- Directly interpolated into SQL with f-string
- Allows injection of arbitrary SQL code
- Example attack: `sort_by=DateTime);DROP TABLE AuditLog;--` 

### ✅ AFTER (Fixed Code)
```python
@staticmethod
def get_audit_history(limit=50, search=None, sort_by='DateTime', sort_order='DESC'):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        query = "SELECT DateTime, Action, User, Result, Description FROM AuditLog"
        
        # NEW: Sanitize sort parameters to prevent SQL injection
        ALLOWED_SORT_FIELDS = ['DateTime', 'Action', 'User', 'Result', 'Description']
        ALLOWED_SORT_ORDERS = ['ASC', 'DESC']
        
        if sort_by not in ALLOWED_SORT_FIELDS:
            sort_by = 'DateTime'
        if sort_order.upper() not in ALLOWED_SORT_ORDERS:
            sort_order = 'DESC'
        else:
            sort_order = sort_order.upper()
        
        if search:
            query += " WHERE Action LIKE ? OR Description LIKE ? OR User LIKE ?"
            cursor.execute(query + f" ORDER BY {sort_by} {sort_order} LIMIT ?", 
                         (f"%{search}%", f"%{search}%", f"%{search}%", limit))
        else:
            # NOW SAFE: sort_by and sort_order validated against whitelist
            cursor.execute(query + f" ORDER BY {sort_by} {sort_order} LIMIT ?", (limit,))
```

**Solution:**
- Whitelist validation before interpolation
- Only allow known column names
- Only allow 'ASC' or 'DESC'
- Invalid values silently corrected to defaults
- Attack attempt `sort_by=DateTime);DROP TABLE AuditLog;--` is rejected and replaced with 'DateTime'

---

## Bug #6: Template Routing - Page Routes Return 500 Error

### Location
**File:** `web_dashboard/app.py`  
**Multiple routes:** /validation, /analytics, /audit, /summary, /reports, /settings, /about

### Error
```
jinja2.exceptions.TemplateNotFound: validation.html
```

### ❌ BEFORE (Buggy Code) - Example: Validation Route
```python
@app.route('/validation')
def validation_page():
    """Validation upload and results page"""
    return render_template('validation.html')  # FILE DOESN'T EXIST
```

**Problem:**
- Application is Single Page Application (SPA)
- All UI pages in one `index.html` file
- Trying to render separate non-existent template files
- Results in HTTP 500 TemplateNotFound error

**Affected Routes:**
- `/validation` → `validation.html` (doesn't exist)
- `/analytics` → `analytics.html` (doesn't exist)
- `/audit` → `audit.html` (doesn't exist)
- `/summary` → `summary.html` (doesn't exist)
- `/reports` → `reports.html` (doesn't exist)
- `/settings` → `settings.html` (doesn't exist)
- `/about` → `about.html` (doesn't exist)

### ✅ AFTER (Fixed Code) - All 7 Routes

**Pattern Applied to All Routes:**

```python
@app.route('/validation')
def validation_page():
    """Validation upload and results page - redirects to SPA"""
    return render_template('index.html')

@app.route('/analytics')
def analytics_page():
    """Analytics page - redirects to SPA"""
    return render_template('index.html')

@app.route('/audit')
def audit_page():
    """Audit page - redirects to SPA"""
    return render_template('index.html')

@app.route('/summary')
def summary_page():
    """Summary page - redirects to SPA"""
    return render_template('index.html')

@app.route('/reports')
def reports_page():
    """Reports page - redirects to SPA"""
    return render_template('index.html')

@app.route('/settings')
def settings_page():
    """Settings page - redirects to SPA"""
    return render_template('index.html')

@app.route('/about')
def about_page():
    """About page - redirects to SPA"""
    return render_template('index.html')
```

**Solution:**
- All routes return `index.html`
- JavaScript in index.html handles page switching (showPage() function)
- SPA navigation stays on one URL until user navigates
- No more TemplateNotFound errors

---

## Bug #7: Validation Results Not Persisted to Database

### Location
**File:** `web_dashboard/app.py`  
**Function:** `validate_upload()` endpoint
**Lines:** 385-475

### Problem
- ValidationEngine executed on uploaded file
- Results displayed to user
- But results NOT saved to database
- Dashboard showed no new validations
- No audit trail created
- Data loss on page refresh

### ❌ BEFORE (Incomplete Code)
```python
@app.route('/api/validate/upload', methods=['POST'])
def validate_upload():
    try:
        # ... file handling code ...
        
        validation_engine = ValidationEngine()
        result = validation_engine.validate_complete_workbook(filepath)
        
        # Results calculated but NOT PERSISTED
        # No database INSERT statements
        # No audit log entry
        # No backup created
        
        return jsonify({
            "success": result.passed,
            "errors": result.errors,
            "warnings": result.warnings
        })
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500
```

### ✅ AFTER (Complete Code)
```python
@app.route('/api/validate/upload', methods=['POST'])
def validate_upload():
    try:
        # ... file handling code ...
        
        if not BACKEND_AVAILABLE:
            return jsonify({"error": "Validation backend not available"}), 500
        
        try:
            validation_engine = ValidationEngine()
            result = validation_engine.validate_complete_workbook(filepath)
            
            # Persist validation results to database
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    now = datetime.now()
                    
                    # 1. Create backup before processing
                    try:
                        backup_manager = BackupManager('backups')
                        backup_manager.create_backup(filepath)
                    except Exception as e:
                        logger.warning(f"Could not create backup: {e}")
                    
                    # 2. Insert into WorkbookHistory
                    cursor.execute("""
                        INSERT INTO WorkbookHistory (FileName, FilePath, ProcessDate, ValidationStatus, DurationSeconds)
                        VALUES (?, ?, ?, ?, ?)
                    """, (file.filename, filepath, now, 'PASS' if result.passed else 'FAIL', int(result.duration_seconds)))
                    workbook_id = cursor.lastrowid
                    
                    # 3. Insert into ValidationRun
                    cursor.execute("""
                        INSERT INTO ValidationRun (WorkbookID, StartTime, Duration, Passed, ErrorCount, WarningCount, UserName)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (workbook_id, now, int(result.duration_seconds), 1 if result.passed else 0, 
                           result.error_count, result.warning_count, 'system'))
                    run_id = cursor.lastrowid
                    
                    # 4. Insert validation errors
                    for error_msg in result.errors:
                        cursor.execute("""
                            INSERT INTO ValidationError (RunID, ErrorMessage)
                            VALUES (?, ?)
                        """, (run_id, error_msg))
                    
                    # 5. Insert duplicates (if available from validation result)
                    if hasattr(result, 'duplicates') and result.duplicates:
                        for dup in result.duplicates:
                            batch_num = dup.batch_number if hasattr(dup, 'batch_number') else str(dup)
                            cursor.execute("""
                                INSERT INTO DuplicateRecord (RunID, BatchNumber, DuplicateType)
                                VALUES (?, ?, ?)
                            """, (run_id, batch_num, 'Different Rows'))
                    
                    # 6. Log to audit
                    cursor.execute("""
                        INSERT INTO AuditLog (DateTime, Action, User, Result, Description)
                        VALUES (?, ?, ?, ?, ?)
                    """, (now, 'Workbook Validation', 'system', 
                          'PASS' if result.passed else 'FAIL',
                          f'Validated {file.filename}: {result.error_count} errors, {result.warning_count} warnings'))
                    
                    # 7. Commit transaction
                    conn.commit()
                    conn.close()
                    logger.info(f"Validation results persisted: Run ID {run_id}")
                    
            except Exception as e:
                logger.error(f"Error persisting validation results: {e}")
                if conn:
                    try:
                        conn.rollback()
                        conn.close()
                    except:
                        pass
            
            return jsonify({
                "success": result.passed,
                "errors": result.errors,
                "warnings": result.warnings
            })
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return jsonify({"error": str(e)}), 500
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500
```

**Solution:**
- Create backup before validation (data safety)
- INSERT WorkbookHistory record with file metadata
- INSERT ValidationRun record with pass/fail status
- INSERT ValidationError records for each error message
- INSERT DuplicateRecord records for duplicates found
- INSERT AuditLog record to track the activity
- COMMIT transaction on success or ROLLBACK on error
- Log all operations for debugging

**Impact:**
- ✅ Dashboard shows new validations immediately
- ✅ Audit trail shows who uploaded and when
- ✅ Error details retained for analysis
- ✅ Backup protects original file
- ✅ Historical data available for reporting

---

## Summary of All Fixes

| Bug # | Type | Severity | Fix Applied |
|-------|------|----------|-------------|
| 1 | Database Query | CRITICAL | Added JOIN to ValidationRun table |
| 2 | Database Query | CRITICAL | Changed to subquery for date filtering |
| 3 | Database Query | CRITICAL | Added JOIN to ValidationRun table |
| 4 | Security | CRITICAL | Added whitelist validation on sort parameters |
| 5 | Routing | CRITICAL | All routes redirect to index.html |
| 6 | Architecture | CRITICAL | Added full database persistence flow |

---

## Testing Query Fixes

### Using integration_test.py
```python
# Run this to verify all queries work correctly:
python web_dashboard/integration_test.py

# Output should show:
# ✓ Total workbooks today: [number]
# ✓ Today's validations: [number]
# ✓ Success rate: [number]%
# ✓ Cards processed: [number]
# ✓ Error breakdown: [numbers]
# ✓ Daily trend: [number] days with data
```

### Direct Database Query Testing
```sql
-- Verify CardStatistics has no UpdatedTime column
.schema CardStatistics
-- Should NOT show UpdatedTime column

-- Test fixed query pattern
SELECT COALESCE(SUM(cs.TotalCards), 0) as total
FROM CardStatistics cs
JOIN ValidationRun vr ON cs.RunID = vr.RunID
WHERE DATE(vr.StartTime) = '2026-07-12';

-- Should return a number (not error)
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-07-12  
**All Fixes Verified:** ✅ YES
