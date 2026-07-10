# Capitec Daily Reconciliation System (CDRS)

# 05_System_Architecture.md

**Version:** 1.0

---

# 1. Purpose

This document describes the technical architecture of the Capitec Daily Reconciliation System (CDRS). It defines how every component of the application interacts to ensure scalability, maintainability, performance and reliability.

---

# 2. Architecture Goals

The system must:

- Be modular
- Be scalable
- Be maintainable
- Be easy to test
- Be easy to extend
- Be production ready
- Support future modules without rewriting existing code

---

# 3. Architecture Overview

The application shall use a layered architecture.

```
+------------------------------------------------------+
|                    User Interface                    |
+------------------------------------------------------+
|                Application Controller                |
+------------------------------------------------------+
|                Business Logic Layer                  |
+------------------------------------------------------+
|                Validation Engine                     |
+------------------------------------------------------+
|                Excel Processing Layer                |
+------------------------------------------------------+
|                Reporting Engine                      |
+------------------------------------------------------+
|                Database Layer                        |
+------------------------------------------------------+
|                File System Layer                     |
+------------------------------------------------------+
```

---

# 4. Project Structure

```
Capitec-Reconciliation-System

│
├── docs
│
├── src
│
│   ├── app.py
│
│   ├── gui
│   │      dashboard.py
│   │      settings.py
│   │      progress_window.py
│   │      duplicate_window.py
│   │      report_window.py
│   │
│   ├── core
│   │      validator.py
│   │      workbook_loader.py
│   │      duplicate_checker.py
│   │      batch_counter.py
│   │      bag_validator.py
│   │      summary_updater.py
│   │      backup_manager.py
│   │      audit_manager.py
│   │      pdf_generator.py
│   │
│   ├── database
│   │      database.py
│   │
│   ├── models
│   │      workbook.py
│   │      validation.py
│   │      duplicate.py
│   │
│   ├── reports
│   │
│   ├── config
│   │      settings.json
│   │
│   ├── utils
│   │      helpers.py
│   │      logger.py
│   │
│   └── tests
│
├── backups
├── logs
├── reports
├── sample_files
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

# 5. Application Layers

## Layer 1

### User Interface

Responsible for

- Browse Workbook
- Validation Status
- Progress Bar
- Dashboard
- Reports
- Settings
- Audit History

No validation logic shall exist here.

---

## Layer 2

### Controller

Responsible for

- Starting validation
- Loading workbook
- Calling modules
- Updating progress
- Returning results

---

## Layer 3

### Business Logic

Responsible for

- Applying Business Rules
- Decision making
- Workflow management

No Excel code should exist here.

---

## Layer 4

### Validation Engine

Responsible for

Duplicate checking

Batch counting

Bag validation

Blank validation

Header validation

Card type validation

Workbook validation

Returns

PASS

FAIL

Warnings

Errors

---

## Layer 5

### Excel Engine

Responsible for

Reading workbook

Writing workbook

Highlighting cells

Updating summary

Saving workbook

Creating duplicate sheet

Must preserve formatting.

---

## Layer 6

### Reporting Engine

Responsible for

PDF

Duplicate Report

Validation Report

Statistics

Audit Reports

---

## Layer 7

### Database

Responsible for

Audit Log

History

Validation Statistics

User Preferences

---

# 6. Validation Pipeline

```
Workbook

↓

Backup

↓

Load Workbook

↓

Detect Worksheets

↓

Read Headers

↓

Validate Workbook

↓

Duplicate Validation

↓

No_of_Batches Validation

↓

Bag Validation

↓

Blank Validation

↓

Card Count

↓

Summary Validation

↓

Summary Update

↓

Reports

↓

Audit

↓

PASS / FAIL
```

---

# 7. Module Responsibilities

## Workbook Loader

Open workbook

Detect worksheets

Detect headers

Load data

---

## Duplicate Checker

Split Batch_No

Remove spaces

Ignore empty values

Detect

Cell duplicates

Worksheet duplicates

Return Duplicate List

---

## Batch Counter

Read No_of_Batches

Read Batch_No

Compare totals

Return PASS / FAIL

---

## Bag Validator

Validate apostrophes

Auto Fix

Highlight errors

---

## Card Counter

SIM

Orders

Cards

DMCCLS

Orders

Cards

Totals

---

## Summary Updater

Read Summary Sheet

Calculate dispatch

Calculate stock

Update worksheet

Verify balances

---

## Backup Manager

Timestamp backup

Restore backup

Delete old backups (future)

---

## Audit Manager

Record

Validation

Updates

Errors

Duration

User

Workbook

---

## Report Generator

PDF

Duplicate Sheet

Summary Report

Statistics

---

# 8. Configuration

The application shall use

settings.json

Example

```
SIM_MULTIPLIER = 200

BANK_MULTIPLIER = 300

AUTO_BACKUP = TRUE

AUTO_HIGHLIGHT = TRUE

REPORT_FOLDER = reports

BACKUP_FOLDER = backups

LOG_FOLDER = logs
```

---

# 9. Logging

Every action shall be logged.

Example

```
09:00

Workbook Loaded

09:00:02

Backup Created

09:00:05

Duplicate Check Started

09:00:08

Duplicate Found

Batch

30231

Row

15

09:00:20

Summary Updated

09:00:25

Validation Completed
```

---

# 10. Error Handling

Application must never crash.

Handle

Workbook missing

Worksheet missing

Headers missing

Workbook open

Permission denied

Corrupt workbook

Unexpected exception

Log every error.

---

# 11. Performance

Maximum workbook

50,000+

rows

Validation

<60 seconds

Memory efficient

Responsive UI

No freezing

Use background threads.

---

# 12. Security

Read only until validation completes.

Create backup before write.

Never overwrite without backup.

Audit every modification.

---

# 13. Scalability

Future support

Multiple customers

Barcode scanners

Cloud storage

Email notifications

Power BI

Automatic scheduling

REST API

User Login

Role permissions

---

# 14. Design Principles

Single Responsibility Principle

Open/Closed Principle

Dependency Injection

Loose Coupling

High Cohesion

Clean Architecture

Reusable Components

Testable Modules

---

# 15. Acceptance Criteria

The architecture shall

✓ Separate UI from business logic

✓ Separate validation from Excel processing

✓ Support future modules

✓ Support automated testing

✓ Be maintainable

✓ Be production ready

✓ Be scalable

✓ Be suitable for packaging as a Windows executable

---

End of Document