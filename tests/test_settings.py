import pytest
from pathlib import Path
from typing import Optional, List
from unittest.mock import Mock, MagicMock, patch, call
from PySide6.QtWidgets import (
    QWidget,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QTextEdit,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QApplication,
)
from PySide6.QtCore import Qt

# Import the module under test
# Adjust the import path based on your actual module structure
from pyside6_settings.settings import BaseSettings, _SettingsBridge
from pyside6_settings.fields import WidgetMetadata, Field
from pyside6_settings.loaders import BaseConfigLoader
from pyside6_settings.widgets import TagInputWidget, PathBrowseWidget


# Fixtures
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_config_loader():
    """Create a mock config loader."""
    loader = Mock(spec=BaseConfigLoader)
    loader.load.return_value = {}
    loader.save.return_value = None
    return loader


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "test_config.json"
    return config_file


# Sample Settings classes for testing
class SimpleSettings(BaseSettings):
    """Simple settings for basic tests."""

    name: str = Field(default="test", description="Test name")
    age: int = Field(default=25, ge=0, le=150)
    enabled: bool = Field(default=True)
    score: float = Field(default=0.5, ge=0.0, le=1.0)


class GroupedSettings(BaseSettings):
    """Settings with groups."""

    username: str = Field(
        default="user",
        title="Username",
        group="Account",
    )
    password: str = Field(
        default="",
        title="Password",
        widget="password",
        group="Account",
    )
    theme: str = Field(
        default="dark",
        title="Theme",
        choices=["light", "dark"],
        group="Appearance",
    )


class ComplexSettings(BaseSettings):
    """Settings with various field types."""

    tags: List[str] = Field(default_factory=list)
    config_path: Path = Field(default=Path("."))
    optional_value: Optional[str] = Field(default=None)
    excluded_field: str = Field(default="hidden", exclude=True)
    description: str = Field(default="", widget="textarea")


