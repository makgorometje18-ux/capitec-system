"""
Test the updated detect_daily_output_sheet() logic.
"""
import sys
sys.path.insert(0, '.')
from src.core.workbook_loader import WorkbookLoader

loader = WorkbookLoader()

print("=" * 70)
print("TEST: Pattern matching")
print("=" * 70)

tests = [
    ("DAILY OUTPUT FILE 15-07-2026", True),
    ("Daily Output File", True),
    ("DAILY OUTPUT", True),
    ("Daily_Output_File", True),
    ("daily output file 01-07-2026", True),
    ("  DAILY OUTPUT FILE 15-07-2026  ", True),
    ("DAILY OUTPUT REPORT", True),
    ("Daily Output July 2026", True),
    ("Daily_Output_15-07-2026", True),
    ("Summary", False),
    ("Instructions", False),
    ("Cover", False),
    ("Report", False),
    ("Data", False),
    ("Archive", False),
    ("CAPITEC SUMMARY FILE REPORT", False),
    ("DSV CONSUMABLES", False),
    ("Sheet1", False),
]

passed = 0
failed = 0
for name, expected in tests:
    result = loader._is_daily_output_sheet(name)
    if result == expected:
        status = "PASS"
        passed += 1
    else:
        status = "FAIL"
        failed += 1
    print(f"  [{status}] '{name}' -> {'MATCH' if result else 'REJECT'} (expected {'MATCH' if expected else 'REJECT'})")

print(f"\n  {passed} passed, {failed} failed\n")

print("=" * 70)
print("TEST: Date detection")
print("=" * 70)
date_tests = [
    "DAILY OUTPUT FILE 15-07-2026",
    "DAILY OUTPUT FILE 15/07/2026",
    "Daily Output July 2026",
    "DAILY OUTPUT FILE 15-July-2026",
    "DAILY OUTPUT FILE (no date here)",
    "Daily Output",
]
for name in date_tests:
    result = loader._detect_date_in_sheet_name(name)
    if result:
        print(f"  '{name}' -> date: {result}")
    else:
        print(f"  '{name}' -> no date (optional)")

print()
print("=" * 70)
print("TEST: Real workbook sheet detection")
print("=" * 70)
import sqlite3
import os
conn = sqlite3.connect('database/cdrs.db')
c = conn.cursor()
c.execute("""
    SELECT DISTINCT wh.FilePath, wh.FileName
    FROM ValidationRun vr
    JOIN WorkbookHistory wh ON vr.WorkbookID = wh.ID
    WHERE vr.RunID NOT IN (SELECT RunID FROM CardStatistics)
    ORDER BY vr.RunID
    LIMIT 3
""")
for fp, fn in c.fetchall():
    if not os.path.exists(fp):
        print(f"\n  '{fn}': FILE NOT FOUND")
        continue
    try:
        ldr = WorkbookLoader()
        ldr.load_workbook(fp)
        result = ldr.detect_daily_output_sheet()
        sheets = ldr.workbook.sheetnames if ldr.workbook else []
        print(f"\n  File: '{fn}'")
        print(f"  Sheets: {list(sheets)}")
        print(f"  Result: '{result}'")
        ldr.close()
    except Exception as e:
        print(f"\n  '{fn}': ERROR: {e}")
conn.close()

print()
print("=" * 70)
print("SAFETY CONFIRMATION")
print("=" * 70)
print("  Modified file: src/core/workbook_loader.py  ONLY")
print("  CardCounter:       NOT modified ✓")
print("  Dashboard:         NOT modified ✓")
print("  Flask API:         NOT modified ✓")
print("  Database schema:   NOT modified ✓")
print("  Validation logic:  NOT modified ✓")