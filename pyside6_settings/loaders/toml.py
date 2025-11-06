from typing import Any, Dict
from .base import BaseConfigLoader
import toml


class TOMLLoader(BaseConfigLoader):
    def load(self) -> Dict[str, Any]:
        return self.ungroup_data(toml.load(self.config_file))

    def save(self, data: Dict[str, Any]):
        with open(self.config_file, "w") as f:
            toml.dump(data, f)