# Test BaseSettings initialization
class TestBaseSettingsInit:
    """Tests for BaseSettings initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        settings = SimpleSettings()
        assert settings.name == "test"
        assert settings.age == 25
        assert settings.enabled is True
        assert settings.score == 0.5

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        settings = SimpleSettings(name="custom", age=30, enabled=False, score=0.8)
        assert settings.name == "custom"
        assert settings.age == 30
        assert settings.enabled is False
        assert settings.score == 0.8

    def test_post_init_creates_widgets_dict(self):
        """Test that model_post_init creates _widgets dict."""
        settings = SimpleSettings()
        assert hasattr(settings, "_widgets")
        assert isinstance(settings._widgets, dict)
        assert len(settings._widgets) == 0

    def test_post_init_creates_bridge(self):
        """Test that model_post_init creates _bridge."""
        settings = SimpleSettings()
        assert hasattr(settings, "_bridge")
        assert isinstance(settings._bridge, _SettingsBridge)


# Test BaseSettings.load()
class TestBaseSettingsLoad:
    """Tests for BaseSettings.load() method."""

    @patch("pyside6_settings.settings.DEFAULT_LOADERS")
    def test_load_existing_file(
        self, mock_loaders, temp_config_file, mock_config_loader
    ):
        """Test loading from existing config file."""
        temp_config_file.write_text('{"name": "loaded", "age": 40}')

        mock_loaders.get.return_value = lambda path: mock_config_loader
        mock_config_loader.load.return_value = {"name": "loaded", "age": 40}

        settings = SimpleSettings.load(temp_config_file)

        assert settings.name == "loaded"
        assert settings.age == 40
        assert settings._config_file == temp_config_file
        assert settings._config_loader == mock_config_loader
        mock_config_loader.load.assert_called_once()

    @patch("pyside6_settings.settings.DEFAULT_LOADERS")
    def test_load_nonexistent_file(self, mock_loaders, tmp_path, mock_config_loader):
        """Test loading from non-existent config file."""
        config_file = tmp_path / "nonexistent.json"

        mock_loaders.get.return_value = lambda path: mock_config_loader
        mock_config_loader.load.return_value = {}

        settings = SimpleSettings.load(config_file)

        # Should use defaults when file doesn't exist
        assert settings.name == "test"
        assert settings.age == 25
        assert settings._config_file == config_file

    @patch("pyside6_settings.settings.DEFAULT_LOADERS")
    def test_load_unsupported_format(self, mock_loaders, tmp_path):
        """Test loading unsupported file format raises exception."""
        config_file = tmp_path / "config.unsupported"
        mock_loaders.get.return_value = None

        with pytest.raises(Exception, match="Config loader for"):
            SimpleSettings.load(config_file)


# Test _save_settings()
class TestSaveSettings:
    """Tests for _save_settings() method."""

    def test_save_settings_basic(self, mock_config_loader):
        """Test basic settings save."""
        settings = SimpleSettings(name="save_test", age=35)
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        settings._save_settings()

        mock_config_loader.save.assert_called_once()
        saved_data = mock_config_loader.save.call_args[0][0]
        assert saved_data["General"]["name"] == "save_test"
        assert saved_data["General"]["age"] == 35

    def test_save_settings_with_groups(self, mock_config_loader):
        """Test saving settings with groups."""
        settings = GroupedSettings()
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        settings._save_settings()

        saved_data = mock_config_loader.save.call_args[0][0]
        assert "Account" in saved_data
        assert saved_data["Account"]["username"] == "user"
        assert saved_data["Account"]["password"] == ""

    def test_save_settings_excludes_fields(self, mock_config_loader):
        """Test that excluded fields are not saved."""
        settings = ComplexSettings()
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        settings._save_settings()

        saved_data = mock_config_loader.save.call_args[0][0]
        assert "excluded_field" not in saved_data

    def test_save_settings_without_config_file(self):
        """Test save raises error without config file."""
        settings = SimpleSettings()

        with pytest.raises(RuntimeError, match="Config file not set"):
            settings._save_settings()

    def test_save_settings_without_loader(self):
        """Test save raises error without config loader."""
        settings = SimpleSettings()
        settings._config_file = Path("test.json")

        with pytest.raises(RuntimeError, match="Config loader not set"):
            settings._save_settings()


# Test widget creation
class TestWidgetCreation:
    """Tests for widget creation methods."""

    def test_create_widget_for_string_field(self, qapp):
        """Test creating widget for string field."""
        settings = SimpleSettings()
        widget_metadata = WidgetMetadata(title="Name")

        widget = settings._create_widget_for_field("name", widget_metadata)

        assert isinstance(widget, QLineEdit)
        assert widget.text() == "test"

    def test_create_widget_for_int_field(self, qapp):
        """Test creating widget for int field."""
        settings = SimpleSettings()
        widget_metadata = WidgetMetadata(title="Age")

        widget = settings._create_widget_for_field("age", widget_metadata)

        assert isinstance(widget, QSpinBox)
        assert widget.value() == 25
        assert widget.minimum() == 0
        assert widget.maximum() == 150

    def test_create_widget_for_bool_field(self, qapp):
        """Test creating widget for bool field."""
        settings = SimpleSettings()
        widget_metadata = WidgetMetadata(title="Enabled")

        widget = settings._create_widget_for_field("enabled", widget_metadata)

        assert isinstance(widget, QCheckBox)
        assert widget.isChecked() is True

    def test_create_widget_for_float_field(self, qapp):
        """Test creating widget for float field."""
        settings = SimpleSettings()
        widget_metadata = WidgetMetadata(title="Score")

        widget = settings._create_widget_for_field("score", widget_metadata)

        assert isinstance(widget, QDoubleSpinBox)
        assert widget.value() == 0.5
        assert widget.minimum() == 0.0
        assert widget.maximum() == 1.0

    def test_create_widget_with_choices(self, qapp):
        """Test creating combobox widget with choices."""
        settings = GroupedSettings()
        widget_metadata = WidgetMetadata(title="Theme", choices=["light", "dark"])

        widget = settings._create_widget_for_field("theme", widget_metadata)

        assert isinstance(widget, QComboBox)
        assert widget.count() == 2
        assert widget.currentText() == "dark"

    def test_create_widget_for_list_field(self, qapp):
        """Test creating widget for list field."""
        settings = ComplexSettings()
        widget_metadata = WidgetMetadata(title="Tags")

        widget = settings._create_widget_for_field("tags", widget_metadata)

        assert isinstance(widget, TagInputWidget)

    def test_create_widget_for_path_field(self, qapp):
        """Test creating widget for Path field."""
        settings = ComplexSettings()
        widget_metadata = WidgetMetadata(title="Config Path")

        widget = settings._create_widget_for_field("config_path", widget_metadata)

        assert isinstance(widget, PathBrowseWidget)

    def test_create_widget_password(self, qapp):
        """Test creating password widget."""
        settings = GroupedSettings()
        widget_metadata = WidgetMetadata(title="Password", widget="password")

        widget = settings._create_widget_for_field("password", widget_metadata)

        assert isinstance(widget, QLineEdit)
        assert widget.echoMode() == QLineEdit.EchoMode.Password

    def test_create_widget_textarea(self, qapp):
        """Test creating textarea widget."""
        settings = ComplexSettings()
        widget_metadata = WidgetMetadata(widget="textarea")

        widget = settings._create_widget_for_field("description", widget_metadata)

        assert isinstance(widget, QTextEdit)

    def test_create_widget_excluded_returns_none(self, qapp):
        """Test that excluded fields return None."""
        settings = ComplexSettings()
        widget_metadata = WidgetMetadata(widget="hidden")

        widget = settings._create_widget_for_field("excluded_field", widget_metadata)

        assert widget is None

    def test_widget_tooltip_from_description(self, qapp):
        """Test that widget tooltip is set from field description."""
        settings = SimpleSettings()
        widget_metadata = WidgetMetadata(title="Name")

        widget = settings._create_widget_for_field("name", widget_metadata)

        assert widget.toolTip() == "Test name"


# Test value change handling
class TestValueChangeHandling:
    """Tests for value change handling."""

    def test_on_value_changed_updates_field(self, mock_config_loader):
        """Test that _on_value_changed updates the field."""
        settings = SimpleSettings()
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        settings._on_value_changed("name", "new_name")

        assert settings.name == "new_name"
        # mock_config_loader.save.assert_called_once()

    def test_setattr_triggers_save(self, mock_config_loader):
        """Test that setting attribute triggers save."""
        settings = SimpleSettings()
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        settings.name = "updated"

        assert settings.name == "updated"
        assert mock_config_loader.save.called

    def test_setattr_only_saves_on_change(self, mock_config_loader):
        """Test that setting same value doesn't trigger save."""
        settings = SimpleSettings()
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        # Reset mock after initialization
        mock_config_loader.reset_mock()

        settings.name = "test"  # Same as default

        # Should not save if value didn't change
        assert mock_config_loader.save.call_count == 0


