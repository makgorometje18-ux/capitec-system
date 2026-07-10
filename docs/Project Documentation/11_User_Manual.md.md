# Capitec Daily Reconciliation System (CDRS)

# 11_User_Manual.md

**Version:** 1.0

---

# Table of Contents

1. Introduction
2. System Overview
3. System Requirements
4. Starting the Application
5. Dashboard Overview
6. Opening a Workbook
7. Running Validation
8. Understanding Validation Results
9. Fixing Validation Errors
10. Updating the Summary Report
11. Generating Reports
12. Audit History
13. Settings
14. Backup & Restore
15. Troubleshooting
16. Frequently Asked Questions
17. Best Practices
18. Keyboard Shortcuts

---

# 1. Introduction

Welcome to the Capitec Daily Reconciliation System (CDRS).

The application automates the reconciliation of Capitec Daily Output Excel workbooks by validating production data, detecting errors, calculating card quantities, updating the Summary Report, and generating audit reports.

---

# 2. System Overview

The application performs the following tasks:

• Detect duplicate Batch Numbers.

• Detect duplicate Batch Numbers within the same cell.

• Validate No_of_Batches.

• Validate Bag_No formatting.

• Detect blank mandatory fields.

• Count SIM card orders.

• Count Bank card orders.

• Calculate dispatched quantities.

• Update the Capitec Summary Report.

• Highlight errors directly in Excel.

• Generate Duplicate Reports.

• Generate PDF Validation Reports.

• Create automatic backups.

• Maintain a complete audit history.

---

# 3. Starting the Application

Double-click

Capitec-Reconciliation-System.exe

The Dashboard will open automatically.

The application checks:

- Configuration
- Database
- Required folders
- User settings

If successful, the Dashboard will display:

READY

---

# 4. Dashboard

The Dashboard displays:

Workbook

Validation Status

Progress

SIM Orders

Bank Orders

SIM Cards

Bank Cards

Errors

Warnings

Buttons:

- Browse Workbook
- Start Validation
- Update Summary
- Generate PDF
- Audit History
- Settings
- Exit

---

# 5. Opening a Workbook

Step 1

Click

Browse Workbook

Step 2

Select

DAILY OUTPUT FILE.xlsx

Step 3

Click

Open

The application will display:

Workbook Name

Workbook Size

Detected Worksheets

Workbook Status

---

# 6. Running Validation

Click

Start Validation

The application performs:

✓ Backup

✓ Worksheet Detection

✓ Header Validation

✓ Duplicate Detection

✓ Batch Count Validation

✓ Bag Validation

✓ Blank Field Validation

✓ Card Counting

✓ Summary Validation

✓ Report Generation

✓ Audit Logging

Progress is displayed throughout.

---

# 7. Understanding Validation Results

PASS

Displayed when:

No duplicates exist.

No validation errors exist.

Summary updated successfully.

FAIL

Displayed when:

Duplicate Batch Numbers exist.

No_of_Batches is incorrect.

Bag_No is invalid.

Headers are missing.

Mandatory fields are blank.

Summary update is cancelled.

---

# 8. Duplicate Report

If duplicates are found:

A worksheet named

Duplicate Report

is created automatically.

Columns include:

Batch Number

Worksheet

Row

Cell

Occurrences

Description

Suggested Fix

---

# 9. Fixing Errors

Duplicate Batch Numbers

Locate highlighted rows.

Correct the Batch_No.

Save workbook.

Run validation again.

No_of_Batches Errors

Correct No_of_Batches.

Run validation again.

Bag_No Errors

Click

Auto Fix

or manually remove extra apostrophes.

Blank Fields

Complete missing information.

Run validation again.

---

# 10. Excel Highlighting

Green

Validation Passed

Yellow

Warning

Red

Validation Failed

The original workbook formatting is preserved.

---

# 11. Updating the Summary Report

The Summary Report updates only after successful validation.

The application calculates:

SIM Orders

SIM Cards

Bank Orders

Bank Cards

Quantity Dispatched

Quantity In Stock

If validation fails

↓

Update is cancelled automatically.

---

# 12. PDF Reports

Click

Generate PDF

The report includes:

Workbook Information

Validation Summary

Duplicate Summary

Card Totals

Errors

Warnings

Audit Information

Date & Time

---

# 13. Audit History

Click

Audit History

View:

Validation Date

Workbook

Duration

Errors

Warnings

Status

Summary Updated

Users can search by:

Date

Workbook

Validation Result

---

# 14. Settings

Users can configure:

SIM Multiplier

Bank Multiplier

Backup Folder

Report Folder

Log Folder

Auto Backup

Auto PDF

Auto Highlight

Dark Mode

Restore Defaults

---

# 15. Backup & Restore

Before modifying any workbook:

A timestamped backup is created automatically.

Backups are stored in:

backups/

To restore:

1. Open backups folder.

2. Select desired backup.

3. Copy it to the working folder.

---

# 16. Troubleshooting

Workbook will not open

Verify file exists.

Ensure workbook is not already open.

Summary sheet missing

Verify worksheet name begins with:

CAPITEC SUMMARY FILE REPORT

Duplicate detected unexpectedly

Check Batch_No values carefully.

Extra spaces are ignored automatically.

Bag_No validation failed

Ensure only one leading apostrophe exists.

---

# 17. Frequently Asked Questions

Q:

Why was my Summary Report not updated?

A:

One or more validation rules failed.

Correct the errors and run validation again.

---

Q:

Can I undo changes?

A:

Yes.

Restore the workbook from the automatic backup.

---

Q:

Where are reports saved?

A:

reports/

---

Q:

Where are backups saved?

A:

backups/

---

# 18. Best Practices

Always validate before updating the Summary Report.

Review highlighted rows before correcting data.

Keep backup files.

Do not rename required worksheet headers.

Review the Duplicate Report before releasing production files.

Archive reports regularly.

---

# 19. Keyboard Shortcuts

Ctrl + O

Open Workbook

Ctrl + R

Run Validation

Ctrl + P

Generate PDF

Ctrl + H

Audit History

Ctrl + S

Save Workbook

F1

Help

---

# 20. Contact & Support

Application

Capitec Daily Reconciliation System

Version

1.0

For technical support, contact your system administrator or the application developer.

---

End of Document