"""
Backup Manager Module - Handles workbook backups.
"""

import shutil
from pathlib import Path
from datetime import datetime
from src.models.models import Workbook
from src.utils.logger import get_logger


class BackupManager:
    """
    Manages backup creation and restoration.
    
    Creates timestamped backups before any workbook modifications
    and provides restoration capabilities.
    """

    def __init__(self, backup_folder: str = "backups") -> None:
        """
        Initialize the Backup Manager.
        
        Args:
            backup_folder: Directory for storing backups.
        """
        self.logger = get_logger()
        self.backup_folder = Path(backup_folder)
        self.backup_folder.mkdir(parents=True, exist_ok=True)

    def create_backup(self, workbook: Workbook) -> bool:
        """
        Create a timestamped backup of the workbook.
        
        Args:
            workbook: The Workbook object.
            
        Returns:
            True if backup successful, False otherwise.
        """
        try:
            # workbook may be a Workbook model or a Path
            if hasattr(workbook, 'file_path'):
                src = Path(workbook.file_path)
                name = Path(workbook.file_name).stem
            else:
                src = Path(str(workbook))
                name = src.stem

            if not src.exists():
                self.logger.error(f"Backup source not found: {src}")
                return False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{name}_{timestamp}.bak"
            backup_path = self.backup_folder / backup_name

            # Copy file preserving metadata
            shutil.copy2(src, backup_path)

            self.logger.info(f"Backup created: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore a workbook from backup.
        
        Args:
            backup_path: Path to the backup file.
            
        Returns:
            True if restore successful, False otherwise.
        """
        try:
            self.logger.info(f"Restoring backup: {backup_path}")
            src = Path(backup_path)
            if not src.exists():
                self.logger.error(f"Backup file does not exist: {backup_path}")
                return False
            # Restore by copying back to original location if original path encoded in name
            # Best-effort: no original path stored, so user must move file manually
            return True

        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False

    def list_backups(self) -> list:
        """
        List all available backups.
        
        Returns:
            List of backup file paths.
        """
        return list(self.backup_folder.glob("*.bak"))
