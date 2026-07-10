"""
Capitec Daily Reconciliation System (CDRS) - Main Application Entry Point.

Version: 1.0.0

This is the main entry point for the application. It initializes the system,
loads configuration, and launches the GUI.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from src.utils.logger import get_logger, Logger
from src.utils.settings_manager import get_settings
from src.database.database import get_database
from src.gui.dashboard import Dashboard


def main() -> int:
    """
    Main application entry point.
    
    Initializes logging, settings, database, and launches the GUI.
    
    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        # Initialize logger
        logger = get_logger()
        logger.info("=" * 60)
        logger.info("Capitec Daily Reconciliation System (CDRS) Starting...")
        logger.info("=" * 60)
        
        # Load settings
        settings = get_settings()
        app_name = settings.get('application.name', 'CDRS')
        app_version = settings.get('application.version', '1.0.0')
        logger.info(f"Application: {app_name} v{app_version}")
        
        # Initialize database
        logger.info("Initializing database...")
        db = get_database()
        logger.info("Database initialized successfully")
        
        # Create Qt application
        logger.info("Initializing GUI...")
        qt_app = QApplication(sys.argv)
        
        # Create and show main dashboard
        dashboard = Dashboard()
        dashboard.show()
        
        logger.info("Application started successfully")
        logger.info(f"Window Title: {app_name}")
        
        # Run application event loop
        exit_code = qt_app.exec()
        
        # Cleanup
        logger.info("Shutting down...")
        db.close()
        logger.info("=" * 60)
        logger.info("Capitec Daily Reconciliation System (CDRS) Closed")
        logger.info("=" * 60)
        
        return exit_code
        
    except Exception as e:
        error_msg = f"Fatal error: {str(e)}"
        logger = get_logger()
        logger.critical(error_msg)
        
        # Show error dialog
        try:
            qt_app = QApplication.instance()
            if qt_app is None:
                qt_app = QApplication(sys.argv)
            
            QMessageBox.critical(
                None,
                "Application Error",
                f"Fatal error occurred:\\n\\n{error_msg}\\n\\nCheck logs for details."
            )
        except:
            pass
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