# Test widget synchronization
class TestWidgetSynchronization:
    """Tests for widget synchronization via bridge."""

    def test_widget_syncs_on_model_change(self, qapp, mock_config_loader):
        """Test that widget updates when model changes."""
        settings = SimpleSettings()
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        widget = settings.get_widget("name", with_label=False)

        # Change model value
        settings.name = "synced"

        # Widget should update
        assert isinstance(widget, QLineEdit)
        assert widget.text() == "synced"

    def test_checkbox_syncs_on_model_change(self, qapp, mock_config_loader):
        """Test that checkbox syncs when model changes."""
        settings = SimpleSettings()
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        widget = settings.get_widget("enabled", with_label=False)

        settings.enabled = False

        assert isinstance(widget, QCheckBox)
        assert widget.isChecked() is False


# Test get_widget()
class TestGetWidget:
    """Tests for get_widget() method."""

    def test_get_widget_without_label(self, qapp):
        """Test getting widget without label."""
        settings = SimpleSettings()
        widget = settings.get_widget("name", with_label=False)

        assert isinstance(widget, QLineEdit)

    def test_get_widget_with_label(self, qapp):
        """Test getting widget with label."""
        settings = SimpleSettings()
        widget = settings.get_widget("name", with_label=True)

        assert isinstance(widget, QWidget)
        assert isinstance(widget.layout(), QFormLayout)

    def test_get_widget_excluded_raises_error(self, qapp):
        """Test that getting excluded widget raises error."""
        settings = ComplexSettings()

        with pytest.raises(ValueError, match="widget was disabled or excluded"):
            settings.get_widget("excluded_field")


