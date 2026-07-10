"""
About Window - Application information.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtGui import QFont
from src.utils.logger import get_logger
from src.utils.settings_manager import get_settings


class AboutWindow(QDialog):
    """
    About dialog showing application information.
    
    Displays version, author, copyright, and
    other important system information.
    """

    def __init__(self) -> None:
        """Initialize the About Window."""
        super().__init__()
        self.logger = get_logger()
        self.settings = get_settings()
        
        self.setWindowTitle("About")
        self.setGeometry(250, 250, 400, 300)
        self.setModal(True)
        
        self._create_widgets()
        self._setup_layout()
        
        self.logger.info("AboutWindow initialized")

    def _create_widgets(self) -> None:
        """Create all widgets."""
        # Title
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        
        app_name = self.settings.get('application.name', 'CDRS')
        self.title_label = QLabel(app_name)
        self.title_label.setFont(title_font)
        
        # Version
        version = self.settings.get('application.version', '1.0.0')
        self.version_label = QLabel(f"Version {version}")
        
        # Author
        author = self.settings.get('application.author', 'Capitec Development Team')
        self.author_label = QLabel(f"Author: {author}")
        
        # Copyright
        self.copyright_label = QLabel("© 2026 Capitec Bank Holdings Limited")
        
        # Description
        self.description_label = QLabel(
            "A professional Windows desktop application for automated "
            "reconciliation of Capitec Daily Output Excel workbooks."
        )
        self.description_label.setWordWrap(True)
        
        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.close)

    def _setup_layout(self) -> None:
        """Set up the layout."""
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.author_label)
        layout.addWidget(self.copyright_label)
        layout.addWidget(self.description_label)
        layout.addStretch()
        layout.addWidget(self.ok_button)
        
        self.setLayout(layout)
