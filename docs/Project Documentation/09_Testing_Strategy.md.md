# Capitec Daily Reconciliation System (CDRS)

# 09_Testing_Strategy.md

**Version:** 1.0

---

# 1. Purpose

This document defines the testing strategy for the Capitec Daily Reconciliation System (CDRS). The objective is to ensure the application is accurate, reliable, stable, and production-ready before deployment.

---

# 2. Testing Objectives

The testing process shall verify that:

- All business rules work correctly.
- Duplicate detection is 100% accurate.
- Summary updates are correct.
- Excel formatting is preserved.
- Reports are generated correctly.
- The application remains stable under heavy workloads.
- No data corruption occurs.

---

# 3. Testing Levels

The following testing levels shall be performed:

- Unit Testing
- Integration Testing
- System Testing
- User Acceptance Testing (UAT)
- Regression Testing
- Performance Testing

---

# 4. Unit Testing

Each module shall be tested independently.

Modules:

- Workbook Loader
- Header Validator
- Duplicate Checker
- Batch Validator
- Bag Validator
- Blank Validator
- Card Counter
- Summary Updater
- Excel Highlighter
- Duplicate Report Generator
- PDF Report Generator
- Audit Logger
- Database Manager
- Backup Manager
- Settings Manager

---

# 5. Integration Testing

Verify interaction between modules.

Examples:

Workbook Loader → Duplicate Checker

Duplicate Checker → Report Generator

Card Counter → Summary Updater

Summary Updater → Audit Logger

Dashboard → Validation Engine

---

# 6. System Testing

The complete application shall be tested using real production workbooks.

The following workflow shall be verified:

Open Workbook

↓

Backup Created

↓

Validation

↓

Highlight Errors

↓

Generate Reports

↓

Update Summary

↓

Audit Log

↓

PASS / FAIL

---

# 7. User Acceptance Testing (UAT)

The application shall be tested by Shipping & Preparation users.

Users must verify:

- Ease of use
- Accuracy
- Performance
- Report quality
- Error messages
- Workflow

---

# 8. Performance Testing

The application shall support:

- 50,000+ rows
- Large Batch_No fields
- Thousands of duplicate checks
- Multiple reports
- Large audit history

Target:

Validation < 60 seconds

Memory usage stable

No application freezing

---

# 9. Regression Testing

Whenever a new feature is added:

- Existing validation rules must still pass.
- Existing reports must still work.
- Existing database functions must remain unchanged.
- Existing UI functions must remain unchanged.

---

# 10. Test Data

The following sample workbooks shall be prepared.

Workbook A

Clean workbook

Expected Result

PASS

---

Workbook B

Duplicate Batch_No in same cell

Expected Result

FAIL

---

Workbook C

Duplicate Batch_No across rows

Expected Result

FAIL

---

Workbook D

Incorrect No_of_Batches

Expected Result

FAIL

---

Workbook E

Multiple apostrophes in Bag_No

Expected Result

FAIL

Auto Fix Available

---

Workbook F

Missing Header

Expected Result

FAIL

---

Workbook G

Blank mandatory fields

Expected Result

FAIL

---

Workbook H

Mixed errors

Expected Result

FAIL

---

# 11. Business Rule Test Cases

## BR-001 Worksheet Detection

Input:

Workbook contains Daily Output and Summary sheets.

Expected Result:

PASS

---

Workbook missing Summary sheet.

Expected Result:

FAIL

---

## BR-002 Header Validation

All required headers exist.

PASS

Header missing.

FAIL

---

## BR-003 Duplicate Checker

Batch_No

1001|1002|1003

PASS

Batch_No

1001|1002|1002

FAIL

---

Two rows

1005

1005

FAIL

---

## BR-004 Batch Count

No_of_Batches

3

Batch_No

1001|1002|1003

PASS

No_of_Batches

2

Batch_No

1001|1002|1003

FAIL

---

## BR-005 Bag Validation

'0001234

PASS

''0001234

FAIL

---

## BR-006 Card Type

SIM

PASS

DMCCLS

PASS

CARD

FAIL

---

## BR-007 Blank Fields

Blank Branch_Name

FAIL

Blank Waybill_No

FAIL

Blank Batch_No

FAIL

---

# 12. Summary Update Testing

Verify:

Quantity Dispatched updated correctly.

Quantity In Stock updated correctly.

Previous values retained if validation fails.

No duplicate updates.

---

# 13. Excel Highlight Testing

Duplicate Rows

Red

Warnings

Yellow

Passed Rows

Green

Formatting preserved.

---

# 14. PDF Testing

Verify PDF contains:

- Workbook Name
- Date
- Validation Result
- Duplicate Summary
- Card Totals
- Errors
- Warnings
- Audit Information

---

# 15. Audit Testing

Verify:

Every validation is recorded.

Every summary update is recorded.

Every error is logged.

Every report generation is logged.

---

# 16. Backup Testing

Verify:

Backup created before modification.

Timestamp correct.

Backup can be restored.

Original workbook remains unchanged.

---

# 17. Database Testing

Verify:

Records inserted correctly.

Queries return expected data.

Audit history searchable.

Settings persist.

No duplicate database records.

---

# 18. User Interface Testing

Verify:

Buttons work.

Progress bar updates.

Status messages display correctly.

Dialogs open.

Settings save correctly.

Application closes safely.

---

# 19. Failure Scenarios

Test:

Workbook missing.

Worksheet missing.

Workbook read-only.

Workbook corrupted.

Permission denied.

Database unavailable.

Unexpected exception.

Application shall never crash.

---

# 20. Acceptance Criteria

The application shall be accepted when:

✓ All business rules pass testing.

✓ Duplicate detection accuracy is 100%.

✓ No_of_Batches validation is correct.

✓ Bag_No validation works correctly.

✓ Summary updates are accurate.

✓ Reports are generated successfully.

✓ Audit logs are complete.

✓ Backups are created successfully.

✓ Excel formatting is preserved.

✓ No critical defects remain.

---

# 21. Test Deliverables

The testing phase shall produce:

- Test Plan
- Test Cases
- Test Results
- Defect Log
- User Acceptance Report
- Performance Report
- Final Test Sign-Off

---

End of Document