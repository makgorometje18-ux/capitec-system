# Capitec Daily Reconciliation System (CDRS)

# 08_Module_Design.md

**Version:** 1.0

---

# 1. Purpose

This document defines every software module that forms part of the Capitec Daily Reconciliation System (CDRS).

Each module has a single responsibility, making the application easier to maintain, test, and extend.

---

# 2. Module Architecture

```
Application

│

├── User Interface
│
├── Controller
│
├── Workbook Loader
│
├── Validation Engine
│      │
│      ├── Header Validator
│      ├── Duplicate Checker
│      ├── Batch Validator
│      ├── Bag Validator
│      ├── Blank Validator
│      ├── Card Validator
│      └── Business Rules Engine
│
├── Card Counter
│
├── Summary Updater
│
├── Excel Highlighter
│
├── Duplicate Report Generator
│
├── PDF Report Generator
│
├── Audit Logger
│
├── Backup Manager
│
├── Database Manager
│
└── Settings Manager
```

---

# 3. Main Application Module

## File

app.py

### Responsibilities

- Start application
- Load configuration
- Open Dashboard
- Initialise database
- Handle unexpected exceptions
- Close application safely

---

# 4. Dashboard Module

## File

dashboard.py

### Responsibilities

- Display dashboard
- Open workbook
- Display validation status
- Display statistics
- Display buttons
- Display progress

---

# 5. Workbook Loader Module

## File

workbook_loader.py

### Responsibilities

- Open Excel workbook
- Verify workbook exists
- Verify workbook is readable
- Detect worksheets
- Detect headers
- Return workbook object

### Inputs

Workbook path

### Outputs

Workbook object

Validation status

---

# 6. Header Validator Module

## File

header_validator.py

### Responsibilities

Verify required headers

Required headers

- Creation_Date
- Branch_Code
- Branch_Name
- Card_Type
- No_of_Batches
- Waybill_No
- Batch_No
- Bag_No

Return missing headers

---

# 7. Duplicate Checker Module

## File

duplicate_checker.py

### Responsibilities

Read every Batch_No

Split using "|"

Trim spaces

Ignore empty values

Detect

- Duplicate inside one cell
- Duplicate across worksheet

Return

Duplicate list

Duplicate count

Duplicate report

---

# 8. Batch Validator Module

## File

batch_validator.py

### Responsibilities

Read

No_of_Batches

Read

Batch_No

Count batches

Compare totals

Return

PASS

FAIL

Error description

---

# 9. Bag Validator Module

## File

bag_validator.py

### Responsibilities

Read Bag_No

Verify exactly one apostrophe

Auto-fix multiple apostrophes

Highlight errors

Return validation result

---

# 10. Blank Validator Module

## File

blank_validator.py

### Responsibilities

Detect blank mandatory fields

Check

Branch_Code

Branch_Name

Card_Type

Waybill_No

Batch_No

Bag_No

No_of_Batches

Return error list

---

# 11. Business Rules Engine

## File

business_rules.py

### Responsibilities

Execute all validation rules

BR-001

↓

BR-015

Return

Overall PASS

Overall FAIL

Warnings

Errors

---

# 12. Card Counter Module

## File

card_counter.py

### Responsibilities

Calculate

SIM Orders

SIM Cards

Bank Orders

Bank Cards

Totals

Formula

SIM

Orders × 200

DMCCLS

Orders × 300

---

# 13. Summary Updater Module

## File

summary_updater.py

### Responsibilities

Locate Summary Sheet

Read stock

Read dispatch

Update

Quantity Dispatched

Quantity In Stock

Verify calculations

Save workbook

---

# 14. Excel Highlighter Module

## File

excel_highlighter.py

### Responsibilities

Highlight

Duplicate rows

Header errors

Bag errors

Blank fields

Colours

Green

Yellow

Red

---

# 15. Duplicate Report Module

## File

duplicate_report.py

### Responsibilities

Create worksheet

Duplicate Report

Include

Batch Number

Worksheet

Row

Cell

Occurrences

Description

Suggested Fix

---

# 16. PDF Report Generator

## File

report_generator.py

### Responsibilities

Generate

Validation Report

Duplicate Report

Summary Report

Statistics

Audit Report

Save PDF

---

# 17. Backup Manager

## File

backup_manager.py

### Responsibilities

Create backup

Timestamp backup

Restore backup

Verify backup success

---

# 18. Audit Logger

## File

audit_logger.py

### Responsibilities

Record

Workbook

Validation

Errors

Warnings

Summary update

Duration

User

Save to database

---

# 19. Database Manager

## File

database.py

### Responsibilities

Open SQLite

Read data

Write data

Execute queries

Backup database

Close connection

---

# 20. Settings Manager

## File

settings_manager.py

### Responsibilities

Read settings

Save settings

Reset defaults

Load configuration

---

# 21. Logging Module

## File

logger.py

### Responsibilities

Record

Information

Warnings

Errors

Debug messages

Application startup

Application shutdown

---

# 22. Helper Module

## File

helpers.py

### Responsibilities

Shared utility functions

Date formatting

String cleaning

Batch splitting

File utilities

Excel utilities

---

# 23. Module Communication

```
Dashboard

↓

Workbook Loader

↓

Header Validator

↓

Duplicate Checker

↓

Batch Validator

↓

Bag Validator

↓

Blank Validator

↓

Business Rules Engine

↓

Card Counter

↓

Summary Updater

↓

Excel Highlighter

↓

Duplicate Report

↓

PDF Generator

↓

Audit Logger

↓

Database

↓

Dashboard
```

---

# 24. Error Handling

Each module shall

Catch exceptions

Log errors

Return meaningful messages

Never crash the application

---

# 25. Future Modules

Future versions may include

- Barcode Scanner Module
- Email Notification Module
- Power BI Export Module
- User Authentication Module
- Cloud Synchronisation Module
- Automatic Folder Monitoring Module
- AI Error Detection Module
- Scheduler Module
- REST API Module

---

# 26. Acceptance Criteria

Every module shall

✓ Have a single responsibility

✓ Be independently testable

✓ Be reusable

✓ Produce meaningful error messages

✓ Log failures

✓ Be documented

✓ Support future enhancements

✓ Follow clean architecture principles

---

End of Document