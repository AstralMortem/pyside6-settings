from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseConfigLoader:
    def __init__(self, config_file: Path):
        self.config_file = config_file

    @abstractmethod
    def load(self) -> Dict[str, Any]: ...

    @abstractmethod
    def save(self, data: Dict[str, Any]): ...

    def ungroup_data(self, data: Dict[str, Any]):
        ungrouped = {}
        for key, val in data.items():
            if isinstance(val, dict):
                ungrouped.update(val)
            else:
                ungrouped[key] = val
        return ungrouped
