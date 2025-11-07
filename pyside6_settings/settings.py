from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Self,
    Tuple,
    get_args,
    get_origin,
)
from pydantic import BaseModel, ConfigDict
from pathlib import Path
from .loaders import DEFAULT_LOADERS, BaseConfigLoader
from .type_parser import TypeParser
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
    QScrollArea
)
from PySide6.QtCore import Signal, QObject
from .fields import WidgetMetadata
from .widgets import TagInputWidget, PathBrowseWidget


class _SettingsBridge(QObject):
    value_changed = Signal(str, object)


class BaseSettings(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_enum_values=True,
    )
    _config_file: Path
    _config_loader: BaseConfigLoader
    _bridge: _SettingsBridge
    _widgets: Dict[str, QWidget]
    _type_parser: ClassVar[TypeParser] = TypeParser()

    def model_post_init(self, context: Any) -> None:
        self._widgets = {}
        self._bridge = _SettingsBridge()

    def __init__(self, **data):
        for key, val in data.items():
            data[key] = self._type_parser.parse_value(val)
        super().__init__(**data)

    @classmethod
    def load(cls, config_file: str | Path, auto_create: bool = False) -> Self:
        config_file = Path(config_file)
        config_loader = DEFAULT_LOADERS.get(config_file.suffix, None)
        if config_loader is None:
            raise Exception(
                f"Config loader for .{config_file.suffix} format, does not exist,"
                f" available file formats: {','.join(DEFAULT_LOADERS.keys())} "
            )

        # Create instance of config loader
        config_loader = config_loader(config_file)

        # Load config
        if config_file.exists():
            data = config_loader.load()
        else:
            data = {}

        # Create settings instance and set fields
        instance = cls(**data)
        instance._config_file = config_file
        instance._config_loader = config_loader

        # If True, create config file with default values first time
        if auto_create and not config_file.exists():
            instance._save_settings()


        return instance

    def _get_field_info(self, field_name: str):
        if field_name not in self.__pydantic_fields__:
            raise RuntimeError(f"No such field: {field_name}")
        return self.__pydantic_fields__[field_name]

    def _get_or_create_widget_metadata(self, field_name: str) -> WidgetMetadata:
        field_info = self._get_field_info(field_name)
        metadata = field_info.json_schema_extra.get(  # type: ignore
            "widget_metadata",
            WidgetMetadata(
                title=field_info.title,
                description=field_info.description,
            ),
        )
        return metadata  # type: ignore

    def _save_settings(self):
        if not hasattr(self, "_config_file"):
            raise RuntimeError("Config file not set")

        if not hasattr(self, "_config_loader"):
            raise RuntimeError("Config loader not set")

        data = {}
        for field_name, field_info in self.__pydantic_fields__.items():
            # Skipp config value if excluded
            if field_info.exclude:
                continue

            # Get widget metadata
            widget_metadata = self._get_or_create_widget_metadata(field_name)
            # Get python value and try serialize type if necessary
            value = self._type_parser.serialize_value(getattr(self, field_name))

            # Save settings by groups
            if widget_metadata and widget_metadata.group:
                if widget_metadata.group not in data:
                    data[widget_metadata.group] = {}
                data[widget_metadata.group][field_name] = value
            else:
                data[field_name] = value

        self._config_loader.save(data)

    def _on_value_changed(self, name: str, value: Any):
        setattr(self, name, value)
        self._save_settings()

        # Emit value changed signal in bridge
        if self._bridge:
            self._bridge.value_changed.emit(name, value)

    def _create_widget_for_field(self, name: str, widget_metadata: WidgetMetadata):
        field_info = self._get_field_info(name)
        field_type = field_info.annotation

        # Handle optional types
        origin = get_origin(field_type)
        if origin is type(Optional):
            args = get_args(field_type)
            field_type = args[0] if args else str

        # Create widget
        widget = None
        current_value = getattr(self, name)

        # Exclude
        if field_info.exclude or widget_metadata.widget == "hidden":
            return None

        if widget_metadata.choices:
            widget = QComboBox()
            widget.addItems([str(c) for c in widget_metadata.choices])
            if current_value in widget_metadata.choices:
                widget.setCurrentText(str(current_value))
            widget.currentTextChanged.connect(
                lambda v: self._on_value_changed(
                    name, type(current_value)(v) if v else v
                )
            )
        elif get_origin(field_type) is list or widget_metadata.widget == "tags":
            widget = TagInputWidget()
            widget.set_tags(list(current_value))
            widget.tags_changed.connect(lambda v: self._on_value_changed(name, list(v)))

        elif (
            field_type == Path
            or widget_metadata.fs_mode
            or widget_metadata.widget == "path"
        ):
            widget = PathBrowseWidget(widget_metadata.fs_mode or "file")
            widget.set_path(Path(current_value))
            widget.path_changed.connect(lambda v: self._on_value_changed(name, Path(v)))

        elif field_type is bool or widget_metadata.widget == "checkbox":
            widget = QCheckBox()
            widget.setChecked(bool(current_value))
            widget.stateChanged.connect(
                lambda state: self._on_value_changed(name, bool(state))
            )

        elif field_type is int or widget_metadata.widget == "spinbox":
            widget = QSpinBox()
            constraints = field_info.metadata
            ge = next(
                (c.ge for c in constraints if hasattr(c, "ge") and c.ge is not None),
                None,
            )
            le = next(
                (c.le for c in constraints if hasattr(c, "le") and c.le is not None),
                None,
            )

            widget.setMinimum(int(ge) if ge is not None else -2147483648)
            widget.setMaximum(int(le) if le is not None else 2147483647)
            widget.setValue(int(current_value))
            widget.valueChanged.connect(lambda v: self._on_value_changed(name, v))

        elif field_type is float or widget_metadata.widget == "doublespinbox":
            widget = QDoubleSpinBox()
            constraints = field_info.metadata
            ge = next(
                (c.ge for c in constraints if hasattr(c, "ge") and c.ge is not None),
                None,
            )
            le = next(
                (c.le for c in constraints if hasattr(c, "le") and c.le is not None),
                None,
            )

            widget.setMinimum(ge if ge is not None else -2147483648)
            widget.setMaximum(le if le is not None else 2147483647)
            widget.setValue(float(current_value))
            widget.valueChanged.connect(lambda v: self._on_value_changed(name, v))

        elif widget_metadata.widget == "password":
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            widget.setText(str(current_value) if current_value is not None else "")
            widget.textChanged.connect(lambda v: self._on_value_changed(name, v))

        elif widget_metadata.widget == "textarea":
            widget = QTextEdit()
            widget.setText(str(current_value) if current_value is not None else "")
            widget.textChanged.connect(
                lambda: self._on_value_changed(name, widget.toPlainText())
            )

        # Default to line edit
        else:
            widget = QLineEdit()
            widget.setText(str(current_value) if current_value is not None else "")
            widget.textChanged.connect(lambda v: self._on_value_changed(name, v))

        # Set tooltip
        tooltip = field_info.description or widget_metadata.description
        if tooltip:
            widget.setToolTip(tooltip)

        # Connect bridge signal for synchronization
        if self._bridge:
            self._connect_bridge_signal(widget, name)
        return widget

    def _connect_bridge_signal(self, widget: QWidget, name: str):
        """Connect bridge signal for widget synchronization."""

        def handler(changed_name, new_value):
            if changed_name != name:
                return

            # Sync widget from model change
            if isinstance(widget, QLineEdit):
                if widget.text() != str(new_value):
                    widget.blockSignals(True)
                    widget.setText(str(new_value))
                    widget.blockSignals(False)
            elif isinstance(widget, QCheckBox):
                if widget.isChecked() != bool(new_value):
                    widget.blockSignals(True)
                    widget.setChecked(bool(new_value))
                    widget.blockSignals(False)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                if widget.value() != new_value:
                    widget.blockSignals(True)
                    widget.setValue(new_value)
                    widget.blockSignals(False)
            elif isinstance(widget, QComboBox):
                if widget.currentText() != str(new_value):
                    widget.blockSignals(True)
                    widget.setCurrentText(str(new_value))
                    widget.blockSignals(False)
            elif isinstance(widget, QTextEdit):
                if widget.toPlainText() != str(new_value):
                    widget.blockSignals(True)
                    widget.setPlainText(str(new_value))
                    widget.blockSignals(False)
            elif isinstance(widget, PathBrowseWidget):
                if widget.get_path() != Path(new_value):
                    widget.blockSignals(True)
                    widget.set_path(Path(new_value))
                    widget.blockSignals(False)
            elif isinstance(widget, TagInputWidget):
                if widget.get_tags() != list(new_value):
                    widget.blockSignals(True)
                    widget.set_tags(list(new_value))
                    widget.blockSignals(False)

        self._bridge.value_changed.connect(handler)

    def __setattr__(self, name: str, value: Any) -> None:
        """Overide __setattr__ to emit value changed signal if directly updated settings attribute"""

        # Check if the attribute is a Pydantic field
        if name in self.__pydantic_fields__:
            old_value = getattr(self, name, None)
            super().__setattr__(name, value)
            # Update if value different
            if old_value != value:
                self._on_value_changed(name, value)
        else:
            super().__setattr__(name, value)

    def get_widget(self, field_name: str, with_label: bool = True) -> QWidget:
        """Return a cloned widget for a specific field (synchronized)."""
        # Get widget metadata
        widget_metadata = self._get_or_create_widget_metadata(field_name)

        # Clone widget (recreate it with same setup)
        widget = self._create_widget_for_field(field_name, widget_metadata)
        if widget is None:
            raise ValueError("Field exists but widget was disabled or excluded")

        # Create form layout it with label flag
        if with_label:
            form = QFormLayout()
            form.addRow(
                widget_metadata.title or field_name.replace("_", " ").title(), widget
            )
            widget = QWidget()
            widget.setLayout(form)

        return widget

    def get_group(self, group_name: str, group_title: Optional[str] = None) -> QGroupBox:
        fields = []

        # Get widget metadata by group
        for field_name in self.__pydantic_fields__.keys():
            widget_metadata = self._get_or_create_widget_metadata(field_name)
            if widget_metadata.group.lower() == group_name.lower():
                fields.append((field_name, widget_metadata))

        if len(fields) == 0:
            raise ValueError(f"No such group: {group_name}")

        return self._create_groupbox_for_group(group_name, fields, group_title)

    def create_form(self, parent: Optional[QWidget] = None) -> QWidget:
        """Create PySide6 UI with form layout and group boxes."""
        main_widget = QWidget(parent)
        main_widget.resize(600, 400)
        main_layout = QVBoxLayout(main_widget)

        # Group fields by group name
        groups: Dict[str, list] = {}
        for field_name in self.__pydantic_fields__.keys():
            widget_metadata = self._get_or_create_widget_metadata(field_name)

            group_name = widget_metadata.group
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append((field_name, widget_metadata))

        # Create grouped fields in group boxes
        for group_name in sorted(groups.keys()):
            group_box = self._create_groupbox_for_group(group_name, groups[group_name])
            main_layout.addWidget(group_box)
        main_layout.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)
        return scroll_area

    def _create_groupbox_for_group(
        self, group_name: str, fields: List[Tuple[str, WidgetMetadata]], group_title: Optional[str] = None
    ):
        """Helper to create groupbox from field in same group"""
        group_box = QGroupBox(group_title or group_name.replace("_", " ").title())
        group_layout = QFormLayout(group_box)

        for field_name, widget_info in fields:
            widget = self._create_widget_for_field(field_name, widget_info)
            if widget is None:
                continue

            label = widget_info.title or field_name.replace("_", " ").title()
            group_layout.addRow(label, widget)

        group_box.setLayout(group_layout)

        return group_box
