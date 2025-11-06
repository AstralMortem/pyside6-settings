from .base import BaseConfigLoader
from .json import JSONLoader
from .toml import TOMLLoader
from .yaml import YAMLLoader
from typing import Dict, Type


DEFAULT_LOADERS: Dict[str, Type[BaseConfigLoader]] = {
    ".json": JSONLoader,
    ".toml": TOMLLoader,
    ".yaml": YAMLLoader,
    ".yml": YAMLLoader,
}
