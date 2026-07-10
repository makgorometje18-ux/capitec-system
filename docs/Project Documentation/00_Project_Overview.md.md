# Capitec Daily Reconciliation System (CDRS)
## Software Requirements Specification (PROJECT_REQUIREMENTS.md)

> Version: 1.0

# 1. Project Overview
Build a professional Windows desktop application to automate reconciliation of Capitec Daily Output Excel workbooks.

## Objectives
- Eliminate manual reconciliation.
- Detect duplicate batch numbers.
- Validate No_of_Batches against Batch_No.
- Validate Bag_No formatting.
- Separate SIM and Bank Card orders.
- Automatically update the Capitec Summary File Report.
- Produce audit logs, PDF reports and backups.
- Preserve workbook formatting.

# 2. Technology
- Python 3.13+
- PySide6
- openpyxl
- pandas
- SQLite
- reportlab
- logging
- pytest
- PyInstaller

# 3. Functional Requirements

## 3.1 Workbook Detection
Automatically detect worksheets beginning with:
- DAILY OUTPUT FILE
- CAPITEC SUMMARY FILE REPORT

## 3.2 Backup
Before any modification:
- Create timestamped backup.
- Never overwrite backups.

## 3.3 Duplicate Batch Validation
Read column Batch_No.
Split values using "|".
Detect:
- duplicates within the same cell
- duplicates across rows
Report:
- batch number
- worksheet
- row
- cell
- occurrences

Highlight offending rows red.

Create a worksheet named "Duplicate Report".

## 3.4 No_of_Batches Validation
Compare No_of_Batches with number of batch numbers in Batch_No.
Example:
No_of_Batches=3
Batch_No=123|124|125
PASS

Mismatch:
Expected
Actual
Cell
Row

## 3.5 Bag_No Validation
Correct:
'00012345

Invalid:
''00012345
'''00012345

Provide one-click automatic fix.

## 3.6 Blank Field Validation
Check:
- Branch_Code
- Branch_Name
- Card_Type
- Waybill_No
- Batch_No
- Bag_No
- No_of_Batches

## 3.7 Card Counting
Card_Type=SIM
Orders=sum(No_of_Batches)
Cards=Orders*200

Card_Type=DMCCLS
Orders=sum(No_of_Batches)
Cards=Orders*300

Multipliers configurable.

## 3.8 Summary Update
Locate:
C-Connect batch
and row beginning P_

Update:
Quantity Dispatched
Quantity In Stock

Validate previous balance before update.

## 3.9 Excel Highlighting
Errors = Red
Warnings = Yellow
Passed = Green

## 3.10 Audit Log
Store:
Date
Time
Workbook
Duration
Errors
Warnings
SIM Orders
Bank Orders
SIM Cards
Bank Cards
User
Validation Result

## 3.11 PDF Report
Include:
Workbook
Date
Duplicates
Batch Errors
Bag Errors
SIM Summary
Bank Summary
PASS/FAIL

## 3.12 PASS / FAIL
Green:
VALIDATION PASSED

Red:
VALIDATION FAILED

# 4. GUI

Dashboard must include:
- Browse Workbook
- Progress Bar
- Validation Status
- Error Count
- Passed Count
- Start Validation
- Fix Errors
- Update Summary
- Generate PDF
- Audit History
- Settings
- Exit

# 5. Workflow

Select Workbook
→ Backup
→ Detect Sheets
→ Validate
→ Highlight
→ Duplicate Report
→ Count Cards
→ Update Summary
→ Generate PDF
→ Audit Log
→ PASS/FAIL

# 6. Error Handling

Handle:
- workbook open
- missing sheet
- missing headers
- protected workbook
- permission denied
- invalid workbook

Never crash.

# 7. Settings
SIM_MULTIPLIER=200
BANK_MULTIPLIER=300
AUTO_BACKUP=true
AUTO_HIGHLIGHT=true

# 8. Testing
Unit tests
Integration tests
Sample valid workbook
Sample invalid workbook

# 9. Future Enhancements
- Barcode scanner integration
- User login
- Email notifications
- Automatic folder monitoring
- Power BI integration
- Cloud synchronization
- Automatic updates

# 10. Deliverables
- Python source code
- Windows executable
- README
- requirements.txt
- User Manual
- SQLite database
- Tests
- Installer

