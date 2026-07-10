# Capitec Daily Reconciliation System (CDRS)

# 07_UI_UX_Design.md

**Version:** 1.0

---

# 1. Purpose

This document defines the complete User Interface (UI) and User Experience (UX) design for the Capitec Daily Reconciliation System (CDRS).

The objective is to create a modern, professional, easy-to-use Windows desktop application that enables users to complete daily reconciliation with minimal training.

---

# 2. Design Principles

The application shall be:

- Clean
- Professional
- Responsive
- Easy to navigate
- Fast
- Minimal clicks
- Easy to understand
- Consistent throughout

---

# 3. Colour Standards

| Status | Colour |
|----------|---------|
| Success | Green |
| Error | Red |
| Warning | Orange |
| Information | Blue |
| Background | White |
| Sidebar | Dark Blue |

---

# 4. Main Dashboard

When the application opens, the Dashboard shall be displayed.

------------------------------------------------------------

CAPITEC DAILY RECONCILIATION SYSTEM

------------------------------------------------------------

Company Logo

Workbook

[ Browse Workbook ]

Selected Workbook

DAILY OUTPUT FILE 30-06-2026.xlsx

------------------------------------------------------------

Validation Status

Ready

Progress

0%

------------------------------------------------------------

Summary

SIM Orders

0

Bank Orders

0

SIM Cards

0

Bank Cards

0

Errors

0

Warnings

0

------------------------------------------------------------

Buttons

Start Validation

Update Summary

Generate PDF

Audit History

Settings

Exit

------------------------------------------------------------

---

# 5. Navigation

Navigation shall consist of:

Dashboard

Validation Report

Duplicate Report

Audit History

Settings

About

---

# 6. Browse Workbook

User clicks

Browse Workbook

↓

Windows File Dialog opens

↓

User selects workbook

↓

Workbook information displayed

Filename

Workbook size

Created Date

Modified Date

Detected Worksheets

---

# 7. Validation Screen

When validation begins

Display

Progress Bar

Current Task

Elapsed Time

Estimated Remaining Time

Validation Log

Example

Loading Workbook

Checking Headers

Checking Duplicates

Checking No_of_Batches

Checking Bag Numbers

Counting Cards

Updating Summary

Generating PDF

Saving Audit

Completed

---

# 8. Progress Bar

Example

██████████░░░░░░░░

55%

Current Task

Checking Duplicate Batch Numbers

---

# 9. Validation Results

PASS Example

Green Banner

VALIDATION PASSED

No duplicate Batch Numbers found.

Workbook is ready.

Summary successfully updated.

FAIL Example

Red Banner

VALIDATION FAILED

Duplicate Batch Numbers Found

No_of_Batches Errors

Bag Number Errors

Summary NOT Updated

---

# 10. Duplicate Report Screen

Table Columns

Batch Number

Worksheet

Row

Cell

Occurrences

Description

Status

Double-clicking a row shall highlight the corresponding row in Excel.

---

# 11. Validation Report Screen

Display

Total Rows

Rows Passed

Rows Failed

Duplicates

Bag Errors

Header Errors

Warnings

Validation Time

Validation Score

Example

Validation Score

98%

Workbook Status

READY FOR PROCESSING

---

# 12. Summary Update Screen

Display

SIM Orders

SIM Cards

Bank Orders

Bank Cards

Previous Stock

Quantity Dispatched

Remaining Stock

Button

Update Summary

Confirmation Dialog

Are you sure you want to update the Summary Report?

YES

NO

---

# 13. Audit History Screen

Columns

Date

Workbook

Duration

Errors

Warnings

Result

Summary Updated

Search Filters

Date

Workbook

Status

Buttons

Export PDF

Export Excel

Delete Record (Administrator Only)

---

# 14. Settings Screen

General Settings

SIM Multiplier

Default

200

Bank Multiplier

Default

300

Checkboxes

Enable Auto Backup

Enable Auto Highlight

Enable Auto PDF

Enable Audit Log

Enable Dark Mode

Folders

Backup Folder

Report Folder

Log Folder

Buttons

Save

Cancel

Restore Defaults

---

# 15. About Screen

Application Name

Version

Developer

Company

Copyright

System Information

Database Version

---

# 16. Notifications

Information

Blue

Validation Started

Success

Green

Validation Completed Successfully

Warning

Orange

Workbook Contains Warnings

Error

Red

Validation Failed

---

# 17. Error Messages

Examples

Workbook Not Found

Summary Worksheet Missing

Duplicate Batch Number Detected

Header Missing

Bag_No Invalid

No_of_Batches Incorrect

Permission Denied

---

# 18. Keyboard Shortcuts

Ctrl + O

Open Workbook

Ctrl + S

Save Workbook

Ctrl + P

Generate PDF

Ctrl + R

Run Validation

Ctrl + H

Audit History

F1

Help

---

# 19. Future Dashboard Widgets

Validation Trend

Daily Statistics

Monthly Statistics

Duplicate Trend

Most Common Errors

Average Validation Time

Last Backup

Recent Workbooks

---

# 20. Acceptance Criteria

The UI shall:

✓ Be easy to navigate.

✓ Clearly display validation progress.

✓ Clearly display PASS or FAIL.

✓ Highlight important information.

✓ Allow users to operate the application with minimal training.

✓ Remain responsive during validation.

✓ Support future enhancements without redesign.

---

# Future Enhancements

The UI should support:

- User Login
- Role-Based Permissions
- Barcode Scanner Status
- Automatic Folder Monitoring
- Email Notifications
- Power BI Integration
- Multi-Client Support
- Live Dashboard
- Automatic Updates

---

End of Document