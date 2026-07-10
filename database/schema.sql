-- Capitec Daily Reconciliation System (CDRS) - Database Schema
-- Version: 1.0
-- SQLite 3

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Table 1: WorkbookHistory
-- Stores every workbook processed by the system
CREATE TABLE IF NOT EXISTS WorkbookHistory (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    FileName TEXT NOT NULL,
    FilePath TEXT NOT NULL,
    ProcessDate DATETIME NOT NULL,
    WorkbookSize INTEGER,
    ValidationStatus TEXT,
    DurationSeconds INTEGER,
    UNIQUE(FilePath, ProcessDate)
);

-- Table 2: ValidationRun
-- One record per reconciliation
CREATE TABLE IF NOT EXISTS ValidationRun (
    RunID INTEGER PRIMARY KEY AUTOINCREMENT,
    WorkbookID INTEGER NOT NULL,
    StartTime DATETIME NOT NULL,
    EndTime DATETIME,
    Duration INTEGER,
    Passed BOOLEAN DEFAULT 0,
    ErrorCount INTEGER DEFAULT 0,
    WarningCount INTEGER DEFAULT 0,
    UserName TEXT,
    FOREIGN KEY (WorkbookID) REFERENCES WorkbookHistory(ID)
);

-- Table 3: DuplicateRecord
-- Stores every duplicate Batch Number detected
CREATE TABLE IF NOT EXISTS DuplicateRecord (
    DuplicateID INTEGER PRIMARY KEY AUTOINCREMENT,
    RunID INTEGER NOT NULL,
    BatchNumber TEXT NOT NULL,
    Worksheet TEXT NOT NULL,
    RowNumber INTEGER,
    CellReference TEXT,
    Occurrences INTEGER DEFAULT 1,
    DuplicateType TEXT,
    FOREIGN KEY (RunID) REFERENCES ValidationRun(RunID)
);

-- Table 4: ValidationError
-- Stores every validation failure
CREATE TABLE IF NOT EXISTS ValidationError (
    ErrorID INTEGER PRIMARY KEY AUTOINCREMENT,
    RunID INTEGER NOT NULL,
    RuleID TEXT,
    Worksheet TEXT,
    RowNumber INTEGER,
    ColumnName TEXT,
    CellReference TEXT,
    ErrorMessage TEXT NOT NULL,
    SuggestedFix TEXT,
    FOREIGN KEY (RunID) REFERENCES ValidationRun(RunID)
);

-- Table 5: SummaryUpdate
-- Track every Summary Report modification
CREATE TABLE IF NOT EXISTS SummaryUpdate (
    UpdateID INTEGER PRIMARY KEY AUTOINCREMENT,
    RunID INTEGER NOT NULL,
    ItemName TEXT NOT NULL,
    PreviousDispatch INTEGER,
    NewDispatch INTEGER,
    PreviousStock INTEGER,
    NewStock INTEGER,
    UpdatedTime DATETIME NOT NULL,
    FOREIGN KEY (RunID) REFERENCES ValidationRun(RunID)
);

-- Table 6: CardStatistics
-- Store calculated totals
CREATE TABLE IF NOT EXISTS CardStatistics (
    StatisticsID INTEGER PRIMARY KEY AUTOINCREMENT,
    RunID INTEGER NOT NULL,
    SIMOrders INTEGER DEFAULT 0,
    SIMCards INTEGER DEFAULT 0,
    BankOrders INTEGER DEFAULT 0,
    BankCards INTEGER DEFAULT 0,
    TotalOrders INTEGER DEFAULT 0,
    TotalCards INTEGER DEFAULT 0,
    FOREIGN KEY (RunID) REFERENCES ValidationRun(RunID)
);

-- Table 9: ReconciliationHistory
-- Records each reconciliation run with card counts and summary status
CREATE TABLE IF NOT EXISTS ReconciliationHistory (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Workbook TEXT NOT NULL,
    ActiveWorksheet TEXT,
    Date DATETIME,
    SIMOrders INTEGER DEFAULT 0,
    SIMCards INTEGER DEFAULT 0,
    BankOrders INTEGER DEFAULT 0,
    BankCards INTEGER DEFAULT 0,
    PreviousStock INTEGER DEFAULT 0,
    NewStock INTEGER DEFAULT 0,
    ValidationResult TEXT,
    SummaryUpdated INTEGER DEFAULT 0,
    User TEXT,
    Timestamp DATETIME
);

-- Table 7: AuditLog
-- Application activity log
CREATE TABLE IF NOT EXISTS AuditLog (
    AuditID INTEGER PRIMARY KEY AUTOINCREMENT,
    DateTime DATETIME NOT NULL,
    Action TEXT NOT NULL,
    User TEXT,
    Result TEXT,
    Description TEXT
);

-- Table 8: Settings
-- Store user preferences
CREATE TABLE IF NOT EXISTS Settings (
    SettingID INTEGER PRIMARY KEY AUTOINCREMENT,
    SettingName TEXT UNIQUE NOT NULL,
    SettingValue TEXT NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ValidationRun_WorkbookID ON ValidationRun(WorkbookID);
CREATE INDEX IF NOT EXISTS idx_ValidationRun_StartTime ON ValidationRun(StartTime);
CREATE INDEX IF NOT EXISTS idx_DuplicateRecord_RunID ON DuplicateRecord(RunID);
CREATE INDEX IF NOT EXISTS idx_DuplicateRecord_BatchNumber ON DuplicateRecord(BatchNumber);
CREATE INDEX IF NOT EXISTS idx_ValidationError_RunID ON ValidationError(RunID);
CREATE INDEX IF NOT EXISTS idx_AuditLog_DateTime ON AuditLog(DateTime);
CREATE INDEX IF NOT EXISTS idx_AuditLog_Action ON AuditLog(Action);
CREATE INDEX IF NOT EXISTS idx_Settings_SettingName ON Settings(SettingName);

-- Insert default settings
INSERT OR IGNORE INTO Settings (SettingName, SettingValue) VALUES
    ('SIM_MULTIPLIER', '200'),
    ('BANK_MULTIPLIER', '300'),
    ('AUTO_BACKUP', 'TRUE'),
    ('AUTO_HIGHLIGHT', 'TRUE'),
    ('THEME', 'Light');
