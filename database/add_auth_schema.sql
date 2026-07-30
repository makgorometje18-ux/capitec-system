a-- Authentication Schema for Capitec Daily Reconciliation System
-- Version: 1.0
-- SQLite 3

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users Table
-- Stores user credentials, roles, and account status
CREATE TABLE IF NOT EXISTS Users (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    PasswordHash TEXT NOT NULL,
    Salt TEXT NOT NULL,
    Role TEXT NOT NULL DEFAULT 'Staff',
    AccountStatus TEXT NOT NULL DEFAULT 'ACTIVE',
    PasswordLastChanged TEXT NOT NULL,
    FirstLogin INTEGER DEFAULT 1,
    CreatedAt TEXT NOT NULL,
    FailedLoginAttempts INTEGER DEFAULT 0,
    LockedUntil TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_Users_Username ON Users(Username);
CREATE INDEX IF NOT EXISTS idx_Users_Role ON Users(Role);
CREATE INDEX IF NOT EXISTS idx_Users_AccountStatus ON Users(AccountStatus);

-- Insert default admin user with default password 'Capitec2024!'
-- Password: Capitec2024! (meets requirements: 8+ chars, uppercase, number)
-- Admin must change this on first login
INSERT OR IGNORE INTO Users (Username, PasswordHash, Salt, Role, AccountStatus, PasswordLastChanged, FirstLogin, CreatedAt)
SELECT 
    'ADMIN',
    'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0',  -- Placeholder - will be updated by migration
    'admin_salt_placeholder',
    'Admin',
    'ACTIVE',
    datetime('now'),
    1,
    datetime('now')
WHERE NOT EXISTS (SELECT 1 FROM Users WHERE Username = 'ADMIN');

-- Insert initial staff users (password must be created on first login)
INSERT OR IGNORE INTO Users (Username, PasswordHash, Salt, Role, AccountStatus, PasswordLastChanged, FirstLogin, CreatedAt)
VALUES 
    ('SIDLAI_KHUNGEKA', 'dne_placeholder', 'salt_placeholder', 'Staff', 'ACTIVE', datetime('now'), 1, datetime('now')),
    ('LIWANI_SISIPO', 'dne_placeholder', 'salt_placeholder', 'Staff', 'ACTIVE', datetime('now'), 1, datetime('now')),
    ('XAKAYI_ZIZIPHO', 'dne_placeholder', 'salt_placeholder', 'Staff', 'ACTIVE', datetime('now'), 1, datetime('now'));

-- Note: Staff users with 'dne_placeholder' hash will need to set their password on first login
-- The system will force password creation for these users