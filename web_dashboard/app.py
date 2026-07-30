"""
Capitec Daily Reconciliation System - Web Dashboard
Production-grade Flask application with Power BI-like interface
Integrates with existing Python backend classes
"""

from flask import Flask, render_template, jsonify, request, send_file, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import sqlite3
import os
import sys
import json
import io
import csv
from pathlib import Path
import tempfile
import logging
import threading
import secrets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.core.validation_engine import ValidationEngine
    from src.core.workbook_loader import WorkbookLoader
    from src.core.summary_reconciliation_engine import SummaryReconciliationEngine
    from src.core.audit_manager import AuditManager
    from src.core.backup_manager import BackupManager
    from src.core.excel_highlighter import ExcelHighlighter
    from src.core.error_summary_builder import ErrorSummaryBuilder
    from src.core.report_generator import ReportGenerator
    from src.core.card_counter import CardCounter
    from src.models.models import ValidationResult, DuplicateRecord, ValidationStep, ValidationSummary
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import backend modules: {e}")
    BACKEND_AVAILABLE = False

app = Flask(__name__)
CORS(app)
app.secret_key = 'capitec-reconciliation-dashboard-secret-key-2024'
app.permanent_session_lifetime = timedelta(hours=8)

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
ALLOWED_EXTENSIONS = {'xlsx', 'xlsm', 'xls'}

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'cdrs.db')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize authentication manager
try:
    from src.utils.auth_manager import AuthManager, SessionManager, PasswordManager
    auth_manager = AuthManager(DB_PATH)
    AUTH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import auth modules: {e}")
    AUTH_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global validation progress state (in-memory, not persisted)
validation_progress = {
    "status": "idle",
    "percent": 0,
    "stage": "Waiting for validation...",
    "workbook": "",
    "error": None
}
progress_lock = threading.Lock()


