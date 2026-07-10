"""
Settings Manager - Handles application configuration and settings.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from src.utils.logger import get_logger


class SettingsManager:
    """
    Manages application settings and configuration.
    
    Loads settings from JSON configuration file and provides
    methods to read and update settings at runtime.
    """

    _instance: Optional['SettingsManager'] = None
    _settings: Dict[str, Any] = {}
    _config_path: Path = Path('src/config/settings.json')

    def __new__(cls) -> 'SettingsManager':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self) -> None:
        """
        Load settings from the JSON configuration file.
        
        If the file doesn't exist, default settings are used.
        """
        logger = get_logger()
        
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r') as f:
                    config = json.load(f)
                    self._settings = config
                    logger.info(f"Settings loaded from {self._config_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing settings file: {e}")
                self._set_default_settings()
        else:
            logger.warning(f"Settings file not found at {self._config_path}")
            self._set_default_settings()

    def _set_default_settings(self) -> None:
        """Set default application settings."""
        self._settings = {
            "application": {
                "name": "Capitec Daily Reconciliation System",
                "version": "1.0.0",
                "author": "Capitec Development Team"
            },
            "settings": {
                "sim_multiplier": 200,
                "bank_multiplier": 300,
                "auto_backup": True,
                "auto_highlight": True,
                "auto_pdf": True,
                "enable_audit_log": True,
                "dark_mode": False
            },
            "paths": {
                "backup_folder": "backups",
                "report_folder": "reports",
                "log_folder": "logs",
                "database_folder": "database",
                "sample_files_folder": "sample_files"
            },
            "database": {
                "name": "cdrs.db",
                "location": "database/cdrs.db"
            },
            "ui": {
                "window_width": 1024,
                "window_height": 768,
                "window_title": "Capitec Daily Reconciliation System"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/cdrs.log"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value by key.
        
        Supports nested keys using dot notation (e.g., 'settings.sim_multiplier').
        
        Args:
            key: The setting key or nested key path.
            default: Default value if key is not found.
            
        Returns:
            The setting value or default if not found.
        """
        keys = key.split('.')
        value = self._settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value by key.
        
        Supports nested keys using dot notation.
        
        Args:
            key: The setting key or nested key path.
            value: The value to set.
        """
        keys = key.split('.')
        current = self._settings
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        get_logger().info(f"Setting {key} changed to {value}")

    def save_settings(self) -> None:
        """
        Save the current settings to the configuration file.
        
        Creates the config directory if it doesn't exist.
        """
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, 'w') as f:
                json.dump(self._settings, f, indent=2)
            get_logger().info("Settings saved successfully")
        except IOError as e:
            get_logger().error(f"Error saving settings: {e}")

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all settings as a dictionary.
        
        Returns:
            Dictionary containing all settings.
        """
        return self._settings.copy()

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self._set_default_settings()
        self.save_settings()
        get_logger().info("Settings reset to defaults")


def get_settings() -> SettingsManager:
    """
    Convenience function to get the settings manager instance.
    
    Returns:
        SettingsManager: The settings manager instance.
    """
    return SettingsManager()
