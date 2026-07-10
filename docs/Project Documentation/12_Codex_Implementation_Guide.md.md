Document 12
12_Codex_Implementation_Guide.md
# Capitec Daily Reconciliation System (CDRS)

# 12_Codex_Implementation_Guide.md

Version: 1.0

---

# Purpose

This document is the implementation blueprint for AI coding assistants (such as Codex) and software developers. It defines the technologies, coding standards, project structure, implementation order, and acceptance criteria for building the Capitec Daily Reconciliation System (CDRS).

---

# 1. Project Objective

Develop a professional Windows desktop application that automates reconciliation of Capitec Daily Output Excel workbooks.

The application shall:

- Detect duplicate Batch Numbers.
- Detect duplicates inside a single Batch_No cell.
- Validate No_of_Batches.
- Validate Bag_No formatting.
- Detect blank mandatory fields.
- Count SIM and DMCCLS orders.
- Calculate dispatched card quantities.
- Update the Capitec Summary File Report.
- Highlight errors in Excel.
- Generate Duplicate Reports.
- Generate PDF reports.
- Create automatic backups.
- Maintain audit logs.
- Display PASS/FAIL validation results.

---

# 2. Technology Stack

Programming Language

Python 3.12+

GUI

PySide6 (Qt)

Excel Processing

openpyxl

Database

SQLite3

Reporting

ReportLab

Packaging

PyInstaller

Configuration

JSON

Logging

Python logging module

Testing

pytest

Linting

ruff

Formatting

black

---

# 3. Required Project Structure

Capitec-Reconciliation-System/

app.py

requirements.txt

README.md

LICENSE

/config

settings.json

/core

workbook_loader.py

header_validator.py

duplicate_checker.py

batch_validator.py

bag_validator.py

blank_validator.py

card_counter.py

summary_updater.py

backup_manager.py

excel_highlighter.py

duplicate_report.py

audit_logger.py

report_generator.py

settings_manager.py

business_rules.py

/gui

dashboard.py

progress_dialog.py

settings_dialog.py

report_window.py

duplicate_window.py

about_window.py

/database

database.py

schema.sql

/models

validation_result.py

duplicate_record.py

summary_record.py

audit_record.py

/utils

helpers.py

constants.py

logger.py

/tests

/docs

/backups

/logs

/reports

/sample_files

---

# 4. Development Order

Phase 1

Project setup

Phase 2

Workbook Loader

Phase 3

Header Validator

Phase 4

Duplicate Checker

Phase 5

Batch Validator

Phase 6

Bag Validator

Phase 7

Blank Validator

Phase 8

Business Rules Engine

Phase 9

Card Counter

Phase 10

Summary Updater

Phase 11

Excel Highlighter

Phase 12

Duplicate Report Generator

Phase 13

Audit Logger

Phase 14

PDF Report Generator

Phase 15

Database

Phase 16

GUI

Phase 17

Testing

Phase 18

Packaging

---

# 5. Coding Standards

Use:

- Type hints
- Dataclasses where appropriate
- Docstrings for all public classes and functions
- Small, focused functions
- Dependency injection where practical
- Exception handling throughout
- Logging instead of print()
- Constants instead of hardcoded values

Follow:

PEP 8

---

# 6. Business Rules

Implement every rule described in:

03_Business_Rules.md

No business rule may be omitted.

No assumptions may be made without updating the documentation.

---

# 7. Excel Rules

Never modify workbook formatting unless explicitly required.

Always preserve:

- Fonts
- Borders
- Colours
- Formulas
- Column widths
- Row heights
- Merged cells

Only update:

- Highlight colours
- Duplicate Report sheet
- Summary Report values

---

# 8. Validation Workflow

User selects workbook

↓

Backup workbook

↓

Load workbook

↓

Locate worksheets

↓

Validate headers

↓

Validate mandatory fields

↓

Validate Batch_No

↓

Validate duplicates

↓

Validate No_of_Batches

↓

Validate Bag_No

↓

Count cards

↓

Generate reports

↓

Update Summary

↓

Save workbook

↓

Audit database

↓

Display PASS / FAIL

---

# 9. Error Handling

The application must never terminate unexpectedly.

All exceptions shall:

- Be caught
- Be logged
- Be displayed to the user with meaningful messages
- Preserve the original workbook

---

# 10. Performance Targets

Support:

50,000+

rows

Validation time

Less than 60 seconds

Workbook loading

Less than 10 seconds

Memory usage

Efficient

User Interface

Responsive

---

# 11. Security

Before updating any workbook:

Create timestamped backup.

Do not overwrite backups.

Protect audit history.

Prevent duplicate Summary updates.

---

# 12. Database Requirements

Use SQLite.

Tables:

- WorkbookHistory
- ValidationRun
- DuplicateRecord
- ValidationError
- SummaryUpdate
- CardStatistics
- AuditLog
- Settings

Implement indexes.

Use transactions where appropriate.

---

# 13. Reporting

Generate:

Duplicate Report worksheet

Validation PDF

Audit Log

Summary Report

Statistics

Future:

Excel Dashboard

Monthly Reports

---

# 14. GUI Requirements

Dashboard

Browse Workbook

Validation Button

Progress Bar

Statistics Panel

Duplicate Window

Audit History

Settings

About

Dark Mode support

---

# 15. Testing Requirements

Unit Tests

Integration Tests

Performance Tests

Regression Tests

User Acceptance Tests

Target Coverage

80%+

---

# 16. Build Requirements

Generate:

Windows executable

Capitec-Reconciliation-System.exe

Packaging Tool

PyInstaller

---

# 17. Deliverables

The completed project shall include:

✔ Python source code

✔ Windows executable

✔ SQLite database

✔ Documentation

✔ README

✔ User Manual

✔ Installer

✔ Unit tests

✔ Sample Excel files

✔ Audit reports

✔ PDF reports

---

# 18. Future Roadmap

Version 2.0

- Barcode Scanner Integration
- Folder Monitoring
- Email Notifications
- User Login
- Role-Based Security
- Power BI Integration
- SharePoint Integration
- Automatic Updates
- Cloud Synchronisation

Version 3.0

- AI-assisted anomaly detection
- Web dashboard
- Multi-user support
- API integration
- Mobile companion application

---

# 19. Definition of Done

The project is complete when:

✓ All business rules are implemented.

✓ All tests pass.

✓ Validation accuracy is 100%.

✓ Duplicate detection is accurate.

✓ Summary updates are correct.

✓ Reports generate successfully.

✓ Excel formatting is preserved.

✓ Database records are created correctly.

✓ Application is packaged as a Windows executable.

✓ User documentation is complete.

---

# 20. Final Instruction for Codex

Codex (or any developer) must implement the application strictly according to the documentation set:

- 00_Project_Overview.md
- 01_Executive_Summary.md
- 02_Software_Requirements_Specification.md
- 03_Business_Rules.md
- 04_Excel_Workbook_Specification.md
- 05_System_Architecture.md
- 06_Database_Design.md
- 07_UI_UX_Design.md
- 08_Module_Design.md
- 09_Testing_Strategy.md
- 10_Deployment_Guide.md
- 11_User_Manual.md
- 12_Codex_Implementation_Guide.md

If implementation conflicts with the documentation, the documentation takes precedence until formally revised.

---

End of Document