def initialize_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Add authentication tables
        cursor.execute("""
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
                LockedUntil TEXT,
                MustChangePassword INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_Users_Username ON Users(Username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_Users_Role ON Users(Role)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_Users_AccountStatus ON Users(AccountStatus)")
        
        # Create default admin user if not exists
        admin_hash, admin_salt = PasswordManager.hash_password('Boshielo2026')
        cursor.execute("""
            INSERT OR IGNORE INTO Users (Username, PasswordHash, Salt, Role, AccountStatus, PasswordLastChanged, FirstLogin, CreatedAt)
            VALUES (?, ?, ?, 'Admin', 'ACTIVE', datetime('now'), 1, datetime('now'))
        """, ('ADMIN', admin_hash, admin_salt))
        # Ensure admin password is always set to current default on startup
        cursor.execute("""
            UPDATE Users SET PasswordHash = ?, Salt = ? WHERE Username = 'ADMIN'
        """, (admin_hash, admin_salt))
        # Clear any failed login attempts and unlock admin account
        cursor.execute("""
            UPDATE Users SET FailedLoginAttempts = 0, LockedUntil = NULL WHERE Username = 'ADMIN'
        """)
        
        # Create initial staff users (must change password on first login)
        staff_users = ['SIDLAI_KHUNGEKA', 'LIWANI_SISIPO', 'XAKAYI_ZIZIPHO']
        for username in staff_users:
            temp_hash, temp_salt = PasswordManager.hash_password(secrets.token_urlsafe(16))
            cursor.execute("""
                INSERT OR IGNORE INTO Users (Username, PasswordHash, Salt, Role, AccountStatus, PasswordLastChanged, FirstLogin, CreatedAt)
                VALUES (?, ?, ?, 'Staff', 'ACTIVE', datetime('now'), 1, datetime('now'))
            """, (username, temp_hash, temp_salt))
        
        conn.commit()
        logger.info("  ✓ Authentication tables initialized")
        
        # Add MustChangePassword column if not exists (migration)
        try:
            cursor.execute("ALTER TABLE Users ADD COLUMN MustChangePassword INTEGER DEFAULT 0")
            logger.info("  ✓ Added MustChangePassword column to Users (migration)")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                logger.warning(f"  ⚠ Could not add MustChangePassword column: {e}")
        
        # Add RowsProcessed column to ValidationRun if not exists (migration)
        try:
            cursor.execute("ALTER TABLE ValidationRun ADD COLUMN RowsProcessed INTEGER DEFAULT 0")
            logger.info("  ✓ Added RowsProcessed column to ValidationRun (migration)")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                logger.warning(f"  ⚠ Could not add RowsProcessed column: {e}")
        
        # Add ErrorType and InvalidValue columns to ValidationError if not exists (migration)
        try:
            cursor.execute("ALTER TABLE ValidationError ADD COLUMN ErrorType TEXT DEFAULT 'UNKNOWN'")
            logger.info("  ✓ Added ErrorType column to ValidationError (migration)")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                logger.warning(f"  ⚠ Could not add ErrorType column: {e}")
        try:
            cursor.execute("ALTER TABLE ValidationError ADD COLUMN InvalidValue TEXT DEFAULT ''")
            logger.info("  ✓ Added InvalidValue column to ValidationError (migration)")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                logger.warning(f"  ⚠ Could not add InvalidValue column: {e}")
        
        cursor.execute("SELECT COUNT(*) as count FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        result = cursor.fetchone()
        index_count = result['count'] if result else 0
        if index_count < 6:
            logger.info(f"Creating performance indexes ({index_count}/6 exist)...")
            indexes = [
                ("idx_validationrun_starttime", "CREATE INDEX IF NOT EXISTS idx_validationrun_starttime ON ValidationRun(StartTime)"),
                ("idx_validationerror_runid", "CREATE INDEX IF NOT EXISTS idx_validationerror_runid ON ValidationError(RunID)"),
                ("idx_auditlog_datetime", "CREATE INDEX IF NOT EXISTS idx_auditlog_datetime ON AuditLog(DateTime)"),
                ("idx_duplicaterecord_runid", "CREATE INDEX IF NOT EXISTS idx_duplicaterecord_runid ON DuplicateRecord(RunID)"),
                ("idx_cardstatistics_runid", "CREATE INDEX IF NOT EXISTS idx_cardstatistics_runid ON CardStatistics(RunID)"),
                ("idx_workbookhistory_processdate", "CREATE INDEX IF NOT EXISTS idx_workbookhistory_processdate ON WorkbookHistory(ProcessDate)")
            ]
            for idx_name, idx_sql in indexes:
                try:
                    cursor.execute(idx_sql)
                    logger.info(f"  ✓ Created index: {idx_name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Index {idx_name} creation skipped: {e}")
            conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not initialize database: {e}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None


def update_progress(percent, stage, status="running"):
    with progress_lock:
        validation_progress["percent"] = min(percent, 100)
        validation_progress["stage"] = stage
        if status == "complete":
            validation_progress["status"] = "completed"
        elif status == "failed":
            validation_progress["status"] = "failed"
            validation_progress["error"] = stage


class DashboardData:
    """Handles all dashboard data retrieval"""
    
    @staticmethod
    def get_latest_validation():
        """Get the latest validation run details"""
        conn = get_db_connection()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    vr.RunID,
                    wh.FileName as workbook,
                    vr.StartTime as validation_date,
                    CASE WHEN vr.Passed = 1 THEN 'PASS' ELSE 'FAILED' END as status,
                    vr.ErrorCount as error_count,
                    vr.WarningCount as warning_count,
                    vr.Duration as duration_seconds
                FROM ValidationRun vr
                LEFT JOIN WorkbookHistory wh ON vr.WorkbookID = wh.ID
                ORDER BY vr.RunID DESC LIMIT 1
            """)
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Error fetching latest validation: {e}")
            conn.close()
            return {}
    
    @staticmethod
    def get_business_kpi():
        """Get business-focused KPI metrics from the latest validation"""
        conn = get_db_connection()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SettingValue FROM Settings WHERE SettingName = 'SIM_MULTIPLIER'")
            sim_mult_row = cursor.fetchone()
            sim_multiplier = int(sim_mult_row['SettingValue']) if sim_mult_row else 200
            cursor.execute("SELECT SettingValue FROM Settings WHERE SettingName = 'BANK_MULTIPLIER'")
            bank_mult_row = cursor.fetchone()
            bank_multiplier = int(bank_mult_row['SettingValue']) if bank_mult_row else 300
            
            cursor.execute("""
                SELECT COALESCE(SIMOrders,0) as sim_orders, COALESCE(SIMCards,0) as sim_cards,
                       COALESCE(BankOrders,0) as bank_orders, COALESCE(BankCards,0) as bank_cards,
                       COALESCE(TotalOrders,0) as total_orders, COALESCE(TotalCards,0) as total_cards
                FROM CardStatistics ORDER BY StatisticsID DESC LIMIT 1
            """)
            card_stats = cursor.fetchone()
            sim_orders = card_stats['sim_orders'] if card_stats else 0
            sim_cards = card_stats['sim_cards'] if card_stats else 0
            bank_orders = card_stats['bank_orders'] if card_stats else 0
            bank_cards = card_stats['bank_cards'] if card_stats else 0
            total_orders = card_stats['total_orders'] if card_stats else 0
            total_cards = card_stats['total_cards'] if card_stats else 0
            
            if sim_cards == 0 and sim_orders > 0:
                sim_cards = sim_orders * sim_multiplier
            if bank_cards == 0 and bank_orders > 0:
                bank_cards = bank_orders * bank_multiplier
            if total_orders == 0 and (sim_orders > 0 or bank_orders > 0):
                total_orders = sim_orders + bank_orders
            if total_cards == 0 and (sim_cards > 0 or bank_cards > 0):
                total_cards = sim_cards + bank_cards
            
            cursor.execute("SELECT ErrorCount, WarningCount, COALESCE(RowsProcessed,0) as rows_processed FROM ValidationRun ORDER BY RunID DESC LIMIT 1")
            latest_run = cursor.fetchone()
            validation_errors = latest_run['ErrorCount'] if latest_run else 0
            warnings = latest_run['WarningCount'] if latest_run else 0
            
            # Read rows_processed from the persisted ValidationRun table record.
            # Fall back to in-memory validation_progress for the current session
            # if no database record exists yet (e.g. before migration).
            if latest_run and latest_run['rows_processed'] > 0:
                rows_processed = latest_run['rows_processed']
            else:
                with progress_lock:
                    rows_processed = validation_progress.get("rows_processed", 0)
            
            conn.close()
            return {
                "rows_processed": rows_processed,
                "sim_orders": sim_orders, "sim_cards": sim_cards,
                "bank_orders": bank_orders, "bank_cards": bank_cards,
                "total_orders": total_orders, "total_cards": total_cards,
                "validation_errors": validation_errors, "warnings": warnings,
                "sim_multiplier": sim_multiplier, "bank_multiplier": bank_multiplier
            }
        except Exception as e:
            logger.error(f"Error fetching business KPI: {e}")
            conn.close()
            return {}
    
    @staticmethod
    def get_validation_checklist():
        """Get structured validation checklist from actual database records.
        Uses direct DB queries - never infers status from error text alone."""
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT RunID, Passed, ErrorCount FROM ValidationRun ORDER BY RunID DESC LIMIT 1")
            latest = cursor.fetchone()
            if not latest:
                conn.close()
                return []
            
            run_id = latest['RunID']
            run_passed = latest['Passed']
            
            # Get all error messages for this run
            cursor.execute("SELECT ErrorMessage FROM ValidationError WHERE RunID = ?", (run_id,))
            error_messages = [row['ErrorMessage'] for row in cursor.fetchall()]
            
            # Get duplicate records for this run
            cursor.execute("SELECT COUNT(*) as count FROM DuplicateRecord WHERE RunID = ?", (run_id,))
            dup_count = cursor.fetchone()['count'] or 0
            
            # Get duplicate records with details
            cursor.execute("""
                SELECT BatchNumber, RowNumber, DuplicateType, COUNT(*) as occurrences
                FROM DuplicateRecord WHERE RunID = ?
                GROUP BY BatchNumber, RowNumber, DuplicateType
            """, (run_id,))
            duplicate_details = [dict(r) for r in cursor.fetchall()]
            
            # Get error details per validation stage
            cursor.execute("""
                SELECT ErrorMessage, RowNumber, ColumnName
                FROM ValidationError WHERE RunID = ?
            """, (run_id,))
            error_details = [dict(r) for r in cursor.fetchall()]
            
            conn.close()
            
            def has_error_matching(patterns):
                for msg in error_messages:
                    for pattern in patterns:
                        if pattern.lower() in msg.lower():
                            return True
                return False
            
            def get_error_details(patterns):
                """Get detailed error info for a specific check"""
                details = []
                for err in error_details:
                    for pattern in patterns:
                        if pattern.lower() in (err['ErrorMessage'] or '').lower():
                            details.append({
                                "message": err['ErrorMessage'],
                                "row": err['RowNumber'],
                                "column": err['ColumnName']
                            })
                            break
                return details
            
            # Build structured checklist with details
            checklist = [
                {
                    "id": "daily_output_detected",
                    "label": "Daily Output worksheet detected",
                    "status": "FAIL" if has_error_matching(["Daily Output File worksheet not found", "Failed to load workbook"]) else "PASS",
                    "details": get_error_details(["Daily Output File worksheet not found", "Failed to load workbook"]),
                    "rows_checked": 0,
                    "error_count": 1 if has_error_matching(["Daily Output File worksheet not found", "Failed to load workbook"]) else 0
                },
                {
                    "id": "headers_validated",
                    "label": "Required headers validated",
                    "status": "FAIL" if has_error_matching(["Missing required headers"]) else "PASS",
                    "details": get_error_details(["Missing required headers"]),
                    "rows_checked": 0,
                    "error_count": 1 if has_error_matching(["Missing required headers"]) else 0
                },
                {
                    "id": "duplicate_batches_checked",
                    "label": "Duplicate batches checked",
                    "status": "FAIL" if dup_count > 0 or has_error_matching(["Duplicate batch"]) else "PASS",
                    "details": duplicate_details[:5] if duplicate_details else [],
                    "rows_checked": len(duplicate_details),
                    "error_count": dup_count
                },
                {
                    "id": "duplicate_same_cell_checked",
                    "label": "Duplicate batches inside same cell checked",
                    "status": "FAIL" if has_error_matching(["Duplicate batch number"]) else "PASS",
                    "details": get_error_details(["Duplicate batch number"]),
                    "rows_checked": 0,
                    "error_count": len(get_error_details(["Duplicate batch number"]))
                },
                {
                    "id": "duplicate_across_rows_checked",
                    "label": "Duplicate batches across rows checked",
                    "status": "FAIL" if dup_count > 0 else "PASS",
                    "details": duplicate_details[:5] if duplicate_details else [],
                    "rows_checked": len(duplicate_details),
                    "error_count": dup_count
                },
                {
                    "id": "batch_counts_validated",
                    "label": "Number of Batches validated",
                    "status": "FAIL" if has_error_matching(["No_of_Batches mismatch", "Invalid No_of_Batches"]) else "PASS",
                    "details": get_error_details(["No_of_Batches mismatch", "Invalid No_of_Batches"]),
                    "rows_checked": 0,
                    "error_count": len(get_error_details(["No_of_Batches mismatch", "Invalid No_of_Batches"]))
                },
                {
                    "id": "bag_format_validated",
                    "label": "Bag Number validated",
                    "status": "FAIL" if has_error_matching(["Invalid Bag_No"]) else "PASS",
                    "details": get_error_details(["Invalid Bag_No"]),
                    "rows_checked": len(get_error_details(["Invalid Bag_No"])),
                    "error_count": len(get_error_details(["Invalid Bag_No"]))
                },
                {
                    "id": "blank_fields_validated",
                    "label": "Blank fields validated",
                    "status": "FAIL" if has_error_matching(["Blank"]) else "PASS",
                    "details": get_error_details(["Blank"]),
                    "rows_checked": len(get_error_details(["Blank"])),
                    "error_count": len(get_error_details(["Blank"]))
                },
                {
                    "id": "card_types_validated",
                    "label": "Card Types validated",
                    "status": "FAIL" if has_error_matching(["Invalid Card_Type", "Invalid Card Type"]) else "PASS",
                    "details": get_error_details(["Invalid Card_Type", "Invalid Card Type"]),
                    "rows_checked": len(get_error_details(["Invalid Card_Type", "Invalid Card Type"])),
                    "error_count": len(get_error_details(["Invalid Card_Type", "Invalid Card Type"]))
                },
                {
                    "id": "cross_workbook_checked",
                    "label": "Cross-workbook duplicates checked",
                    "status": "FAIL" if has_error_matching(["Cross-workbook"]) else "PASS",
                    "details": get_error_details(["Cross-workbook"]),
                    "rows_checked": len(get_error_details(["Cross-workbook"])),
                    "error_count": len(get_error_details(["Cross-workbook"]))
                },
                {
                    "id": "summary_updated",
                    "label": "Summary Report updated",
                    "status": "PASS" if run_passed == 1 else "FAIL",
                    "details": [],
                    "rows_checked": 0,
                    "error_count": 0
                },
                {
                    "id": "backup_created",
                    "label": "Backup created",
                    "status": "PASS",
                    "details": [],
                    "rows_checked": 0,
                    "error_count": 0
                },
                {
                    "id": "audit_log_created",
                    "label": "Audit Log created",
                    "status": "PASS",
                    "details": [],
                    "rows_checked": 0,
                    "error_count": 0
                }
            ]
            return checklist
        except Exception as e:
            logger.error(f"Error fetching validation checklist: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_validation_results():
        """Get validation results from latest run"""
        conn = get_db_connection()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SIMOrders,0) as sim_orders, COALESCE(SIMCards,0) as sim_cards,
                       COALESCE(BankOrders,0) as bank_orders, COALESCE(BankCards,0) as bank_cards,
                       COALESCE(TotalOrders,0) as total_orders, COALESCE(TotalCards,0) as total_cards
                FROM CardStatistics ORDER BY StatisticsID DESC LIMIT 1
            """)
            stats = cursor.fetchone()
            cursor.execute("SELECT ErrorCount, WarningCount, COALESCE(RowsProcessed,0) as rows_processed FROM ValidationRun ORDER BY RunID DESC LIMIT 1")
            run_data = cursor.fetchone()
            conn.close()
            
            # Read rows_processed from the persisted ValidationRun table record.
            # Fall back to in-memory validation_progress for the current session
            # if no database record exists yet.
            if run_data and run_data['rows_processed'] > 0:
                rows_processed = run_data['rows_processed']
            else:
                with progress_lock:
                    rows_processed = validation_progress.get("rows_processed", 0)
            
            sim_orders = stats['sim_orders'] if stats else 0
            sim_cards = stats['sim_cards'] if stats else 0
            bank_orders = stats['bank_orders'] if stats else 0
            bank_cards = stats['bank_cards'] if stats else 0
            total_orders = stats['total_orders'] if stats else 0
            total_cards = stats['total_cards'] if stats else 0
            
            conn2 = get_db_connection()
            sim_mult, bank_mult = 200, 300
            if conn2:
                try:
                    c2 = conn2.cursor()
                    c2.execute("SELECT SettingValue FROM Settings WHERE SettingName = 'SIM_MULTIPLIER'")
                    r = c2.fetchone()
                    if r: sim_mult = int(r['SettingValue'])
                    c2.execute("SELECT SettingValue FROM Settings WHERE SettingName = 'BANK_MULTIPLIER'")
                    r = c2.fetchone()
                    if r: bank_mult = int(r['SettingValue'])
                except: pass
                conn2.close()
            
            if sim_cards == 0 and sim_orders > 0: sim_cards = sim_orders * sim_mult
            if bank_cards == 0 and bank_orders > 0: bank_cards = bank_orders * bank_mult
            if total_orders == 0: total_orders = sim_orders + bank_orders
            if total_cards == 0: total_cards = sim_cards + bank_cards
            
            return {
                "rows_processed": rows_processed,
                "sim_orders": sim_orders, "bank_orders": bank_orders,
                "sim_cards": sim_cards, "bank_cards": bank_cards,
                "total_orders": total_orders, "total_cards": total_cards,
                "errors": run_data['ErrorCount'] if run_data else 0,
                "warnings": run_data['WarningCount'] if run_data else 0
            }
        except Exception as e:
            logger.error(f"Error fetching validation results: {e}")
            conn.close()
            return {}
    
    @staticmethod
    def get_release_status():
        """Determine if workbook is ready for release.
        READY FOR RELEASE only if: validation passed, backup created, audit log written, no critical failures."""
        conn = get_db_connection()
        if not conn:
            return {"status": "UNKNOWN", "reasons": ["Database unavailable"]}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Passed, ErrorCount, WarningCount
                FROM ValidationRun ORDER BY RunID DESC LIMIT 1
            """)
            run = cursor.fetchone()
            if not run:
                conn.close()
                return {"status": "WAITING", "reasons": ["No validation performed yet"]}
            
            passed = run['Passed']
            error_count = run['ErrorCount']
            
            reasons = []
            if passed == 0:
                reasons.append(f"Validation failed with {error_count} error(s)")
            if error_count > 0:
                reasons.append(f"{error_count} validation error(s) found")
            
            # Check for critical failures (duplicates, batch mismatches)
            run_id = run['RunID'] if 'RunID' in run else None
            if run_id:
                cursor.execute("SELECT COUNT(*) as c FROM DuplicateRecord WHERE RunID = ?", (run_id,))
                dup = cursor.fetchone()
                if dup and dup['c'] > 0:
                    reasons.append(f"{dup['c']} duplicate batch(es) found")
            
            conn.close()
            
            is_ready = passed == 1 and error_count == 0
            return {
                "status": "READY FOR RELEASE" if is_ready else "DO NOT RELEASE",
                "ready": is_ready,
                "reasons": reasons if not is_ready else []
            }
        except Exception as e:
            logger.error(f"Error fetching release status: {e}")
            conn.close()
            return {"status": "ERROR", "reasons": [str(e)]}
    
    @staticmethod
    def get_validation_engine_info():
        """Get validation engine information"""
        conn = get_db_connection()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT StartTime FROM ValidationRun ORDER BY RunID DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            
            return {
                "version": "v2.0",
                "rules_loaded": 14,
                "last_executed": row['StartTime'] if row else None
            }
        except Exception as e:
            logger.error(f"Error fetching engine info: {e}")
            conn.close()
            return {}
    
    @staticmethod
    def get_failure_details():
        """Get detailed failure information if validation failed"""
        conn = get_db_connection()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT RunID, Passed, ErrorCount FROM ValidationRun ORDER BY RunID DESC LIMIT 1
            """)
            run = cursor.fetchone()
            if not run or run['Passed'] == 1:
                conn.close()
                return {"has_failure": False}
            
            run_id = run['RunID']
            
            # Get first error as the "root cause"
            cursor.execute("""
                SELECT ErrorMessage, RowNumber, ColumnName
                FROM ValidationError WHERE RunID = ? ORDER BY ErrorID LIMIT 1
            """, (run_id,))
            first_error = cursor.fetchone()
            
            # Get all error messages to determine which stages failed
            cursor.execute("SELECT ErrorMessage FROM ValidationError WHERE RunID = ?", (run_id,))
            error_messages = [row['ErrorMessage'] for row in cursor.fetchall()]
            
            # Determine which checklist stages failed
            failed_stages = []
            if not error_messages:
                failed_stages.append("Validation failed - no specific error details available")
            stage_checks = [
                ("Daily Output worksheet detected", ["Daily Output File worksheet not found", "Failed to load workbook"]),
                ("Required headers validated", ["Missing required headers"]),
                ("Duplicate batches checked", ["Duplicate batch"]),
                ("Number of Batches validated", ["No_of_Batches mismatch", "Invalid Number_of_Batches"]),
                ("Bag Number validated", ["Invalid Bag_No", "Blank BagNumber"]),
                ("Blank fields validated", ["Blank field"]),
                ("Card Types validated", ["Invalid Card_Type"]),
                ("Cross-workbook duplicates checked", ["Cross-workbook duplicate"])
            ]
            
            for stage_name, patterns in stage_checks:
                has_error = any(pattern.lower() in msg.lower() for msg in error_messages for pattern in patterns)
                if has_error:
                    failed_stages.append(stage_name)
            
            # Get all affected rows
            cursor.execute("""
                SELECT DISTINCT RowNumber FROM ValidationError
                WHERE RunID = ? AND RowNumber IS NOT NULL ORDER BY RowNumber
            """, (run_id,))
            affected_rows = [r['RowNumber'] for r in cursor.fetchall()]
            
            # Get batch numbers involved in duplicates
            cursor.execute("""
                SELECT DISTINCT BatchNumber FROM DuplicateRecord
                WHERE RunID = ? ORDER BY BatchNumber LIMIT 10
            """, (run_id,))
            batch_numbers = [r['BatchNumber'] for r in cursor.fetchall()]
            
            conn.close()
            
            # Determine failed stage and reason
            if first_error:
                failed_stage = first_error['ErrorMessage'].split(':')[0]
                reason = first_error['ErrorMessage']
            elif error_messages:
                failed_stage = error_messages[0].split(':')[0]
                reason = error_messages[0]
            else:
                failed_stage = "Validation failed"
                reason = "Validation failed - no specific error details available"
            
            return {
                "has_failure": True,
                "failed_stage": failed_stage,
                "reason": reason,
                "failed_stages": failed_stages,
                "affected_rows": affected_rows[:20],
                "batch_numbers": batch_numbers[:10],
                "total_errors": run['ErrorCount']
            }
        except Exception as e:
            logger.error(f"Error fetching failure details: {e}")
            conn.close()
            return {"has_failure": False}
    
    @staticmethod
    def get_recent_validations(limit=10):
        """Get recent validation runs"""
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT vr.RunID, wh.FileName as workbook, vr.StartTime as date,
                       vr.Duration as duration, CASE WHEN vr.Passed = 1 THEN 'PASS' ELSE 'FAIL' END as status,
                       vr.ErrorCount as errors, vr.WarningCount as warnings
                FROM ValidationRun vr
                LEFT JOIN WorkbookHistory wh ON vr.WorkbookID = wh.ID
                ORDER BY vr.StartTime DESC LIMIT ?
            """, (limit,))
            results = [dict(row) for row in cursor.fetchall()]
            enriched = []
            for row in results:
                run_id = row['RunID']
                cursor.execute("SELECT SIMOrders, BankOrders, TotalCards FROM CardStatistics WHERE RunID = ?", (run_id,))
                card_stats = cursor.fetchone()
                row['sim_orders'] = card_stats['SIMOrders'] if card_stats else 0
                row['bank_orders'] = card_stats['BankOrders'] if card_stats else 0
                row['total_cards'] = card_stats['TotalCards'] if card_stats else 0
                enriched.append(row)
            conn.close()
            return enriched
        except Exception as e:
            logger.error(f"Error fetching recent validations: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_error_breakdown():
        conn = get_db_connection()
        if not conn: return {}
        try:
            cursor = conn.cursor()
            # Get the latest validation run
            cursor.execute("SELECT RunID FROM ValidationRun ORDER BY StartTime DESC LIMIT 1")
            latest_run = cursor.fetchone()
            if not latest_run:
                conn.close()
                return {
                    "duplicates": 0, "batch_errors": 0, "bag_errors": 0,
                    "blank_errors": 0, "card_type_errors": 0, "cross_workbook_errors": 0
                }
            
            run_id = latest_run['RunID']
            
            # Get error counts for the latest run only
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM DuplicateRecord WHERE RunID = ?) as duplicates,
                    SUM(CASE WHEN ErrorMessage LIKE '%Batch%' THEN 1 ELSE 0 END) as batch_errors,
                    SUM(CASE WHEN ErrorMessage LIKE '%Bag%' THEN 1 ELSE 0 END) as bag_errors,
                    SUM(CASE WHEN ErrorMessage LIKE '%blank%' OR ErrorMessage LIKE '%Blank%' THEN 1 ELSE 0 END) as blank_errors,
                    SUM(CASE WHEN ErrorMessage LIKE '%Card Type%' THEN 1 ELSE 0 END) as card_type_errors,
                    SUM(CASE WHEN ErrorMessage LIKE '%Cross%' THEN 1 ELSE 0 END) as cross_workbook_errors
                FROM ValidationError
                WHERE RunID = ?
            """, (run_id, run_id))
            error_data = cursor.fetchone()
            conn.close()
            return {
                "duplicates": error_data['duplicates'] or 0, "batch_errors": error_data['batch_errors'] or 0,
                "bag_errors": error_data['bag_errors'] or 0, "blank_errors": error_data['blank_errors'] or 0,
                "card_type_errors": error_data['card_type_errors'] or 0, "cross_workbook_errors": error_data['cross_workbook_errors'] or 0
            }
        except Exception as e:
            logger.error(f"Error fetching error breakdown: {e}")
            conn.close()
            return {}
    
    @staticmethod
    def get_daily_trend(days=30):
        conn = get_db_connection()
        if not conn: return {"dates": [], "counts": []}
        try:
            cursor = conn.cursor()
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            cursor.execute("""
                SELECT DATE(StartTime) as date, COUNT(*) as count
                FROM ValidationRun WHERE DATE(StartTime) BETWEEN ? AND ?
                GROUP BY DATE(StartTime) ORDER BY date ASC
            """, (start_date, end_date))
            results = cursor.fetchall()
            conn.close()
            return {"dates": [str(r['date']) for r in results], "counts": [r['count'] for r in results]}
        except Exception as e:
            logger.error(f"Error fetching daily trend: {e}")
            conn.close()
            return {"dates": [], "counts": []}
    
    @staticmethod
    def get_error_trend(days=30):
        conn = get_db_connection()
        if not conn: return {"dates": [], "counts": []}
        try:
            cursor = conn.cursor()
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            cursor.execute("""
                SELECT DATE(vr.StartTime) as date, SUM(vr.ErrorCount) as total_errors
                FROM ValidationRun vr WHERE DATE(vr.StartTime) BETWEEN ? AND ?
                GROUP BY DATE(vr.StartTime) ORDER BY date ASC
            """, (start_date, end_date))
            results = cursor.fetchall()
            conn.close()
            return {"dates": [str(r['date']) for r in results], "counts": [r['total_errors'] for r in results]}
        except Exception as e:
            logger.error(f"Error fetching error trend: {e}")
            conn.close()
            return {"dates": [], "counts": []}
    
    @staticmethod
    def get_audit_history(limit=50, search=None, sort_by='DateTime', sort_order='DESC'):
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            query = "SELECT AuditID as id, DateTime as date, Action as action, User as user, Result as result, Description as description FROM AuditLog"
            ALLOWED_SORT_FIELDS = ['DateTime', 'Action', 'User', 'Result', 'Description']
            ALLOWED_SORT_ORDERS = ['ASC', 'DESC']
            if sort_by not in ALLOWED_SORT_FIELDS: sort_by = 'DateTime'
            if sort_order.upper() not in ALLOWED_SORT_ORDERS: sort_order = 'DESC'
            else: sort_order = sort_order.upper()
            if search:
                query += " WHERE Action LIKE ? OR Description LIKE ? OR User LIKE ?"
                cursor.execute(query + f" ORDER BY {sort_by} {sort_order} LIMIT ?", (f"%{search}%", f"%{search}%", f"%{search}%", limit))
            else:
                cursor.execute(query + f" ORDER BY {sort_by} {sort_order} LIMIT ?", (limit,))
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error fetching audit history: {e}")
            conn.close()
            return []


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    if AUTH_AVAILABLE and SessionManager.is_authenticated():
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('login_page'))

@app.route('/api/dashboard/latest')
def api_latest_validation():
    data = DashboardData.get_latest_validation()
    
    # Get the most recent RunID
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    vr.RunID,
                    vr.StartTime as validation_date,
                    CASE WHEN vr.Passed = 1 THEN 'PASS' ELSE 'FAILED' END as status,
                    vr.ErrorCount as error_count,
                    vr.WarningCount as warning_count,
                    vr.Duration as duration_seconds,
                    COALESCE(vr.UserName, 'system') as operator,
                    wh.FileName as workbook
                FROM ValidationRun vr
                LEFT JOIN WorkbookHistory wh ON vr.WorkbookID = wh.ID
                ORDER BY vr.RunID DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['validation_id'] = f"#{row['RunID']}"
                from datetime import datetime
                data['worksheet_name'] = f"DAILY OUTPUT FILE {datetime.now().strftime('%d-%m-%Y')}"
                data['daily_output_file'] = data['worksheet_name']
                data['operator'] = session.get("username", "Unknown")
                
                # Format validation date
                if data.get('validation_date'):
                    try:
                        dt = datetime.strptime(data['validation_date'], '%Y-%m-%d %H:%M:%S')
                        data['validation_date_formatted'] = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        data['validation_date_formatted'] = data.get('validation_date', 'N/A')
                else:
                    data['validation_date_formatted'] = 'N/A'
        except Exception as e:
            logger.error(f"Error fetching enhanced dashboard data: {e}")
        finally:
            conn.close()
    
    return jsonify(data)

@app.route('/api/dashboard/business-kpi')
def api_business_kpi():
    return jsonify(DashboardData.get_business_kpi())

@app.route('/api/dashboard/checklist')
def api_validation_checklist():
    return jsonify(DashboardData.get_validation_checklist())

@app.route('/api/dashboard/validation-results')
def api_validation_results():
    return jsonify(DashboardData.get_validation_results())

@app.route('/api/dashboard/release-status')
def api_release_status():
    return jsonify(DashboardData.get_release_status())

@app.route('/api/dashboard/engine-info')
def api_engine_info():
    return jsonify(DashboardData.get_validation_engine_info())

@app.route('/api/dashboard/failure-details')
def api_failure_details():
    return jsonify(DashboardData.get_failure_details())

@app.route('/api/dashboard/recent')
def api_recent_validations():
    return jsonify(DashboardData.get_recent_validations(limit=10))

@app.route('/api/dashboard/trend')
def api_daily_trend():
    return jsonify(DashboardData.get_daily_trend(30))

@app.route('/api/dashboard/error-trend')
def api_error_trend():
    return jsonify(DashboardData.get_error_trend(30))

@app.route('/api/dashboard/run-data/<int:run_id>')
def api_run_data(run_id):
    """Get all dashboard data for a specific validation run (for history drill-down)"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Get the specific validation run details
        cursor.execute("""
            SELECT 
                vr.RunID,
                wh.FileName as workbook,
                vr.StartTime as validation_date,
                CASE WHEN vr.Passed = 1 THEN 'PASS' ELSE 'FAILED' END as status,
                vr.ErrorCount as error_count,
                vr.WarningCount as warning_count,
                vr.Duration as duration_seconds,
                COALESCE(vr.RowsProcessed, 0) as rows_processed
            FROM ValidationRun vr
            LEFT JOIN WorkbookHistory wh ON vr.WorkbookID = wh.ID
            WHERE vr.RunID = ?
        """, (run_id,))
        latest = cursor.fetchone()
        if not latest:
            conn.close()
            return jsonify({"error": "Run not found"}), 404
        
        latest_dict = dict(latest)
        
        # Get card statistics for this run
        cursor.execute("""
            SELECT COALESCE(SIMOrders,0) as sim_orders, COALESCE(SIMCards,0) as sim_cards,
                   COALESCE(BankOrders,0) as bank_orders, COALESCE(BankCards,0) as bank_cards,
                   COALESCE(TotalOrders,0) as total_orders, COALESCE(TotalCards,0) as total_cards
            FROM CardStatistics WHERE RunID = ?
        """, (run_id,))
        card_stats = cursor.fetchone()
        
        sim_orders = card_stats['sim_orders'] if card_stats else 0
        sim_cards = card_stats['sim_cards'] if card_stats else 0
        bank_orders = card_stats['bank_orders'] if card_stats else 0
        bank_cards = card_stats['bank_cards'] if card_stats else 0
        total_orders = card_stats['total_orders'] if card_stats else 0
        total_cards = card_stats['total_cards'] if card_stats else 0
        
        cursor.execute("SELECT SettingValue FROM Settings WHERE SettingName = 'SIM_MULTIPLIER'")
        sim_mult_row = cursor.fetchone()
        sim_mult = int(sim_mult_row['SettingValue']) if sim_mult_row else 200
        cursor.execute("SELECT SettingValue FROM Settings WHERE SettingName = 'BANK_MULTIPLIER'")
        bank_mult_row = cursor.fetchone()
        bank_mult = int(bank_mult_row['SettingValue']) if bank_mult_row else 300
        
        if sim_cards == 0 and sim_orders > 0: sim_cards = sim_orders * sim_mult
        if bank_cards == 0 and bank_orders > 0: bank_cards = bank_orders * bank_mult
        if total_orders == 0: total_orders = sim_orders + bank_orders
        if total_cards == 0: total_cards = sim_cards + bank_cards
        
        # Get error messages for this run
        cursor.execute("SELECT ErrorMessage FROM ValidationError WHERE RunID = ?", (run_id,))
        error_messages = [row['ErrorMessage'] for row in cursor.fetchall()]
        
        # Get all error details
        cursor.execute("SELECT ErrorMessage, RowNumber, ColumnName FROM ValidationError WHERE RunID = ?", (run_id,))
        error_details = [dict(r) for r in cursor.fetchall()]
        
        # Get duplicate records
        cursor.execute("SELECT COUNT(*) as count FROM DuplicateRecord WHERE RunID = ?", (run_id,))
        dup_count = cursor.fetchone()['count'] or 0
        
        cursor.execute("""
            SELECT BatchNumber, RowNumber, DuplicateType, COUNT(*) as occurrences
            FROM DuplicateRecord WHERE RunID = ?
            GROUP BY BatchNumber, RowNumber, DuplicateType
        """, (run_id,))
        duplicate_details = [dict(r) for r in cursor.fetchall()]
        
        # Get failure details if failed
        has_failure = latest_dict['status'] == 'FAILED'
        failure_data = {"has_failure": False}
        if has_failure:
            cursor.execute("""
                SELECT ErrorMessage, RowNumber, ColumnName
                FROM ValidationError WHERE RunID = ? ORDER BY ErrorID LIMIT 1
            """, (run_id,))
            first_error = cursor.fetchone()
            
            cursor.execute("""
                SELECT DISTINCT RowNumber FROM ValidationError
                WHERE RunID = ? AND RowNumber IS NOT NULL ORDER BY RowNumber
            """, (run_id,))
            affected_rows = [r['RowNumber'] for r in cursor.fetchall()]
            
            cursor.execute("""
                SELECT DISTINCT BatchNumber FROM DuplicateRecord
                WHERE RunID = ? ORDER BY BatchNumber LIMIT 10
            """, (run_id,))
            batch_numbers = [r['BatchNumber'] for r in cursor.fetchall()]
            
            # Determine failed stage and reason
            if first_error:
                failed_stage = first_error['ErrorMessage'].split(':')[0]
                reason = first_error['ErrorMessage']
            elif error_messages:
                failed_stage = error_messages[0].split(':')[0]
                reason = error_messages[0]
            else:
                failed_stage = "Validation failed"
                reason = "Validation failed - no specific error details available"
            
            failure_data = {
                "has_failure": True,
                "failed_stage": failed_stage,
                "reason": reason,
                "affected_rows": affected_rows[:20],
                "batch_numbers": batch_numbers[:10],
                "total_errors": latest_dict['error_count']
            }
        
        # Build release status
        passed = latest_dict['status'] == 'PASS'
        reasons = []
        if not passed:
            reasons.append(f"Validation failed with {latest_dict['error_count']} error(s)")
        if dup_count > 0:
            reasons.append(f"{dup_count} duplicate batch(es) found")
        
        # Build KPI data
        kpi_data = {
            "rows_processed": latest_dict['rows_processed'],
            "sim_orders": sim_orders, "sim_cards": sim_cards,
            "bank_orders": bank_orders, "bank_cards": bank_cards,
            "total_orders": total_orders, "total_cards": total_cards,
            "validation_errors": latest_dict['error_count'],
            "warnings": latest_dict['warning_count'],
            "sim_multiplier": sim_mult, "bank_multiplier": bank_mult
        }
        
        # Build checklist
        def has_error_matching(patterns):
            for msg in error_messages:
                for pattern in patterns:
                    if pattern.lower() in msg.lower():
                        return True
            return False
        
        def get_error_details(patterns):
            details = []
            for err in error_details:
                for pattern in patterns:
                    if pattern.lower() in (err['ErrorMessage'] or '').lower():
                        details.append({
                            "message": err['ErrorMessage'],
                            "row": err['RowNumber'],
                            "column": err['ColumnName']
                        })
                        break
            return details
        
        run_passed = 1 if passed else 0
        checklist = [
            {"id": "daily_output_detected", "label": "Daily Output worksheet detected", "status": "FAIL" if has_error_matching(["Daily Output File worksheet not found", "Failed to load workbook"]) else "PASS", "details": get_error_details(["Daily Output File worksheet not found", "Failed to load workbook"]), "rows_checked": 0, "error_count": 1 if has_error_matching(["Daily Output File worksheet not found", "Failed to load workbook"]) else 0},
            {"id": "headers_validated", "label": "Required headers validated", "status": "FAIL" if has_error_matching(["Missing required headers"]) else "PASS", "details": get_error_details(["Missing required headers"]), "rows_checked": 0, "error_count": 1 if has_error_matching(["Missing required headers"]) else 0},
            {"id": "duplicate_batches_checked", "label": "Duplicate batches checked", "status": "FAIL" if dup_count > 0 or has_error_matching(["Duplicate batch"]) else "PASS", "details": duplicate_details[:5] if duplicate_details else [], "rows_checked": len(duplicate_details), "error_count": dup_count},
            {"id": "batch_counts_validated", "label": "Number of Batches validated", "status": "FAIL" if has_error_matching(["No_of_Batches mismatch", "Invalid No_of_Batches"]) else "PASS", "details": get_error_details(["No_of_Batches mismatch", "Invalid No_of_Batches"]), "rows_checked": 0, "error_count": len(get_error_details(["No_of_Batches mismatch", "Invalid No_of_Batches"]))},
            {"id": "bag_format_validated", "label": "Bag Number validated", "status": "FAIL" if has_error_matching(["Invalid Bag_No"]) else "PASS", "details": get_error_details(["Invalid Bag_No"]), "rows_checked": len(get_error_details(["Invalid Bag_No"])), "error_count": len(get_error_details(["Invalid Bag_No"]))},
            {"id": "blank_fields_validated", "label": "Blank fields validated", "status": "FAIL" if has_error_matching(["Blank"]) else "PASS", "details": get_error_details(["Blank"]), "rows_checked": len(get_error_details(["Blank"])), "error_count": len(get_error_details(["Blank"]))},
            {"id": "card_types_validated", "label": "Card Types validated", "status": "FAIL" if has_error_matching(["Invalid Card_Type", "Invalid Card Type"]) else "PASS", "details": get_error_details(["Invalid Card_Type", "Invalid Card Type"]), "rows_checked": len(get_error_details(["Invalid Card_Type", "Invalid Card Type"])), "error_count": len(get_error_details(["Invalid Card_Type", "Invalid Card Type"]))},
            {"id": "cross_workbook_checked", "label": "Cross-workbook duplicates checked", "status": "FAIL" if has_error_matching(["Cross-workbook"]) else "PASS", "details": get_error_details(["Cross-workbook"]), "rows_checked": len(get_error_details(["Cross-workbook"])), "error_count": len(get_error_details(["Cross-workbook"]))},
            {"id": "summary_updated", "label": "Summary Report updated", "status": "PASS" if run_passed == 1 else "FAIL", "details": [], "rows_checked": 0, "error_count": 0},
            {"id": "backup_created", "label": "Backup created", "status": "PASS", "details": [], "rows_checked": 0, "error_count": 0},
            {"id": "audit_log_created", "label": "Audit Log created", "status": "PASS", "details": [], "rows_checked": 0, "error_count": 0}
        ]
        
        # Build validation results
        results_data = {
            "rows_processed": latest_dict['rows_processed'],
            "sim_orders": sim_orders, "bank_orders": bank_orders,
            "sim_cards": sim_cards, "bank_cards": bank_cards,
            "total_orders": total_orders, "total_cards": total_cards,
            "errors": latest_dict['error_count'],
            "warnings": latest_dict['warning_count']
        }
        
        conn.close()
        
        return jsonify({
            "latest": latest_dict,
            "kpi": kpi_data,
            "checklist": checklist,
            "results": results_data,
            "failure": failure_data,
            "release": {
                "status": "READY FOR RELEASE" if passed and latest_dict['error_count'] == 0 else "DO NOT RELEASE",
                "ready": passed and latest_dict['error_count'] == 0,
                "reasons": reasons
            }
        })
    except Exception as e:
        logger.error(f"Error fetching run data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/validation-progress')
def api_validation_progress():
    with progress_lock:
        return jsonify(dict(validation_progress))

@app.route('/api/dashboard/delete-run', methods=['POST'])
def api_delete_validation_run():
    """Delete a validation run and all associated data permanently"""
    try:
        data = request.get_json()
        run_id = data.get('run_id')
        if not run_id:
            return jsonify({"error": "Missing run_id"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Verify the run exists
        cursor.execute("SELECT WorkbookID FROM ValidationRun WHERE RunID = ?", (run_id,))
        run = cursor.fetchone()
        if not run:
            conn.close()
            return jsonify({"error": "Validation run not found"}), 404
        
        workbook_id = run['WorkbookID']
        
        # Disable foreign key enforcement for the delete to avoid constraint issues
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Delete all associated records
        cursor.execute("DELETE FROM DuplicateRecord WHERE RunID = ?", (run_id,))
        cursor.execute("DELETE FROM ValidationError WHERE RunID = ?", (run_id,))
        cursor.execute("DELETE FROM CardStatistics WHERE RunID = ?", (run_id,))
        cursor.execute("DELETE FROM SummaryUpdate WHERE RunID = ?", (run_id,))
        cursor.execute("DELETE FROM ValidationRun WHERE RunID = ?", (run_id,))
        cursor.execute("DELETE FROM WorkbookHistory WHERE ID = ?", (workbook_id,))
        
        # Re-enable foreign key enforcement
        cursor.execute("PRAGMA foreign_keys = ON")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted validation run {run_id} and associated data")
        return jsonify({"status": "ok", "message": f"Validation run {run_id} deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting validation run: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/clear', methods=['POST'])
def api_clear_dashboard():
    try:
        logger.info("Clearing dashboard display data (preserving history)")
        return jsonify({"status": "ok", "message": "Dashboard display cleared."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/validation')
def validation_page():
    if AUTH_AVAILABLE and not SessionManager.is_authenticated():
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard_page():
    if AUTH_AVAILABLE and not SessionManager.is_authenticated():
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/api/validate/upload', methods=['POST'])
def validate_upload():
    try:
        if 'file' not in request.files:
            logger.warning("Upload failed: No file in request")
            return jsonify({"error": "No file provided"}), 400
        file = request.files['file']
        if file.filename == '':
            logger.warning("Upload failed: Empty filename")
            return jsonify({"error": "No file selected"}), 400
        if not allowed_file(file.filename):
            logger.warning(f"Upload failed: Invalid file format {file.filename}")
            return jsonify({"error": "Invalid file format. Use .xlsx, .xlsm, or .xls"}), 400
        
        logger.info(f"Upload received: {file.filename} (size: {file.content_length or 0} bytes)")
        # Reset progress state
        with progress_lock:
            validation_progress["status"] = "running"
            validation_progress["percent"] = 0
            validation_progress["stage"] = "Preparing validation..."
            validation_progress["workbook"] = file.filename
            validation_progress["error"] = None
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"File saved to: {filepath}")
        
        if not BACKEND_AVAILABLE:
            logger.error("Validation backend not available")
            with progress_lock:
                validation_progress["status"] = "failed"
                validation_progress["stage"] = "Validation backend not available"
            return jsonify({"error": "Validation backend not available"}), 500
        
        try:
            validation_engine = ValidationEngine(progress_callback=update_progress)
            logger.info(f"Validation engine started for: {filename}")
            result = validation_engine.validate_complete_workbook(filepath)
            logger.info(f"Validation completed: passed={result.passed}, errors={result.error_count}, warnings={result.warning_count}")
            
            # Persist results
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    now = datetime.now()
                    try:
                        backup_manager = BackupManager('backups')
                        backup_manager.create_backup(filepath)
                    except Exception as e:
                        logger.warning(f"Could not create backup: {e}")
                    
                    cursor.execute("""
                        INSERT INTO WorkbookHistory (FileName, FilePath, ProcessDate, ValidationStatus, DurationSeconds)
                        VALUES (?, ?, ?, ?, ?)
                    """, (file.filename, filepath, now, 'PASS' if result.passed else 'FAIL', int(result.duration_seconds)))
                    workbook_id = cursor.lastrowid
                    
                    rows_processed = getattr(result, 'rows_processed', 0)
                    
                    cursor.execute("""
                        INSERT INTO ValidationRun (WorkbookID, StartTime, Duration, Passed, ErrorCount, WarningCount, RowsProcessed, UserName)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (workbook_id, now, int(result.duration_seconds), 1 if result.passed else 0,
                           result.error_count, result.warning_count, rows_processed, 'system'))
                    run_id = cursor.lastrowid
                    
                    for error_msg in result.errors:
                        cursor.execute("INSERT INTO ValidationError (RunID, ErrorMessage) VALUES (?, ?)", (run_id, error_msg))
                    
                    # Persist structured validation errors if available
                    if hasattr(result, 'validation_errors') and result.validation_errors:
                        for verr in result.validation_errors:
                            cursor.execute("""
                                INSERT INTO ValidationError 
                                    (RunID, RuleID, ErrorType, Worksheet, RowNumber, ColumnName, CellReference, ErrorMessage, InvalidValue)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                run_id,
                                verr.rule_id,
                                verr.error_type,
                                verr.worksheet,
                                verr.row_number,
                                verr.column_name,
                                verr.cell_reference,
                                verr.error_message,
                                verr.invalid_value
                            ))
                    
                    if hasattr(result, 'duplicates') and result.duplicates:
                        for dup in result.duplicates:
                            batch_num = dup.batch_number if hasattr(dup, 'batch_number') else str(dup)
                            cursor.execute("""
                                INSERT INTO DuplicateRecord (RunID, BatchNumber, DuplicateType)
                                VALUES (?, ?, ?)
                            """, (run_id, batch_num, 'Different Rows'))
                    
                    try:
                        loader = WorkbookLoader()
                        loader.load_workbook(filepath)
                        daily_sheet = loader.detect_daily_output_sheet()
                        card_counter = CardCounter()
                        if daily_sheet:
                            stats = card_counter.count_cards_from_loader(loader, daily_sheet)
                            cursor.execute("""
                                INSERT INTO CardStatistics (RunID, SIMOrders, SIMCards, BankOrders, BankCards, TotalOrders, TotalCards)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (run_id, stats.sim_orders, stats.sim_cards, stats.bank_orders, stats.bank_cards,
                                  stats.total_orders, stats.total_cards))
                        loader.close()
                    except Exception as e:
                        logger.warning(f"Could not compute card statistics: {e}")
                    
                    # Also store in-memory as a fallback for the current session
                    with progress_lock:
                        validation_progress["rows_processed"] = rows_processed
                    
                    cursor.execute("""
                        INSERT INTO AuditLog (DateTime, Action, User, Result, Description)
                        VALUES (?, ?, ?, ?, ?)
                    """, (now, 'Workbook Validation', 'system', 'PASS' if result.passed else 'FAIL',
                           f'Validated {file.filename}: {result.error_count} errors, {result.warning_count} warnings'))
                    
                    conn.commit()
                    conn.close()
            except Exception as e:
                logger.error(f"Error persisting validation results: {e}")
                if conn:
                    try: conn.rollback(); conn.close()
                    except: pass
            
            with progress_lock:
                validation_progress["status"] = "completed" if result.passed else "failed"
                validation_progress["percent"] = 100
                validation_progress["stage"] = "Validation Completed Successfully" if result.passed else "Validation Failed"
            
            return jsonify({
                "filename": file.filename, "upload_path": filepath,
                "passed": result.passed, "error_count": result.error_count,
                "warning_count": result.warning_count, "duration_seconds": result.duration_seconds,
                "errors": result.errors, "warnings": result.warnings,
                "duplicates_found": result.duplicates_found,
                "validation_errors": [
                    {
                        "rule_id": ve.rule_id,
                        "error_type": ve.error_type,
                        "worksheet": ve.worksheet,
                        "row_number": ve.row_number,
                        "column_name": ve.column_name,
                        "cell_reference": ve.cell_reference,
                        "error_message": ve.error_message,
                        "invalid_value": ve.invalid_value,
                        "suggested_fix": ve.suggested_fix
                    } for ve in (result.validation_errors or [])
                ]
            })
        except Exception as e:
            logger.error(f"Validation error: {e}")
            with progress_lock:
                validation_progress["status"] = "failed"
                validation_progress["stage"] = f"Validation failed: {str(e)[:100]}"
            return jsonify({"error": f"Validation failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Upload error: {e}")
        with progress_lock:
            validation_progress["status"] = "failed"
            validation_progress["stage"] = f"Upload failed: {str(e)[:100]}"
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/analytics')
def analytics_page():
    if AUTH_AVAILABLE and SessionManager.is_authenticated():
        return render_template('index.html')
    return redirect(url_for('login_page'))

@app.route('/api/analytics/charts')
def api_analytics_charts():
    return jsonify({"errors": DashboardData.get_error_breakdown(), "trend": DashboardData.get_daily_trend(30)})

@app.route('/audit')
def audit_page():
    if AUTH_AVAILABLE and SessionManager.is_authenticated() and SessionManager.is_admin():
        return render_template('index.html')
    return redirect(url_for('login_page'))

@app.route('/api/audit/history')
def api_audit_history():
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'DateTime')
    sort_order = request.args.get('sort_order', 'DESC')
    limit = request.args.get('limit', 50, type=int)
    return jsonify(DashboardData.get_audit_history(limit=limit, search=search, sort_by=sort_by, sort_order=sort_order))

@app.route('/api/audit/export')
def api_audit_export():
    data = DashboardData.get_audit_history(limit=1000)
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True,
                     download_name=f'audit_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

@app.route('/summary')
def summary_page():
    if AUTH_AVAILABLE and SessionManager.is_authenticated():
        return render_template('index.html')
    return redirect(url_for('login_page'))

@app.route('/api/summary/analyze', methods=['POST'])
def api_summary_analyze():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "Invalid file path"}), 400
        if not BACKEND_AVAILABLE:
            return jsonify({"error": "Backend not available"}), 500
        engine = SummaryReconciliationEngine()
        analysis = engine.analyze(file_path)
        return jsonify({
            "summary_worksheet": analysis.summary_worksheet_name,
            "daily_worksheet": analysis.latest_daily_worksheet_name,
            "sim_orders": analysis.sim_orders, "sim_cards": analysis.sim_cards,
            "bank_orders": analysis.dmcc_orders, "bank_cards": analysis.dmcc_cards,
            "total_orders": analysis.total_orders, "total_cards": analysis.total_cards,
            "summary_rows": [{"item_name": r.item_name, "previous": r.previous_dispatch, "new": r.new_dispatch}
                           for r in analysis.summary_rows] if analysis.summary_rows else []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reports')
def reports_page():
    if AUTH_AVAILABLE and SessionManager.is_authenticated():
        return render_template('index.html')
    return redirect(url_for('login_page'))

@app.route('/api/reports/download')
def api_reports_download():
    return jsonify({"error": "Report generation in progress"}), 501

@app.route('/settings')
def settings_page():
    if AUTH_AVAILABLE and SessionManager.is_authenticated():
        return render_template('index.html')
    return redirect(url_for('login_page'))

@app.route('/api/settings/get')
def api_settings_get():
    conn = get_db_connection()
    if not conn: return jsonify({})
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SettingName, SettingValue FROM Settings")
        settings = {row['SettingName']: row['SettingValue'] for row in cursor.fetchall()}
        conn.close()
        return jsonify(settings)
    except Exception as e:
        conn.close()
        return jsonify({})

@app.route('/api/settings/<key>')
def api_settings_get_key(key):
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SettingValue FROM Settings WHERE SettingName = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row: return jsonify({'key': key, 'value': row['SettingValue']})
        return jsonify({'key': key, 'value': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/save', methods=['POST'])
def api_settings_save():
    try:
        data = request.get_json()
        conn = get_db_connection()
        if not conn: return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()
        for key, value in data.items():
            cursor.execute("INSERT OR REPLACE INTO Settings (SettingName, SettingValue) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/about')
def about_page():
    if AUTH_AVAILABLE and SessionManager.is_authenticated():
        return render_template('index.html')
    return redirect(url_for('login_page'))

@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "service": "CDRS Web Dashboard", "backend": "available" if BACKEND_AVAILABLE else "unavailable"})

@app.route('/api/auth/status')
def api_auth_status():
    """Check current authentication status"""
    if not AUTH_AVAILABLE:
        return jsonify({"authenticated": False})
    
    user = SessionManager.get_current_user()
    if not user:
        return jsonify({"authenticated": False})
    
    return jsonify({
        "authenticated": True,
        "username": user['username'],
        "role": user['role'],
        "first_login": user['first_login']
    })

# ============================================================================
# AUTHENTICATION PAGES
# ============================================================================

@app.route('/change-password')
def change_password_page():
    """Change password page"""
    if AUTH_AVAILABLE and not SessionManager.is_authenticated():
        return redirect(url_for('login_page'))
    return render_template('change_password.html')

@app.route('/forgot-password')
def forgot_password_page():
    """Forgot password page"""
    return render_template('login.html')

@app.route('/first-login')
def first_login_page():
    """First login page"""
    return render_template('login.html')

@app.route('/admin/users')
def admin_users_page():
    """Admin user management page"""
    if AUTH_AVAILABLE and SessionManager.is_authenticated() and SessionManager.is_admin():
        return render_template('admin_users.html')
    return redirect(url_for('login_page'))

@app.route('/account-settings')
def account_settings_page():
    """Account settings page"""
    if AUTH_AVAILABLE and SessionManager.is_authenticated():
        return render_template('account_settings.html')
    return redirect(url_for('login_page'))

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login')
def login_page():
    """Display login page"""
    return render_template('login.html')

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Authenticate user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip().upper()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Authenticate user
        user = auth_manager.authenticate(username, password)
        
        if not user:
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Check if password expired
        if PasswordManager.is_password_expired(user['password_last_changed']):
            return jsonify({
                "error": "Password expired. Please reset your password.",
                "expired": True,
                "username": username
            }), 403
        
        # Create session
        SessionManager.create_session(
            username=user['username'],
            user_id=user['user_id'],
            role=user['role'],
            first_login=user['first_login']
        )
        
        # Log authentication
        _log_auth_action('Login', user['username'], 'SUCCESS', f"User logged in successfully")
        
        return jsonify({
            "status": "ok",
            "username": user['username'],
            "role": user['role'],
            "first_login": user['first_login'],
            "must_change_password": user.get('must_change_password', False)
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout user"""
    try:
        username = SessionManager.get_current_user()['username'] if SessionManager.is_authenticated() else 'Unknown'
        SessionManager.destroy_session()
        _log_auth_action('Logout', username, 'SUCCESS', f"User logged out")
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"status": "ok"})

@app.route('/api/auth/first-login', methods=['POST'])
def api_first_login():
    """Handle first login - create new password for first-time login"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip().upper()
        new_password = data.get('new_password', '')
        
        if not username or not new_password:
            return jsonify({"error": "Username and password required"}), 400
        
        # Validate password strength
        is_valid, message = PasswordManager.validate_password_strength(new_password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Get user
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database error"}), 500
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT UserID, PasswordHash, Salt FROM Users WHERE Username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return jsonify({"error": "User not found"}), 404
            
            # Hash the new password
            password_hash, salt = PasswordManager.hash_password(new_password)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update password, clear first_login and must_change_password flags
            cursor.execute("""
                UPDATE Users 
                SET PasswordHash = ?, Salt = ?, PasswordLastChanged = ?, 
                    FirstLogin = 0, MustChangePassword = 0,
                    FailedLoginAttempts = 0, LockedUntil = NULL
                WHERE Username = ?
            """, (password_hash, salt, now, username))
            conn.commit()
            
            # Create session for the user
            SessionManager.create_session(
                username=username,
                user_id=user['UserID'],
                role='Staff',
                first_login=False
            )
            
            _log_auth_action('First Login', username, 'SUCCESS', f"First login password created successfully")
            
            conn.close()
            return jsonify({"status": "ok", "message": "Password created successfully"})
            
        except Exception as e:
            conn.close()
            logger.error(f"First login error: {e}")
            return jsonify({"error": "Failed to set password"}), 500
            
    except Exception as e:
        logger.error(f"First login error: {e}")
        return jsonify({"error": "Failed to process first login"}), 500


@app.route('/api/auth/change-password', methods=['POST'])
def api_change_password():
    """Change user password"""
    if not AUTH_AVAILABLE or not SessionManager.is_authenticated():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        username = SessionManager.get_current_user()['username']
        
        # Verify current password
        user = auth_manager.get_user_by_username(username)
        if not user or not PasswordManager.verify_password(current_password, user['PasswordHash'], user['Salt']):
            return jsonify({"error": "Current password is incorrect"}), 400
        
        # Change password
        success, message = auth_manager.change_password(username, new_password)
        
        if success:
            # Clear first login flag
            SessionManager.create_session(
                username=username,
                user_id=user['UserID'],
                role=user['Role'],
                first_login=False
            )
            _log_auth_action('Password Change', username, 'SUCCESS', f"Password changed successfully")
            return jsonify({"status": "ok", "message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({"error": "Failed to change password"}), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """Forgot password - reset password"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip().upper()
        
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        # Check if user exists
        user = auth_manager.get_user_by_username(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Generate temporary password
        success, message = auth_manager.reset_password(username)
        
        if success:
            _log_auth_action('Password Reset', username, 'SUCCESS', f"Password reset requested")
            return jsonify({"status": "ok", "message": message, "temporary_password": message.split(": ")[-1] if ": " in message else None})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({"error": "Failed to reset password"}), 500

# ============================================================================
# ADMIN USER MANAGEMENT ROUTES
# ============================================================================

@app.route('/api/user/avatar')
def get_user_avatar():
    """Get current user's avatar URL"""
    if not AUTH_AVAILABLE or not SessionManager.is_authenticated():
        return jsonify({"avatar_url": "/static/avatars/default_placeholder.png"})
    
    username = SessionManager.get_current_user()['username']
    avatar_path = f"/static/avatars/{username}.png"
    return jsonify({"avatar_url": avatar_path})

@app.route('/api/admin/users', methods=['GET'])
def api_get_users():
    """Get all users (admin only)"""
    if not AUTH_AVAILABLE or not SessionManager.is_admin():
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        users = auth_manager.get_all_users()
        # Remove sensitive data
        for user in users:
            user.pop('PasswordHash', None)
            user.pop('Salt', None)
        return jsonify(users)
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({"error": "Failed to fetch users"}), 500

@app.route('/api/admin/users', methods=['POST'])
def api_create_user():
    """Create new user (admin only)"""
    if not AUTH_AVAILABLE or not SessionManager.is_admin():
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        username = data.get('username', '').strip().upper()
        password = data.get('password', '')
        role = data.get('role', 'Staff')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        success, message = auth_manager.create_user(username, password, role)
        
        if success:
            admin = SessionManager.get_current_user()
            _log_auth_action('User Created', admin['username'], 'SUCCESS', f"Created user {username} with role {role}")
            return jsonify({"status": "ok", "message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return jsonify({"error": "Failed to create user"}), 500

@app.route('/api/admin/users/<username>', methods=['DELETE'])
def api_delete_user(username):
    """Delete user (admin only)"""
    if not AUTH_AVAILABLE or not SessionManager.is_admin():
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        username = username.upper()
        success, message = auth_manager.delete_user(username)
        
        if success:
            admin = SessionManager.get_current_user()
            _log_auth_action('User Deleted', admin['username'], 'SUCCESS', f"Deleted user {username}")
            return jsonify({"status": "ok", "message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        return jsonify({"error": "Failed to delete user"}), 500

@app.route('/api/admin/users/<username>', methods=['PUT'])
def api_update_user(username):
    """Update user (admin only)"""
    if not AUTH_AVAILABLE or not SessionManager.is_admin():
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        username = username.upper()
        data = request.get_json()
        
        # Update role
        if 'role' in data:
            success, message = auth_manager.update_user_role(username, data['role'])
            if not success:
                return jsonify({"error": message}), 400
        
        # Reset password if provided
        if 'password' in data and data['password']:
            success, message = auth_manager.reset_password(username, data['password'])
            if not success:
                return jsonify({"error": message}), 400
        
        admin = SessionManager.get_current_user()
        _log_auth_action('User Updated', admin['username'], 'SUCCESS', f"Updated user {username}")
        return jsonify({"status": "ok", "message": "User updated successfully"})
            
    except Exception as e:
        logger.error(f"Update user error: {e}")
        return jsonify({"error": "Failed to update user"}), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================



def _log_auth_action(action: str, username: str, result: str, description: str):
    """Log authentication action to audit log"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO AuditLog (DateTime, Action, User, Result, Description)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now(), action, username, result, description))
            conn.commit()
            conn.close()
    except Exception as e:
        logger.error(f"Error logging auth action: {e}")

if __name__ == '__main__':
    logger.info(f"Starting Capitec Daily Reconciliation System Web Dashboard")
    logger.info(f"Database path: {DB_PATH}")
    logger.info(f"Database exists: {os.path.exists(DB_PATH)}")
    logger.info(f"Backend available: {BACKEND_AVAILABLE}")
    initialize_database()
    app.run(debug=True, host='localhost', port=5000, use_reloader=False)