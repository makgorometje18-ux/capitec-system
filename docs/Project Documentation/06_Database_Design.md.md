# Capitec Daily Reconciliation System (CDRS)

# 06_Database_Design.md

**Version:** 1.0

---

# 1. Purpose

This document defines the database architecture used by the Capitec Daily Reconciliation System (CDRS).

The application uses a lightweight SQLite database to store application settings, audit history, validation history, reconciliation statistics, backups, and user preferences.

The database is **not** used to store Daily Output workbook data permanently. Workbook data is processed in memory during validation.

---

# 2. Database Technology

Database Engine

SQLite 3

Advantages

- No installation required
- Portable
- Fast
- Reliable
- Easy backup
- Single database file
- Ideal for desktop applications

Database Name

```

cdrs.db

```

Location

```

database/
cdrs.db

```

---

# 3. Entity Relationship Diagram

```

Workbook
|
|----< ValidationRun
|
|----< DuplicateRecord
|
|----< ValidationError
|
|----< SummaryUpdate
|
|----< AuditLog

```

---

# 4. Database Tables

The application shall contain the following tables.

---

## Table 1

WorkbookHistory

Purpose

Store every workbook processed.

Fields

| Field | Type |
|---------|---------|
| ID | Integer PK |
| FileName | Text |
| FilePath | Text |
| ProcessDate | DateTime |
| WorkbookSize | Integer |
| ValidationStatus | Text |
| DurationSeconds | Integer |

---

## Table 2

ValidationRun

Purpose

One record per reconciliation.

Fields

| Field | Type |
|---------|---------|
| RunID | Integer PK |
| WorkbookID | Integer |
| StartTime | DateTime |
| EndTime | DateTime |
| Duration | Integer |
| Passed | Boolean |
| ErrorCount | Integer |
| WarningCount | Integer |
| UserName | Text |

---

## Table 3

DuplicateRecord

Purpose

Store every duplicate Batch Number detected.

Fields

| Field | Type |
|---------|---------|
| DuplicateID | Integer PK |
| RunID | Integer |
| BatchNumber | Text |
| Worksheet | Text |
| RowNumber | Integer |
| CellReference | Text |
| Occurrences | Integer |
| DuplicateType | Text |

DuplicateType

- Same Cell
- Different Rows

---

## Table 4

ValidationError

Purpose

Stores every validation failure.

Fields

| Field | Type |
|---------|---------|
| ErrorID | Integer PK |
| RunID | Integer |
| RuleID | Text |
| Worksheet | Text |
| RowNumber | Integer |
| ColumnName | Text |
| CellReference | Text |
| ErrorMessage | Text |
| SuggestedFix | Text |

---

## Table 5

SummaryUpdate

Purpose

Track every Summary Report modification.

Fields

| Field | Type |
|---------|---------|
| UpdateID | Integer PK |
| RunID | Integer |
| ItemName | Text |
| PreviousDispatch | Integer |
| NewDispatch | Integer |
| PreviousStock | Integer |
| NewStock | Integer |
| UpdatedTime | DateTime |

---

## Table 6

CardStatistics

Purpose

Store calculated totals.

Fields

| Field | Type |
|---------|---------|
| StatisticsID | Integer PK |
| RunID | Integer |
| SIMOrders | Integer |
| SIMCards | Integer |
| BankOrders | Integer |
| BankCards | Integer |
| TotalOrders | Integer |
| TotalCards | Integer |

---

## Table 7

AuditLog

Purpose

Application activity log.

Fields

| Field | Type |
|---------|---------|
| AuditID | Integer PK |
| DateTime | DateTime |
| Action | Text |
| User | Text |
| Result | Text |
| Description | Text |

Example

Workbook Loaded

Backup Created

Duplicate Found

Summary Updated

PDF Generated

Application Closed

---

## Table 8

Settings

Purpose

Store user preferences.

Fields

| Field | Type |
|---------|---------|
| SettingID | Integer PK |
| SettingName | Text |
| SettingValue | Text |

Examples

SIM Multiplier

200

Bank Multiplier

300

Theme

Dark

Auto Backup

True

Auto Fix Bag

True

---

# 5. Relationships

WorkbookHistory

↓

ValidationRun

↓

DuplicateRecord

↓

ValidationError

↓

SummaryUpdate

↓

CardStatistics

↓

AuditLog

---

# 6. Database Workflow

Application Starts

↓

Open Database

↓

Load Settings

↓

Run Validation

↓

Store Results

↓

Generate Reports

↓

Save Statistics

↓

Close Database

---

# 7. Indexes

Indexes shall be created for

BatchNumber

RunID

WorkbookID

DateTime

ValidationStatus

Purpose

Increase search performance.

---

# 8. Database Constraints

Primary Keys

Auto Increment

Foreign Keys Enabled

Cascade Delete Disabled

Null Values

Only where permitted.

---

# 9. Backup Strategy

Database backup

Daily

Workbook backup

Before every update

Audit history

Never deleted automatically

---

# 10. Data Retention

Validation History

Unlimited

Duplicate History

Unlimited

Audit Logs

Unlimited

Future setting

Archive after configurable period.

---

# 11. Future Database Enhancements

Microsoft SQL Server

PostgreSQL

Cloud Database

Azure SQL

MySQL

Multiple Users

Network Synchronisation

---

# 12. Acceptance Criteria

The database shall

✓ Store every validation

✓ Store every duplicate

✓ Store every summary update

✓ Store every audit event

✓ Store statistics

✓ Load within one second

✓ Never lose historical records

✓ Support future expansion

---

# Database File Structure

```

database/

│

├── cdrs.db

├── schema.sql

├── migrations/

└── backup/

```

---

End of Document