# Test get_group()
class TestGetGroup:
    """Tests for get_group() method."""

    def test_get_group_returns_groupbox(self, qapp):
        """Test that get_group returns QGroupBox."""
        settings = GroupedSettings()
        group = settings.get_group("Account")

        assert isinstance(group, QGroupBox)
        assert group.title() == "Account"

    def test_get_group_contains_fields(self, qapp):
        """Test that group contains correct fields."""
        settings = GroupedSettings()
        group = settings.get_group("Account")

        layout = group.layout()
        assert isinstance(layout, QFormLayout)
        assert layout.rowCount() == 2  # username and password

    def test_get_group_nonexistent_raises_error(self, qapp):
        """Test that getting nonexistent group raises error."""
        settings = GroupedSettings()

        with pytest.raises(ValueError, match="No such group"):
            settings.get_group("NonExistent")


# Test create_form()
class TestCreateForm:
    """Tests for create_form() method."""

    def test_create_form_returns_widget(self, qapp):
        """Test that create_form returns QWidget."""
        settings = GroupedSettings()
        form = settings.create_form()

        assert isinstance(form, QWidget)
        assert isinstance(form.layout(), QVBoxLayout)

    def test_create_form_contains_groups(self, qapp):
        """Test that form contains all groups."""
        settings = GroupedSettings()
        form = settings.create_form()

        layout = form.layout()
        group_boxes = [
            layout.itemAt(i).widget()
            for i in range(layout.count())
            if isinstance(layout.itemAt(i).widget(), QGroupBox)
        ]

        group_titles = [box.title() for box in group_boxes]
        assert "Account" in group_titles
        assert "Appearance" in group_titles

    def test_create_form_with_parent(self, qapp):
        """Test creating form with parent widget."""
        parent = QWidget()
        settings = GroupedSettings()
        form = settings.create_form(parent)

        assert form.parent() == parent


# Test field info methods
class TestFieldInfo:
    """Tests for field info methods."""

    def test_get_field_info_valid_field(self):
        """Test getting field info for valid field."""
        settings = SimpleSettings()
        field_info = settings._get_field_info("name")

        assert field_info is not None
        assert field_info.description == "Test name"

    def test_get_field_info_invalid_field(self):
        """Test getting field info for invalid field raises error."""
        settings = SimpleSettings()

        with pytest.raises(RuntimeError, match="No such field"):
            settings._get_field_info("nonexistent")

    def test_get_or_create_widget_metadata(self):
        """Test getting or creating widget metadata."""
        settings = SimpleSettings()
        metadata = settings._get_or_create_widget_metadata("name")

        assert isinstance(metadata, WidgetMetadata)
        assert metadata.description == "Test name"


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows."""

    def test_widget_interaction_updates_model(self, qapp, mock_config_loader):
        """Test that widget interaction updates model."""
        settings = SimpleSettings()
        settings._config_file = Path("test.json")
        settings._config_loader = mock_config_loader

        widget = settings.get_widget("name", with_label=False)

        # Simulate user input
        assert isinstance(widget, QLineEdit)
        widget.setText("user_input")

        # Model should update
        assert settings.name == "user_input"
        assert mock_config_loader.save.called
