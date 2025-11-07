from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pyside6_settings import BaseSettings, Field
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton

class EditorSettings(BaseSettings):
    # General Settings
    window_title: str = Field(
        default="My Editor",
        title="Window Title",
    )
    
    auto_save: bool = Field(
        default=True,
        title="Auto Save",
        description="Automatically save files",
    )
    
    # Editor Settings
    font_family: str = Field(
        default="Monospace",
        title="Font Family",
        choices=["Monospace", "Arial", "Times New Roman"],
        group="editor"
    )
    
    font_size: int = Field(
        default=12,
        ge=8,
        le=32,
        title="Font Size",
        group="editor"
    )
    
    tab_size: int = Field(
        default=4,
        ge=1,
        le=8,
        title="Tab Size",
        group="editor"
    )
    
    # Paths
    workspace: Path = Field(
        default=Path.home(),
        title="Workspace Directory",
        fs_mode="folder",
        group="paths"
    )
    
    recent_files: List[str] = Field(
        default_factory=list,
        title="Recent Files",
        widget="tags",
        group="paths"
    )

def main():
    app = QApplication([])
    
    # Load settings
    settings = EditorSettings.load("editor_config.json")
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Editor Settings")
    
    # Create central widget with settings form
    central = QWidget()
    layout = QVBoxLayout(central)
    
    # Add settings form
    settings_form = settings.create_form()
    layout.addWidget(settings_form)
    
    # Add close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(window.close)
    layout.addWidget(close_btn)
    
    window.setCentralWidget(central)
    window.resize(600, 500)
    window.show()

    
    app.exec()

if __name__ == "__main__":
    main()