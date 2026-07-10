# Capitec Daily Reconciliation System (CDRS)
# Software Requirements Specification (SRS)
Version: 1.0

## 1. Executive Summary
The Capitec Daily Reconciliation System (CDRS) is a Windows desktop application that automates the reconciliation of Capitec Daily Output Excel workbooks. The system replaces manual validation with automated business rules, reporting, highlighting, stock calculations and audit logging.

## 2. Business Problem
Current reconciliation is manual and can result in:
- Duplicate Batch Numbers
- Incorrect No_of_Batches values
- Incorrect Bag_No formatting
- Manual stock update errors
- Missing audit trail
- Time-consuming reconciliation

## 3. Project Objectives
- Reduce reconciliation time to under 2 minutes.
- Eliminate duplicate Batch Numbers.
- Validate every production record automatically.
- Prevent incorrect Summary Report updates.
- Produce audit evidence for every run.

## 4. Scope
The application shall:
- Open existing Excel workbooks.
- Detect Daily Output and Capitec Summary worksheets automatically.
- Validate workbook contents.
- Highlight errors in Excel.
- Create Duplicate Report worksheet.
- Count SIM and DMCCLS orders.
- Update Summary Report.
- Generate PDF reports.
- Create timestamped backups.
- Maintain SQLite audit history.

## 5. Business Rules

BR001: Batch numbers must be unique across the worksheet.
BR002: Batch numbers must not repeat inside a single Batch_No cell.
BR003: Batch_No values are separated using '|'.
BR004: No_of_Batches must equal the number of values found in Batch_No.
BR005: Bag_No must contain exactly one leading apostrophe.
BR006: Card_Type SIM = Orders × 200.
BR007: Card_Type DMCCLS = Orders × 300.
BR008: Summary Report must not update if validation fails.
BR009: Backup must be created before modification.
BR010: Every reconciliation must be logged.

## 6. Functional Requirements

### Workbook Detection
Automatically locate:
- Sheet beginning with DAILY OUTPUT FILE
- Sheet beginning with CAPITEC SUMMARY FILE REPORT

### Duplicate Validation
Read Batch_No column.
Split by '|'.
Detect:
- Duplicate in same cell.
- Duplicate across worksheet.
Report:
- Batch Number
- Worksheet
- Row
- Cell
- Occurrences

### No_of_Batches Validation
Compare No_of_Batches with the number of batch numbers inside Batch_No.

### Bag_No Validation
Accept:
'00012345

Reject:
''00012345
'''00012345

Provide one-click fix.

### Blank Validation
Validate:
- Branch_Code
- Branch_Name
- Waybill_No
- Batch_No
- Bag_No
- Card_Type
- No_of_Batches

### Card Counting
SIM:
Orders=sum(No_of_Batches)
Cards=Orders×200

DMCCLS:
Orders=sum(No_of_Batches)
Cards=Orders×300

### Summary Update
Update:
- Quantity Dispatched
- Quantity In Stock

Only if all validations pass.

### Excel Highlighting
Errors=Red
Warnings=Yellow
Passed=Green

### Duplicate Report
Generate worksheet named Duplicate Report containing:
Batch Number, Sheet, Row, Cell, Error Description.

### Audit Log
Store:
Date, Time, Workbook, User, Duration, Validation Result, Errors, SIM Orders, Bank Orders, Cards Count.

### PDF Report
Generate a reconciliation report summarizing:
Validation results, duplicates, totals, PASS/FAIL.

## 7. User Interface
Dashboard shall contain:
- Browse Workbook
- Start Validation
- Progress Bar
- Validation Status
- Error Summary
- Update Summary
- Generate PDF
- Audit History
- Settings
- Exit

## 8. Workflow
Open Workbook
-> Backup
-> Detect Sheets
-> Validate
-> Highlight Errors
-> Duplicate Report
-> Count Cards
-> Update Summary
-> PDF
-> Audit Log
-> PASS/FAIL

## 9. Non-functional Requirements
- Windows 10/11
- Offline operation
- Preserve Excel formatting
- Support 50,000+ rows
- Complete within 2 minutes
- Modular architecture
- Exception handling
- Logging
- Type hints
- Unit tests

## 10. Future Enhancements
- Barcode scanner integration
- User login
- Email notifications
- Folder monitoring
- Power BI dashboard
- Automatic updates
- Cloud synchronization

## 11. Deliverables
- Python source code
- Windows EXE
- README
- requirements.txt
- SQLite database
- User Manual
- Test suite
- Installer
