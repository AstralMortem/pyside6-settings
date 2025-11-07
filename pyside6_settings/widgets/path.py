from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
)
from PySide6.QtCore import Signal, Qt, QDir
import os
from pyside6_settings.fields import _FS_MODE


class PathBrowseWidget(QWidget):
    """Path browse widget with line edit and browse button"""

    # Signals
    path_changed = Signal(Path)  # Emits when path changes
    path_selected = Signal(Path)  # Emits when path is selected via dialog
    path_validated = Signal(bool)  # Emits validation status

    def __init__(
        self,
        mode: _FS_MODE = "file",
        placeholder: str = "Select File",
        file_filter: str = "All Files (*.*)",
        start_directory: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._mode: _FS_MODE = mode
        self._file_filter = file_filter
        self._dialog_title = placeholder
        self._validate_on_change = True
        self._start_directory = Path(start_directory)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Path line edit
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(self._get_placeholder())
        self.path_edit.textChanged.connect(self._on_path_changed)
        self.path_edit.editingFinished.connect(self._on_editing_finished)
        layout.addWidget(self.path_edit, stretch=1)

        # Browse button
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.browse_btn)

    def _get_placeholder(self):
        """Get placeholder text based on mode"""
        if self._mode == "folder":
            return "Select a folder..."
        elif self._mode == "file":
            return "Enter file path to save..."
        else:
            return "Select a file..."

    def _on_path_changed(self, text: Path):
        """Handle path text change"""
        text = Path(text)
        if self._validate_on_change:
            is_valid = self.validate_path(text)
            self._update_validation_style(is_valid)
            self.path_validated.emit(is_valid)
        self.path_changed.emit(text)

    def _on_editing_finished(self):
        """Handle editing finished"""
        path = Path(self.path_edit.text())
        if path:
            # Normalize path
            normalized = os.path.normpath(path)
            if normalized != path:
                self.path_edit.setText(normalized)

    def _on_browse_clicked(self):
        """Handle browse button click"""
        start_dir = self._start_directory or self.get_path() or Path(QDir.homePath())

        # Make sure start directory exists
        if start_dir and not start_dir.exists():
            start_dir = Path(QDir.homePath())

        selected_path = None

        if self._mode == "folder":
            selected_path = QFileDialog.getExistingDirectory(
                self,
                self._dialog_title,
                str(start_dir),
                QFileDialog.Option.ShowDirsOnly
                | QFileDialog.Option.DontResolveSymlinks,
            )
        elif self._mode == "save_file":
            selected_path, _ = QFileDialog.getSaveFileName(
                self, self._dialog_title, str(start_dir), self._file_filter
            )
        else:  # FILE mode
            selected_path, _ = QFileDialog.getOpenFileName(
                self, self._dialog_title, str(start_dir), self._file_filter
            )

        if selected_path:
            selected_path = Path(selected_path)
            self.set_path(selected_path)
            self.path_selected.emit(selected_path)

    def _update_validation_style(self, is_valid):
        """Update line edit style based on validation"""
        if not self.path_edit.text():
            # Empty - no style
            self.path_edit.setStyleSheet("")
        elif is_valid:
            # Valid - subtle green border
            self.path_edit.setStyleSheet("QLineEdit { border: 1px solid #4CAF50; }")
        else:
            # Invalid - subtle red border
            self.path_edit.setStyleSheet("QLineEdit { border: 1px solid #F44336; }")

    def validate_path(self, path: Optional[Path] = None):
        """Validate the current path based on mode"""
        if path is None:
            path = self.get_path()

        if not path:
            return False

        if self._mode == "folder":
            return path.is_dir()
        elif self._mode == "save_file":
            # For save mode, check if parent directory exists
            parent_dir = path.parent
            return parent_dir.is_dir() if parent_dir else True
        else:  # FILE mode
            return path.is_file()

    # Public methods
    def get_path(self):
        """Get current path"""
        return Path(self.path_edit.text())

    def set_path(self, path: str | Path):
        """Set path"""
        self.path_edit.setText(str(path))

    def clear_path(self):
        """Clear path"""
        self.path_edit.clear()

    def get_mode(self):
        """Get browse mode"""
        return self._mode

    def set_mode(self, mode):
        """Set browse mode"""
        self._mode = mode
        self.path_edit.setPlaceholderText(self._get_placeholder())

    def get_file_filter(self):
        """Get file filter"""
        return self._file_filter

    def set_file_filter(self, filter_string):
        """
        Set file filter for file dialogs
        Example: "Images (*.png *.jpg);;Text files (*.txt);;All Files (*.*)"
        """
        self._file_filter = filter_string

    def set_dialog_title(self, title):
        """Set dialog title"""
        self._dialog_title = title

    def set_start_directory(self, directory: Path):
        """Set starting directory for browse dialog"""
        self._start_directory = directory

    def set_validate_on_change(self, validate):
        """Enable/disable validation on text change"""
        self._validate_on_change = validate
        if not validate:
            self.path_edit.setStyleSheet("")

    def is_path_valid(self):
        """Check if current path is valid"""
        return self.validate_path()
