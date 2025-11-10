from typing import Any, Dict
from .base import BaseConfigLoader
import toml


class TOMLLoader(BaseConfigLoader):
    def load(self) -> Dict[str, Any]:
        with open(self.config_file, "r", encoding="utf-8") as f:
            return self.ungroup_data(toml.load(f))

    def save(self, data: Dict[str, Any]):
        with open(self.config_file, "w", encoding="utf-8") as f:
            toml.dump(data, f)
