"""
Authentication Manager for Capitec Daily Reconciliation System
Handles user authentication, password management, and session control
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import sqlite3
import os


class PasswordManager:
    """Handles password hashing, validation, and expiry"""
    
    SALT_LENGTH = 16
    HASH_ITERATIONS = 100000
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_EXPIRY_DAYS = 30
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash a password with PBKDF2 using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(PasswordManager.SALT_LENGTH)
        
        # Use PBKDF2 with SHA-256
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            PasswordManager.HASH_ITERATIONS
        )
        
        password_hash = hash_bytes.hex()
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify a password against stored hash"""
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            PasswordManager.HASH_ITERATIONS
        )
        return hash_bytes.hex() == stored_hash
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """Validate password meets requirements:
        - Minimum 8 characters
        - At least one number
        - At least one uppercase letter
        """
        if len(password) < PasswordManager.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {PasswordManager.MIN_PASSWORD_LENGTH} characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        return True, "Password meets requirements"
    
    @staticmethod
    def is_password_expired(last_changed: str) -> bool:
        """Check if password has expired (30 days)"""
        try:
            changed_date = datetime.strptime(last_changed, '%Y-%m-%d %H:%M:%S')
            expiry_date = changed_date + timedelta(days=PasswordManager.PASSWORD_EXPIRY_DAYS)
            return datetime.now() > expiry_date
        except:
            return True


