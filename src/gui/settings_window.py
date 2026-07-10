"""
Settings Window - Application settings and configuration.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QSpinBox, QLabel,
    QGroupBox, QGridLayout
)
from src.utils.logger import get_logger
from src.utils.settings_manager import get_settings


class SettingsWindow(QMainWindow):
    """
    Settings window for application configuration.
    
    Allows users to modify settings like multipliers,
    backup options, and UI preferences.
    """

    def __init__(self) -> None:
        """Initialize the Settings Window."""
        super().__init__()
        self.logger = get_logger()
        self.settings = get_settings()
        
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 500, 400)
        
        self._create_widgets()
        self._setup_layout()
        self._load_settings()
        
        self.logger.info("SettingsWindow initialized")

    def _create_widgets(self) -> None:
        """Create all widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Multipliers group
        self.multipliers_group = QGroupBox("Multipliers")
        self.sim_multiplier_label = QLabel("SIM Multiplier:")
        self.sim_multiplier_spinbox = QSpinBox()
        self.sim_multiplier_spinbox.setRange(1, 1000)
        
        self.bank_multiplier_label = QLabel("Bank Multiplier:")
        self.bank_multiplier_spinbox = QSpinBox()
        self.bank_multiplier_spinbox.setRange(1, 1000)
        
        # Options group
        self.options_group = QGroupBox("Options")
        self.auto_backup_checkbox = QCheckBox("Enable Auto Backup")
        self.auto_highlight_checkbox = QCheckBox("Enable Auto Highlight")
        self.auto_pdf_checkbox = QCheckBox("Enable Auto PDF Generation")
        self.audit_log_checkbox = QCheckBox("Enable Audit Logging")
        self.dark_mode_checkbox = QCheckBox("Dark Mode")
        
        # Buttons
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.reset_button = QPushButton("Reset to Defaults")
        
        # Connect signals
        self.save_button.clicked.connect(self._on_save)
        self.cancel_button.clicked.connect(self.close)
        self.reset_button.clicked.connect(self._on_reset)

    def _setup_layout(self) -> None:
        """Set up the layout."""
        central_widget = self.centralWidget()
        main_layout = QVBoxLayout()
        
        # Multipliers layout
        multipliers_layout = QGridLayout()
        multipliers_layout.addWidget(self.sim_multiplier_label, 0, 0)
        multipliers_layout.addWidget(self.sim_multiplier_spinbox, 0, 1)
        multipliers_layout.addWidget(self.bank_multiplier_label, 1, 0)
        multipliers_layout.addWidget(self.bank_multiplier_spinbox, 1, 1)
        self.multipliers_group.setLayout(multipliers_layout)
        main_layout.addWidget(self.multipliers_group)
        
        # Options layout
        options_layout = QVBoxLayout()
        options_layout.addWidget(self.auto_backup_checkbox)
        options_layout.addWidget(self.auto_highlight_checkbox)
        options_layout.addWidget(self.auto_pdf_checkbox)
        options_layout.addWidget(self.audit_log_checkbox)
        options_layout.addWidget(self.dark_mode_checkbox)
        self.options_group.setLayout(options_layout)
        main_layout.addWidget(self.options_group)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(buttons_layout)
        
        main_layout.addStretch()
        central_widget.setLayout(main_layout)

    def _load_settings(self) -> None:
        """Load current settings into the UI."""
        self.sim_multiplier_spinbox.setValue(
            self.settings.get('settings.sim_multiplier', 200)
        )
        self.bank_multiplier_spinbox.setValue(
            self.settings.get('settings.bank_multiplier', 300)
        )
        self.auto_backup_checkbox.setChecked(
            self.settings.get('settings.auto_backup', True)
        )
        self.auto_highlight_checkbox.setChecked(
            self.settings.get('settings.auto_highlight', True)
        )
        self.auto_pdf_checkbox.setChecked(
            self.settings.get('settings.auto_pdf', True)
        )
        self.audit_log_checkbox.setChecked(
            self.settings.get('settings.enable_audit_log', True)
        )
        self.dark_mode_checkbox.setChecked(
            self.settings.get('settings.dark_mode', False)
        )

    def _on_save(self) -> None:
        """Save settings and close window."""
        self.settings.set('settings.sim_multiplier', self.sim_multiplier_spinbox.value())
        self.settings.set('settings.bank_multiplier', self.bank_multiplier_spinbox.value())
        self.settings.set('settings.auto_backup', self.auto_backup_checkbox.isChecked())
        self.settings.set('settings.auto_highlight', self.auto_highlight_checkbox.isChecked())
        self.settings.set('settings.auto_pdf', self.auto_pdf_checkbox.isChecked())
        self.settings.set('settings.enable_audit_log', self.audit_log_checkbox.isChecked())
        self.settings.set('settings.dark_mode', self.dark_mode_checkbox.isChecked())
        self.settings.save_settings()
        
        self.logger.info("Settings saved")
        self.close()

    def _on_reset(self) -> None:
        """Reset settings to defaults."""
        self.settings.reset_to_defaults()
        self._load_settings()
        self.logger.info("Settings reset to defaults")
