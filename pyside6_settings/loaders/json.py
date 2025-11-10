import json
from typing import Any, Dict
from .base import BaseConfigLoader


class JSONLoader(BaseConfigLoader):
    def load(self) -> Dict[str, Any]:
        with open(self.config_file, "r", encoding="utf-8") as f:
            return self.ungroup_data(json.load(f))

    def save(self, data: Dict[str, Any]):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
