# Capitec Daily Reconciliation System (CDRS)

# 10_Deployment_Guide.md

Version: 1.0

---

# 1. Purpose

This document describes the deployment procedure for the Capitec Daily Reconciliation System (CDRS).

It explains how the application will be installed, configured, maintained, updated, and supported in a production environment.

---

# 2. Deployment Objectives

The deployment shall:

- Install the application successfully.
- Preserve user settings.
- Create required folders.
- Initialise the database.
- Verify application readiness.
- Allow easy future updates.

---

# 3. System Requirements

Operating System

- Windows 10
- Windows 11

Minimum Hardware

Processor

- Intel Core i3

Memory

- 8 GB RAM

Storage

- 500 MB free space

Display

- 1366 × 768 minimum

Microsoft Excel

- Microsoft 365
- Excel 2021
- Excel 2019

Python Version (Development)

Python 3.12+

---

# 4. Production Installation

The production version shall be packaged as:

Capitec-Reconciliation-System.exe

The installer shall:

- Install application files
- Install icons
- Create database
- Create configuration files
- Create folders
- Create desktop shortcut
- Create Start Menu shortcut

---

# 5. Folder Structure

Capitec-Reconciliation-System/

│

├── backups/

├── config/

├── database/

├── logs/

├── reports/

├── sample_files/

├── temp/

└── settings.json

---

# 6. First Launch

When the application starts for the first time it shall:

- Create database
- Create configuration
- Create backup folder
- Create report folder
- Create logs folder
- Verify required permissions
- Display Welcome Screen

---

# 7. Configuration

The application shall automatically load:

settings.json

Default values

SIM_MULTIPLIER = 200

BANK_MULTIPLIER = 300

AUTO_BACKUP = TRUE

AUTO_PDF = TRUE

AUTO_HIGHLIGHT = TRUE

---

# 8. Database Initialisation

On first run:

Create

cdrs.db

Create all tables

Create indexes

Insert default settings

Verify successful creation

---

# 9. Deployment Verification

Verify:

✓ Application opens

✓ Dashboard loads

✓ Workbook opens

✓ Validation runs

✓ Reports generate

✓ Database accessible

✓ Backups created

✓ Settings saved

---

# 10. Updating the Application

Future updates shall:

- Preserve database
- Preserve settings
- Preserve reports
- Preserve backups
- Replace application files only

---

# 11. Backup Strategy

Before every workbook update:

Create timestamped backup.

Before every application update:

Backup

Database

Configuration

Reports

Logs

---

# 12. Recovery

If deployment fails:

Restore

Database

Settings

Application files

Restart application

---

# 13. Security

The application shall:

- Prevent accidental overwrite
- Verify workbook integrity
- Protect audit history
- Prevent data corruption

---

# 14. Logging

Deployment shall log:

Installation Started

Folders Created

Database Created

Configuration Created

Installation Completed

Errors

Warnings

---

# 15. Future Deployment Enhancements

Future versions may support:

- Automatic updates
- Network deployment
- MSI installer
- Microsoft Intune deployment
- SCCM deployment
- Cloud synchronisation

---

# 16. Acceptance Criteria

Deployment shall be considered successful when:

✓ Application installs correctly.

✓ Database is created.

✓ Configuration is loaded.

✓ Dashboard opens.

✓ Validation functions operate correctly.

✓ Reports are generated.

✓ Backups function correctly.

✓ No installation errors occur.

---

End of Document