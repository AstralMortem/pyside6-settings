from pydantic.fields import Field as PydanticField
from pydantic_core import PydanticUndefined
from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Literal

_DEFAULT_GROUP = "general"

_WIDGET_TYPES = Literal[
    "hidden",
    "tags",
    "path",
    "checkbox",
    "spinbox",
    "doublespinbox",
    "password",
    "textarea",
]
_FS_MODE = Literal["file", "folder", "save_file"]


class WidgetMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: Optional[str] = PydanticField(default=None)
    description: Optional[str] = PydanticField(default=None)
    group: str = PydanticField(default=_DEFAULT_GROUP)
    widget: Optional[_WIDGET_TYPES] = PydanticField(default=None)
    choices: Optional[list] = PydanticField(default=None)  # Used by QComboBox
    fs_mode: Optional[_FS_MODE] = PydanticField(default=None)  # User by Path


def Field(
    default: Any = PydanticUndefined,
    default_factory: Any = PydanticUndefined,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    group: str = _DEFAULT_GROUP,
    widget: Optional[_WIDGET_TYPES] = None,
    choices: Optional[list] = None,
    fs_mode: Optional[_FS_MODE] = None,
    ge: Optional[float] = None,
    le: Optional[float] = None,
    gt: Optional[float] = None,
    lt: Optional[float] = None,
    exclude: Optional[bool] = None,
    frozen: Optional[bool] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    **extra_params,
):
    widget_metadata = WidgetMetadata(
        title=title,
        description=description,
        group=group,
        widget=widget,
        choices=choices,
        fs_mode=fs_mode,
        **extra_params,
    )

    return PydanticField(
        default=default,
        default_factory=default_factory,
        title=title,
        description=description,
        le=le,
        lt=lt,
        ge=ge,
        gt=gt,
        exclude=exclude,
        frozen=frozen,
        min_length=min_length,
        max_length=max_length,
        json_schema_extra={"widget_metadata": widget_metadata},
    )  # type: ignore