class AuthManager:
    """Main authentication manager"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_connection(self) -> Optional[sqlite3.Connection]:
        """Get database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password"""
        conn = self._get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT UserID, Username, PasswordHash, Salt, Role, AccountStatus, 
                       PasswordLastChanged, FirstLogin, FailedLoginAttempts, LockedUntil,
                       MustChangePassword
                FROM Users 
                WHERE Username = ?
            """, (username,))
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return None
            
            # Check if account is locked
            if user['LockedUntil']:
                locked_until = datetime.strptime(user['LockedUntil'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() < locked_until:
                    return None
                else:
                    # Unlock account
                    self._unlock_account(username)
            
            # Check account status
            if user['AccountStatus'] != 'ACTIVE':
                return None
            
            # Verify password
            if not PasswordManager.verify_password(password, user['PasswordHash'], user['Salt']):
                self._record_failed_login(username)
                return None
            
            # Reset failed login attempts on successful auth
            self._reset_failed_logins(username)
            
            return {
                'user_id': user['UserID'],
                'username': user['Username'],
                'role': user['Role'],
                'first_login': user['FirstLogin'],
                'password_last_changed': user['PasswordLastChanged'],
                'must_change_password': user['MustChangePassword']
            }
            
        except Exception as e:
            print(f"Authentication error: {e}")
            if conn:
                conn.close()
            return None
    
    def _record_failed_login(self, username: str):
        """Record failed login attempt"""
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT FailedLoginAttempts FROM Users WHERE Username = ?", (username,))
            user = cursor.fetchone()
            
            if user:
                attempts = (user['FailedLoginAttempts'] or 0) + 1
                
                # Lock account after 5 failed attempts for 15 minutes
                locked_until = None
                if attempts >= 5:
                    locked_until = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
                
                cursor.execute("""
                    UPDATE Users 
                    SET FailedLoginAttempts = ?, LockedUntil = ?
                    WHERE Username = ?
                """, (attempts, locked_until, username))
                conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"Error recording failed login: {e}")
            if conn:
                conn.close()
    
    def _reset_failed_logins(self, username: str):
        """Reset failed login attempts"""
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Users 
                SET FailedLoginAttempts = 0, LockedUntil = NULL
                WHERE Username = ?
            """, (username,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error resetting failed logins: {e}")
            if conn:
                conn.close()
    
    def _unlock_account(self, username: str):
        """Unlock a timed-locked account"""
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Users 
                SET FailedLoginAttempts = 0, LockedUntil = NULL
                WHERE Username = ?
            """, (username,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error unlocking account: {e}")
            if conn:
                conn.close()
    
    def change_password(self, username: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        # Validate password strength
        is_valid, message = PasswordManager.validate_password_strength(new_password)
        if not is_valid:
            return False, message
        
        conn = self._get_connection()
        if not conn:
            return False, "Database error"
        
        try:
            password_hash, salt = PasswordManager.hash_password(new_password)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Users 
                SET PasswordHash = ?, Salt = ?, PasswordLastChanged = ?, FirstLogin = 0, MustChangePassword = 0
                WHERE Username = ?
            """, (password_hash, salt, now, username))
            
            conn.commit()
            conn.close()
            return True, "Password changed successfully"
            
        except Exception as e:
            print(f"Error changing password: {e}")
            if conn:
                conn.close()
            return False, "Failed to change password"
    
    def reset_password(self, username: str, new_password: Optional[str] = None) -> Tuple[bool, str]:
        """Reset password (admin function)"""
        if new_password is None:
            # Generate temporary password
            new_password = secrets.token_urlsafe(12)
        
        # Validate if provided
        if new_password:
            is_valid, message = PasswordManager.validate_password_strength(new_password)
            if not is_valid:
                return False, message
        
        conn = self._get_connection()
        if not conn:
            return False, "Database error"
        
        try:
            # Ensure user exists before updating
            cursor = conn.cursor()
            cursor.execute("SELECT UserID FROM Users WHERE Username = ?", (username,))
            if not cursor.fetchone():
                conn.close()
                return False, "User not found"
            
            password_hash, salt = PasswordManager.hash_password(new_password)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                UPDATE Users 
                SET PasswordHash = ?, Salt = ?, PasswordLastChanged = ?, FirstLogin = 0, 
                    FailedLoginAttempts = 0, LockedUntil = NULL, MustChangePassword = 1
                WHERE Username = ?
            """, (password_hash, salt, now, username))
            
            conn.commit()
            conn.close()
            return True, f"Password reset. Temporary password: {new_password}"
            
        except Exception as e:
            print(f"Error resetting password: {e}")
            if conn:
                conn.close()
            return False, "Failed to reset password"
    
    def create_user(self, username: str, password: str, role: str, force_first_login: bool = True) -> Tuple[bool, str]:
        """Create a new user"""
        # Validate username (no spaces, uppercase with underscores)
        if ' ' in username or not re.match(r'^[A-Z][A-Z0-9_]*$', username):
            return False, "Username must be uppercase with underscores (no spaces)"
        
        # Validate password
        is_valid, message = PasswordManager.validate_password_strength(password)
        if not is_valid:
            return False, message
        
        conn = self._get_connection()
        if not conn:
            return False, "Database error"
        
        try:
            # Check if user exists
            cursor = conn.cursor()
            cursor.execute("SELECT UserID FROM Users WHERE Username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False, "User already exists"
            
            password_hash, salt = PasswordManager.hash_password(password)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            first_login = 1 if force_first_login else 0
            
            cursor.execute("""
                INSERT INTO Users (Username, PasswordHash, Salt, Role, AccountStatus, 
                                  PasswordLastChanged, FirstLogin, CreatedAt)
                VALUES (?, ?, ?, ?, 'ACTIVE', ?, ?, ?)
            """, (username, password_hash, salt, role, now, first_login, now))
            
            conn.commit()
            conn.close()
            return True, "User created successfully"
            
        except Exception as e:
            print(f"Error creating user: {e}")
            if conn:
                conn.close()
            return False, "Failed to create user"
    
    def delete_user(self, username: str) -> Tuple[bool, str]:
        """Delete a user"""
        if username == 'ADMIN':
            return False, "Cannot delete the main admin account"
        
        conn = self._get_connection()
        if not conn:
            return False, "Database error"
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Users WHERE Username = ?", (username,))
            conn.commit()
            conn.close()
            return True, "User deleted successfully"
            
        except Exception as e:
            print(f"Error deleting user: {e}")
            if conn:
                conn.close()
            return False, "Failed to delete user"
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (for admin panel)"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT UserID, Username, Role, AccountStatus, PasswordLastChanged, 
                       FirstLogin, FailedLoginAttempts, LockedUntil, CreatedAt
                FROM Users
                ORDER BY Username
            """)
            
            users = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return users
            
        except Exception as e:
            print(f"Error fetching users: {e}")
            if conn:
                conn.close()
            return []
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user details by username"""
        conn = self._get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT UserID, Username, Role, AccountStatus, PasswordLastChanged, 
                       FirstLogin, CreatedAt
                FROM Users
                WHERE Username = ?
            """, (username,))
            
            user = cursor.fetchone()
            conn.close()
            return dict(user) if user else None
            
        except Exception as e:
            print(f"Error fetching user: {e}")
            if conn:
                conn.close()
            return None
    
    def update_user_role(self, username: str, new_role: str) -> Tuple[bool, str]:
        """Update user role"""
        if username == 'ADMIN':
            return False, "Cannot modify the main admin account"
        
        if new_role not in ['Admin', 'Staff']:
            return False, "Invalid role"
        
        conn = self._get_connection()
        if not conn:
            return False, "Database error"
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Users SET Role = ? WHERE Username = ?
            """, (new_role, username))
            conn.commit()
            conn.close()
            return True, "Role updated successfully"
            
        except Exception as e:
            print(f"Error updating role: {e}")
            if conn:
                conn.close()
            return False, "Failed to update role"


class SessionManager:
    """Session management utilities"""
    
    SESSION_KEY = 'user_id'
    ROLE_KEY = 'user_role'
    USERNAME_KEY = 'username'
    FIRST_LOGIN_KEY = 'first_login'
    
    @staticmethod
    def create_session(username: str, user_id: int, role: str, first_login: bool = False):
        """Create user session"""
        from flask import session
        session[SessionManager.SESSION_KEY] = user_id
        session[SessionManager.ROLE_KEY] = role
        session[SessionManager.USERNAME_KEY] = username
        session[SessionManager.FIRST_LOGIN_KEY] = first_login
        session.permanent = True
    
    @staticmethod
    def destroy_session():
        """Destroy user session"""
        from flask import session
        session.clear()
    
    @staticmethod
    def get_current_user() -> Optional[Dict]:
        """Get current logged-in user info"""
        from flask import session
        if SessionManager.SESSION_KEY not in session:
            return None
        
        return {
            'user_id': session.get(SessionManager.SESSION_KEY),
            'username': session.get(SessionManager.USERNAME_KEY),
            'role': session.get(SessionManager.ROLE_KEY),
            'first_login': session.get(SessionManager.FIRST_LOGIN_KEY, False)
        }
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        from flask import session
        return SessionManager.SESSION_KEY in session
    
    @staticmethod
    def is_admin() -> bool:
        """Check if current user is admin"""
        from flask import session
        return session.get(SessionManager.ROLE_KEY) == 'Admin'
    
    @staticmethod
    def is_staff() -> bool:
        """Check if current user is staff"""
        from flask import session
        return session.get(SessionManager.ROLE_KEY) == 'Staff'
    
    @staticmethod
    def require_auth():
        """Decorator to require authentication"""
        from flask import redirect, url_for, request
        def decorator(f):
            def wrapper(*args, **kwargs):
                if not SessionManager.is_authenticated():
                    return redirect(url_for('login_page', next=request.url))
                return f(*args, **kwargs)
            wrapper.__name__ = f.__name__
            return wrapper
        return decorator
    
    @staticmethod
    def require_admin():
        """Decorator to require admin role"""
        from flask import redirect, url_for, request
        def decorator(f):
            def wrapper(*args, **kwargs):
                if not SessionManager.is_authenticated():
                    return redirect(url_for('login_page', next=request.url))
                if not SessionManager.is_admin():
                    return redirect(url_for('index'))
                return f(*args, **kwargs)
            wrapper.__name__ = f.__name__
            return wrapper
        return decorator