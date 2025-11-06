from typing import Any, Dict
from .base import BaseConfigLoader
import yaml


class YAMLLoader(BaseConfigLoader):
    def load(self) -> Dict[str, Any]:
        with open(self.config_file, "r") as f:
            return self.ungroup_data(yaml.safe_load(f))

    def save(self, data: Dict[str, Any]):
        with open(self.config_file, "w") as f:
            yaml.dump(data, f)
