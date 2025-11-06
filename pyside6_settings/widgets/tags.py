from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
# from PySide6.QtGui import


class TagWidget(QFrame):
    """Individual tag widget with remove button"""

    removed = Signal(str)  # Emits tag text when removed

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self._setup_ui()

    def _setup_ui(self):
        # Frame styling
        self.setStyleSheet("""
            QFrame {
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 3px;
                padding: 2px 4px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Tag label
        self.label = QLabel(self.text)
        layout.addWidget(self.label)

        # Remove button
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(16, 16)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setFlat(True)
        self.remove_btn.clicked.connect(self._on_remove)
        layout.addWidget(self.remove_btn)

    def _on_remove(self):
        self.removed.emit(self.text)

    def get_text(self):
        return self.text


class TagInputWidget(QWidget):
    """Tag input widget with add/remove functionality"""

    # Signals
    tag_added = Signal(str)  # Emits when a tag is added
    tag_removed = Signal(str)  # Emits when a tag is removed
    tags_changed = Signal(list)  # Emits current tag list when changed

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tags = []
        self._tag_widgets = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Container frame for tags and input
        self.container = QFrame()
        self.container.setFrameShape(QFrame.Shape.StyledPanel)
        self.container.setFrameShadow(QFrame.Shadow.Sunken)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(4, 4, 4, 4)

        # Tags area with flow layout simulation
        self.tags_widget = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_widget)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(4)
        self.tags_layout.addStretch()

        container_layout.addWidget(self.tags_widget)

        # Input line
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Type tag and press Enter...")
        self.input_line.returnPressed.connect(self._on_return_pressed)
        container_layout.addWidget(self.input_line)

        main_layout.addWidget(self.container)

        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def _on_return_pressed(self):
        text = self.input_line.text().strip()
        if text:
            self.add_tag(text)
            self.input_line.clear()

    def add_tag(self, text):
        """Add a tag to the widget"""
        text = text.strip()
        if not text or text in self._tags:
            return False

        # Create tag widget
        tag_widget = TagWidget(text)
        tag_widget.removed.connect(self._on_tag_removed)

        # Insert before stretch
        self.tags_layout.insertWidget(len(self._tag_widgets), tag_widget)

        self._tags.append(text)
        self._tag_widgets.append(tag_widget)

        # Emit signals
        self.tag_added.emit(text)
        self.tags_changed.emit(self._tags.copy())

        return True

    def _on_tag_removed(self, text):
        """Handle tag removal"""
        if text in self._tags:
            idx = self._tags.index(text)
            self._tags.pop(idx)

            # Remove and delete widget
            tag_widget = self._tag_widgets.pop(idx)
            self.tags_layout.removeWidget(tag_widget)
            tag_widget.deleteLater()

            # Emit signals
            self.tag_removed.emit(text)
            self.tags_changed.emit(self._tags.copy())

    def remove_tag(self, text):
        """Remove a tag by text"""
        self._on_tag_removed(text)

    def clear_tags(self):
        """Remove all tags"""
        for tag_widget in self._tag_widgets[:]:
            tag_widget.removed.emit(tag_widget.get_text())

    def get_tags(self):
        """Get list of current tags"""
        return self._tags.copy()

    def set_tags(self, tags):
        """Set tags from a list"""
        self.clear_tags()
        for tag in tags:
            self.add_tag(tag)
