"""
Audit Manager Module - Handles audit logging.
"""

from datetime import datetime
from typing import Optional
from src.models.models import AuditLogEntry
from src.database.database import get_database
from src.utils.logger import get_logger


class AuditManager:
    """
    Manages audit log records.
    
    Records all validation runs, updates, errors, and
    other significant application events to the database.
    """

    def __init__(self) -> None:
        """Initialize the Audit Manager."""
        self.logger = get_logger()
        self.db = get_database()

    def log_action(self, action: str, user: Optional[str] = None,
                   result: str = "Success", description: str = "") -> bool:
        """
        Log an action to the audit log.
        
        Args:
            action: Description of the action.
            user: User who performed the action.
            result: Result of the action (Success/Failure/Warning).
            description: Detailed description.
            
        Returns:
            True if log successful, False otherwise.
        """
        try:
            entry = AuditLogEntry(
                action=action,
                user=user,
                result=result,
                description=description
            )
            
            # Insert into database
            data = {
                'DateTime': entry.timestamp.isoformat(),
                'Action': entry.action,
                'User': entry.user,
                'Result': entry.result,
                'Description': entry.description
            }
            
            self.db.insert('AuditLog', data)
            self.logger.info(f"Audit logged: {action}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging audit: {e}")
            return False

    def get_audit_history(self, limit: int = 100) -> list:
        """
        Get audit history.
        
        Args:
            limit: Maximum number of records to retrieve.
            
        Returns:
            List of audit records.
        """
        try:
            query = "SELECT * FROM AuditLog ORDER BY DateTime DESC LIMIT ?"
            results = self.db.query(query, (limit,))
            return results
            
        except Exception as e:
            self.logger.error(f"Error retrieving audit history: {e}")
            return []
